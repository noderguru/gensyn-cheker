#!/usr/bin/env python3
import os, re, time, random, requests, signal
from typing import List, Tuple, Optional, Dict
from collections import deque
from dotenv import load_dotenv

load_dotenv()

# === .env ===
BOT_TOKEN = os.getenv("BOT_TOKEN", "")
CHAT_ID = os.getenv("CHAT_ID", "")
NOTIFY_TARGET = os.getenv("NOTIFY_TARGET", "console")  # console | both
ACCOUNT_FILE = os.getenv("ACCOUNT_FILE", "account_EOA.txt")
PROXY_FILE   = os.getenv("PROXY_FILE", "proxy.txt")

REQUEST_DELAY_MIN = float(os.getenv("REQUEST_DELAY_MIN", "0"))
REQUEST_DELAY_MAX = float(os.getenv("REQUEST_DELAY_MAX", "0"))
NOTIFY_DELAY_SEC  = float(os.getenv("NOTIFY_DELAY_SEC", "0.5"))
API_URL_TEMPLATE  = os.getenv("API_URL_TEMPLATE", "https://dashboard.gensyn.ai/api/v1/users/{address}/blockassist/stats")
REQUEST_TIMEOUT   = int(os.getenv("REQUEST_TIMEOUT", "15"))
RETRY_PER_PROXY   = int(os.getenv("RETRY_PER_PROXY", "1"))
RETRY_ACCOUNT_MAX = int(os.getenv("RETRY_ACCOUNT_MAX", "5"))

POLL_INTERVAL_SEC = float(os.getenv("POLL_INTERVAL_SEC", "60"))

IP_LOOKUP_URL     = os.getenv("IP_LOOKUP_URL", "https://api.ipify.org")

ADDR_RE = re.compile(r"(?i)\b0x[a-f0-9]{40}\b")

BOLD  = "\033[1m"
RESET = "\033[0m"

PROXY_IP_CACHE: Dict[str, Optional[str]] = {}

def number_to_emoji(i: int) -> str:
    if 1 <= i <= 9:
        return f"{i}\N{COMBINING ENCLOSING KEYCAP}"
    if i == 10:
        return "🔟"
    return "🔢"  # 11+

def read_accounts(path: str) -> List[Tuple[str, Optional[str]]]:
    if not os.path.isfile(path):
        raise FileNotFoundError(f"Файл {path} не найден")
    out: List[Tuple[str, Optional[str]]] = []
    with open(path, "r", encoding="utf-8", errors="ignore") as f:
        for raw in f:
            line = raw.strip()
            if not line:
                continue
            parts = line.split()
            if len(parts) == 2 and ADDR_RE.fullmatch(parts[1]):
                label, addr = parts
                out.append((addr, label))
                continue
            addrs = ADDR_RE.findall(line)
            comment = None
            if "-" in line or "—" in line:
                tmp = re.split(r"[-—]", line, maxsplit=1)
                if len(tmp) == 2:
                    comment = tmp[1].strip()
            for addr in addrs:
                out.append((addr, comment))
    return out

def read_proxies(path: str) -> List[str]:
    if not os.path.isfile(path):
        raise FileNotFoundError(f"Файл {path} не найден")
    with open(path, "r", encoding="utf-8", errors="ignore") as f:
        raw = f.read().split()
    proxies = [p for p in raw if p.startswith("http://") or p.startswith("https://")]
    if not proxies:
        raise ValueError("В proxy.txt нет валидных http(s)://user:pass@ip:port")
    return proxies

def proxy_cycle(proxies: List[str]) -> deque:
    arr = proxies[:]
    random.shuffle(arr)
    return deque(arr)

def get_proxy(pool: deque, used: set, all_proxies: List[str]) -> str:
    for _ in range(len(pool)):
        p = pool[0]; pool.rotate(-1)
        if p not in used:
            used.add(p); return p
    if not pool:
        pool.extend(all_proxies)
    p = pool[0]; pool.rotate(-1)
    return p

def http_get(url: str, proxy: Optional[str]) -> Optional[requests.Response]:
    try:
        return requests.get(
            url,
            headers={"Accept":"application/json","User-Agent":"StatsFetcher/1.0"},
            proxies=({"http": proxy, "https": proxy} if proxy else None),
            timeout=REQUEST_TIMEOUT
        )
    except requests.RequestException:
        return None

def fetch_stats(address: str, proxy_order: List[str]) -> Optional[dict]:
    attempts = 0
    for proxy in proxy_order:
        tries = 0
        while tries <= RETRY_PER_PROXY:
            attempts += 1; tries += 1
            if attempts > RETRY_ACCOUNT_MAX:
                return None
            r = http_get(API_URL_TEMPLATE.format(address=address), proxy)
            if r is not None and r.status_code == 200:
                try:
                    return r.json()
                except Exception:
                    pass
    return None

def get_proxy_public_ip(proxy: str) -> Optional[str]:
    if proxy in PROXY_IP_CACHE:
        return PROXY_IP_CACHE[proxy]
    try:
        r = requests.get(
            IP_LOOKUP_URL,
            proxies={"http": proxy, "https": proxy},
            headers={"User-Agent":"StatsFetcher/1.0"},
            timeout=min(REQUEST_TIMEOUT, 8)
        )
        if r.status_code == 200:
            ip = r.text.strip()
            if re.fullmatch(r"\d{1,3}(\.\d{1,3}){3}", ip):
                PROXY_IP_CACHE[proxy] = ip
                return ip
    except requests.RequestException:
        pass
    PROXY_IP_CACHE[proxy] = None
    return None

def send_tg(text: str) -> bool:
    if not BOT_TOKEN or not CHAT_ID:
        return False
    try:
        r = requests.post(
            f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",
            json={
                "chat_id": str(CHAT_ID),
                "text": text,
                "parse_mode": "HTML",
                "disable_web_page_preview": True
            },
            timeout=15
        )
        return r.status_code == 200
    except requests.RequestException:
        return False

def send_tg_chunks(lines: List[str], header: str = "") -> None:
    text = ("\n".join(([header] if header else []) + lines))
    if len(text) <= 3500:
        send_tg(text)
        return
    chunk, size, limit = [], 0, 3500
    if header:
        chunk.append(header); size += len(header) + 1
    for line in lines:
        if size + len(line) + 1 > limit:
            send_tg("\n".join(chunk)); time.sleep(NOTIFY_DELAY_SEC)
            chunk, size = [], 0
        chunk.append(line); size += len(line) + 1
    if chunk:
        send_tg("\n".join(chunk))

def one_pass() -> List[str]:
    accounts = read_accounts(ACCOUNT_FILE)
    proxies  = read_proxies(PROXY_FILE)
    if not accounts:
        print("[ERR] В account_EOA.txt нет адресов"); return []
    if not proxies:
        print("[ERR] В proxy.txt нет прокси"); return []
    if len(proxies) < len(accounts):
        print(f"[WARN] Аккаунтов {len(accounts)} > прокси {len(proxies)} — уникальность 1:1 недостижима.")

    pool = proxy_cycle(proxies)
    used = set()

    total = len(accounts)
    print(f"[INFO] Всего аккаунтов: {total}")
    result_lines = []

    for i, (addr, note) in enumerate(accounts, 1):

        if REQUEST_DELAY_MAX > 0 or REQUEST_DELAY_MIN > 0:
            time.sleep(random.uniform(REQUEST_DELAY_MIN, REQUEST_DELAY_MAX))

        p = get_proxy(pool, used, proxies)
        alt = [x for x in proxies if x != p]; random.shuffle(alt)

        ip = get_proxy_public_ip(p)
        ip_sfx = f" | via {ip}" if ip else " | via n/a"

        data = fetch_stats(addr, [p] + alt)

        last10 = addr[-10:]
        emoji  = number_to_emoji(i)

        if not data:
            line_console = f"{emoji} {last10} | {BOLD}ERROR{RESET}{ip_sfx}"
            print(line_console)
            print(f"Progress: {i}/{total}", flush=True)
            line_html = f"{emoji} <code>{last10}</code> | <b>ERROR</b>"
        else:
            part = data.get("participation")
            line_console = f"{emoji} {last10} | part-{BOLD}{part}{RESET}{ip_sfx}"
            if note:
                line_console += f" | {note}"
            print(line_console)
            print(f"Progress: {i}/{total}", flush=True)

            line_html = f"{emoji} <code>{last10}</code> | part-<b>{part}</b>"
            if note:
                line_html += f" | {note}"

        result_lines.append(line_html)

    print("[DONE] Проход завершён.")
    return result_lines

def main():
    def handle_sigint(sig, frame):
        print("\n[EXIT] Остановлено пользователем (Ctrl+C).")
        raise SystemExit(0)
    signal.signal(signal.SIGINT, handle_sigint)

    next_tick = time.monotonic()  # стартовая точка
    while True:
        start = time.monotonic()
        lines = one_pass()

        if lines and NOTIFY_TARGET == "both":
            send_tg_chunks(lines, header="📊 BlockAssist stats")

        next_tick += POLL_INTERVAL_SEC
        sleep_s = max(0.0, next_tick - time.monotonic())
        if sleep_s > 0:
            print(f"[SLEEP] До следующего опроса: {sleep_s:.1f}s")
            time.sleep(sleep_s)
        else:
            next_tick = time.monotonic()

if __name__ == "__main__":
    main()
