import requests
import time
from eth_abi import encode
from eth_utils import keccak

# === НАСТРОЙКИ ===
ALCHEMY_RPC = "https://gensyn-testnet.g.alchemy.com/v2/iBYs2GoyiHYlFl4o4MvBeM8-UMpDAcjx"
CONTRACT = "0x2fC68a233EF9E9509f034DD551FF90A79a0B8F82"
PEER_ID_FILE = "peer_id.txt"
SEND_INTERVAL_SECONDS = 3600  # интервал отправки (в секундах)

# === TELEGRAM НАСТРОЙКИ ===
BOT_TOKEN = ""
CHAT_ID = ""

def escape_md(text):
    special_chars = r"_*[]()~`>#+-=|{}.!"
    for char in special_chars:
        text = text.replace(char, f"\\{char}")
    return text

def send_telegram(message):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": CHAT_ID,
        "text": message,
        "parse_mode": "MarkdownV2"
    }
    try:
        response = requests.post(url, data=payload)
        if response.status_code != 200:
            print("❌ Telegram error:", response.text)
    except Exception as e:
        print("⚠️ Ошибка отправки в Telegram:", e)

def get_total_wins(peer_id: str):
    method_sig = keccak(text="getTotalWins(string)")[:4].hex()
    encoded_param = encode(["string"], [peer_id]).hex()
    data = "0x" + method_sig + encoded_param

    payload = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "eth_call",
        "params": [{"to": CONTRACT, "data": data}, "latest"]
    }

    try:
        response = requests.post(ALCHEMY_RPC, json=payload)
        result = response.json()

        if "error" in result:
            return f"❌ `{escape_md(peer_id[-10:])}`: {escape_md(result['error']['message'])}"
        
        hex_value = result["result"]
        total_wins = int(hex_value, 16)
        return f"🏆 `{escape_md(peer_id[-10:])}`: *{total_wins}* wins"
    except Exception as e:
        return f"⚠️ `{escape_md(peer_id[-10:])}`: {escape_md(str(e))}"

def load_peer_ids():
    try:
        with open(PEER_ID_FILE, "r") as f:
            return [line.strip() for line in f if line.strip()]
    except FileNotFoundError:
        print(f"📄 Файл {PEER_ID_FILE} не найден.")
        return []

def main_loop():
    while True:
        peer_ids = load_peer_ids()
        if not peer_ids:
            time.sleep(SEND_INTERVAL_SECONDS)
            continue

        timestamp = time.strftime('%Y-%m-%d %H:%M:%S')
        report_lines = [f"*🕵️‍♂️ Gensyn Total Wins Report*\n_{escape_md(timestamp)}_\n"]
        
        for pid in peer_ids:
            result = get_total_wins(pid)
            report_lines.append(result)

        final_report = "\n".join(report_lines)
        print(final_report)
        send_telegram(final_report)

        time.sleep(SEND_INTERVAL_SECONDS)

if __name__ == "__main__":
    main_loop()
