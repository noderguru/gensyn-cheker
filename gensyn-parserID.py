import requests
import time
from random import uniform
from eth_abi import encode, decode
from eth_utils import keccak

# === НАСТРОЙКИ ===
ALCHEMY_RPC = "https://gensyn-testnet.g.alchemy.com/public"
CONTRACT = "0xFaD7C5e93f28257429569B854151A1B8DCD404c2"
PEER_ID_FILE = "peer_id.txt"
SEND_INTERVAL_SECONDS = 15000

# Пауза между запросами к RPC (в секундах)
REQUEST_DELAY_MIN = 2  # Минимальная пауза
REQUEST_DELAY_MAX = 8  # Максимальная пауза

BOT_TOKEN = "токен бота можно взять здесь @BotFather"
CHAT_ID = "id чата можно взять здесь @myidbot"
DEBUG = False

# === Telegram MarkdownV2 escape ===
def escape_md(text: str) -> str:
    for char in r"_*[]()~`>#+-=|{}.!":
        text = text.replace(char, f"\{char}")
    return text

def send_telegram(message: str):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": message, "parse_mode": "MarkdownV2"}
    try:
        resp = requests.post(url, data=payload)
        if resp.status_code != 200:
            print("❌ Telegram error:", resp.text)
    except Exception as e:
        print("⚠️ Telegram send failed:", e)

def add_request_delay():
    delay = uniform(REQUEST_DELAY_MIN, REQUEST_DELAY_MAX)
    time.sleep(delay)

def eth_call(method_sig: str, encoded_data: str):
    payload = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "eth_call",
        "params": [{"to": CONTRACT, "data": "0x" + method_sig + encoded_data}, "latest"]
    }
    
    add_request_delay()
    
    response = requests.post(ALCHEMY_RPC, json=payload).json()
    if "error" in response:
        raise Exception(response["error"]["message"])
    return response["result"]

def get_total_rewards(peer_id: str):
    try:
        sig = "80c3d97f"  # getTotalRewards(string[])
        encoded = encode(["string[]"], [[peer_id]]).hex()
        raw = eth_call(sig, encoded)
        if DEBUG:
            print(f"[🔍] REWARD peer_id: {peer_id}")
            print(f"[🔍] Encoded: {encoded}")
            print(f"[RAW reward result]: {raw}")
        reward_uint = decode(["uint256[]"], bytes.fromhex(raw[2:]))[0][0]
        return float(reward_uint)
    except Exception as e:
        print(f"[⛔] REWARD failed for {peer_id}: {e}")
        return "⛔"

def get_total_wins(peer_id: str):
    try:
        sig = "099c4002"  # getTotalWins(string)
        encoded = encode(["string"], [peer_id]).hex()
        return int(eth_call(sig, encoded), 16)
    except Exception as e:
        print(f"[⛔] WINS failed for {peer_id}: {e}")
        return "⛔"

def get_voter_vote_count(peer_id: str):
    try:
        sig = "dfb3c7df"  # getVoterVoteCount(string)
        encoded = encode(["string"], [peer_id]).hex()
        return int(eth_call(sig, encoded), 16)
    except Exception as e:
        print(f"[⛔] VOTES failed for {peer_id}: {e}")
        return "⛔"

def get_current_round():
    try:
        sig = keccak(text="currentRound()")[:4].hex()
        return int(eth_call(sig, ""), 16)
    except Exception as e:
        print(f"[⛔] currentRound failed: {e}")
        return "⛔"

def load_peer_ids():
    try:
        with open(PEER_ID_FILE, "r") as f:
            return [line.strip() for line in f if line.strip()]
    except FileNotFoundError:
        print("📄 Файл peer_id.txt не найден.")
        return []

def main_loop():
    while True:
        peer_ids = load_peer_ids()
        if not peer_ids:
            time.sleep(SEND_INTERVAL_SECONDS)
            continue

        print("🚀 Начинаем сбор данных...")
        
        current_round = get_current_round()
        timestamp = escape_md(time.strftime('%Y-%m-%d %H:%M:%S'))
        
        lines = [
            f"*🕵️‍♂️ Gensyn Rewards*\n_{timestamp}_\n",
            f"🔄 *Round:* `{escape_md(str(current_round))}`\n",
            "*📊 Peer Stats \\(Wins / Votes / Reward\\):*"
        ]

        for i, pid in enumerate(peer_ids, 1):
            print(f"📊 Обработка аккаунта {i}/{len(peer_ids)}: {pid[-10:]}...")
            
            short_id = escape_md(pid[-10:])
            wins = get_total_wins(pid)
            votes = get_voter_vote_count(pid)
            reward = get_total_rewards(pid)

            wins_str = escape_md(str(wins)) if wins != "⛔" else "⛔"
            votes_str = escape_md(str(votes)) if votes != "⛔" else "⛔"
            reward_str = escape_md(f"{reward:g}") if isinstance(reward, float) else "⛔"

            lines.append(f"`{short_id}`: {wins_str} / {votes_str} / {reward_str}")

        message = "\n".join(lines)
        
        print("\n" + "="*50)
        print("📈 ИТОГОВЫЕ РЕЗУЛЬТАТЫ:")
        print("="*50)
        print(message)
        print("="*50 + "\n")
        
        print("📤 Отправка сообщения в Telegram...")
        send_telegram(message)
        
        print(f"⏰ Ожидание {SEND_INTERVAL_SECONDS} секунд до следующего цикла...")
        time.sleep(SEND_INTERVAL_SECONDS)

if __name__ == "__main__":
    print(f"🎯 Запуск мониторинга Gensyn {REQUEST_DELAY_MIN}-{REQUEST_DELAY_MAX}с между запросами")
    main_loop()
