import requests
import time
from eth_abi import encode, decode
from eth_utils import keccak, to_checksum_address

# === НАСТРОЙКИ ===
ALCHEMY_RPC = "https://gensyn-testnet.g.alchemy.com/v2/iBYs2GoyiHYlFl4o4MvBeM8-UMpDAcjx"
CONTRACT = "0x2fC68a233EF9E9509f034DD551FF90A79a0B8F82"
PEER_ID_FILE = "peer_id.txt"
SEND_INTERVAL_SECONDS = 3600  # интервал отправки (в секундах)

BOT_TOKEN = ""
CHAT_ID = ""

def escape_md(text):
    special_chars = r"_*[]()~`>#+-=|{}.!"
    for char in special_chars:
        text = text.replace(char, f"\\{char}")
    return text

def send_telegram(message):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": message, "parse_mode": "MarkdownV2"}
    try:
        response = requests.post(url, data=payload)
        if response.status_code != 200:
            print("❌ Telegram error:", response.text)
    except Exception as e:
        print("⚠️ Ошибка отправки в Telegram:", e)

def eth_call(method_sig: str, encoded_data: str):
    payload = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "eth_call",
        "params": [{"to": CONTRACT, "data": "0x" + method_sig + encoded_data}, "latest"]
    }
    response = requests.post(ALCHEMY_RPC, json=payload).json()
    if "error" in response:
        raise Exception(response["error"]["message"])
    return response["result"]

def get_current_round(max_retries=3, delay=10):
    sig = keccak(text="currentRound()")[:4].hex()
    for attempt in range(1, max_retries + 1):
        try:
            result = eth_call(sig, "")
            return int(result, 16)
        except Exception as e:
            print(f"❌ Попытка {attempt}: ошибка получения currentRound:", e)
            if attempt < max_retries:
                time.sleep(delay)
    return None

def get_total_wins(peer_id: str):
    try:
        sig = keccak(text="getTotalWins(string)")[:4].hex()
        encoded = encode(["string"], [peer_id]).hex()
        result = eth_call(sig, encoded)
        return int(result, 16)
    except:
        return "-"

def get_peer_vote_count(round_num: int, peer_id: str):
    try:
        sig = keccak(text="getPeerVoteCount(uint256,string)")[:4].hex()
        encoded = encode(["uint256", "string"], [round_num, peer_id]).hex()
        result = eth_call(sig, encoded)
        return int(result, 16)
    except:
        return "-"

def get_voter_vote_count(eoa: str):
    try:
        sig = keccak(text="getVoterVoteCount(address)")[:4].hex()
        encoded = encode(["address"], [eoa]).hex()
        result = eth_call(sig, encoded)
        return int(result, 16)
    except:
        return "-"

def get_eoas_from_peer_ids(peer_ids: list[str]) -> list[str]:
    try:
        sig = keccak(text="getEoa(string[])")[:4].hex()
        encoded = encode(["string[]"], [peer_ids]).hex()
        result = eth_call(sig, encoded)
        decoded = decode(["address[]"], bytes.fromhex(result[2:]))[0]
        return [to_checksum_address(addr) for addr in decoded]
    except Exception as e:
        print("❌ Ошибка getEoa:", e)
        return []

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

        current_round = get_current_round()
        if current_round is None:
            time.sleep(10)
            continue

        eoas = get_eoas_from_peer_ids(peer_ids)
        if not eoas or len(eoas) != len(peer_ids):
            time.sleep(10)
            continue

        timestamp = escape_md(time.strftime('%Y-%m-%d %H:%M:%S'))
        report_lines = [
            f"*🕵️‍♂️ Gensyn Report*\n_{timestamp}_\n",
            f"🔄 *Round:* `{current_round}`\n",
            "*📊 Peer Stats:*"
        ]

        for pid, eoa in zip(peer_ids, eoas):
            short_id = escape_md(pid[-10:])
            wins = get_total_wins(pid)
            total_votes = get_voter_vote_count(eoa)
            report_lines.append(f"`{short_id}`: {wins} wins / {total_votes} total votes")

        final_report = "\n".join(report_lines)
        print(final_report)
        send_telegram(final_report)
        time.sleep(SEND_INTERVAL_SECONDS)

if __name__ == "__main__":
    main_loop()
