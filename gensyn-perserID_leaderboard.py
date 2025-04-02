import requests
import math
import threading
import sys
import time

# ==== НАСТРОЙКИ/SETTINGS ====
ID_FILENAME = "id.txt"
API_URL = 'https://dashboard.gensyn.ai/api/leaderboard-cumulative'
SEND_TELEGRAM = True
SEND_INTERVAL_SECONDS = 3000

TELEGRAM_BOT_TOKEN = ""
TELEGRAM_CHAT_ID = ""
# ===========================

def send_telegram_message(text):
    if not SEND_TELEGRAM:
        return
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
        payload = {
            "chat_id": TELEGRAM_CHAT_ID,
            "text": text,
            "parse_mode": "Markdown"
        }
        response = requests.post(url, data=payload)
        if response.status_code != 200:
            print("Telegram send error:", response.text)
    except Exception as e:
        print("Telegram exception:", e)

def load_ids(filename):
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            lines = [line.strip() for line in f if line.strip()]
        ids = []
        nicknames = []
        for line in lines:
            if line.startswith("Qm") or line.startswith("F-"):
                ids.append(line[2:] if line.startswith("F-") else line)
            else:
                nicknames.append(line)
        return ids, nicknames
    except FileNotFoundError:
        print("File id.txt not found.")
        return [], []

def truncate_float(value, decimals=4):
    factor = 10 ** decimals
    return math.trunc(value * factor) / factor

def spinner(stop_event):
    spinner_chars = "|/-\\"
    i = 0
    while not stop_event.is_set():
        sys.stdout.write("\rLoading " + spinner_chars[i % len(spinner_chars)])
        sys.stdout.flush()
        i += 1
        time.sleep(0.1)
    sys.stdout.write("\rLoading complete!        \n")

def collect_and_send():
    id_list, nickname_list = load_ids(ID_FILENAME)
    if not id_list and not nickname_list:
        print("No valid IDs or nicknames found in file.")
        return

    spinner_stop = threading.Event()
    spinner_thread = threading.Thread(target=spinner, args=(spinner_stop,))
    spinner_thread.start()

    try:
        response = requests.get(API_URL)
        response.raise_for_status()
    except requests.RequestException as e:
        spinner_stop.set()
        spinner_thread.join()
        print("Request error:", e)
        return

    spinner_stop.set()
    spinner_thread.join()

    try:
        data = response.json()
    except ValueError as e:
        print("JSON parse error:", e)
        return

    leaders = data.get("leaders", [])
    if not isinstance(leaders, list):
        print("Unexpected data structure: expected a list.")
        return

    result_dict = {}

    for item in leaders:
        if not isinstance(item, dict):
            continue
        if item.get("id") in id_list:
            result_dict[item["id"]] = item
        elif item.get("nickname") in nickname_list:
            result_dict[item["nickname"]] = item

    for id_ in id_list:
        if id_ not in result_dict:
            result_dict[id_] = None
    for nick in nickname_list:
        if nick not in result_dict:
            result_dict[nick] = None

    header_format = "{:<50} | {:<30} | {:>6} | {:>6} | {:>20} | {:>20}"
    row_format = header_format
    print(header_format.format("ID", "Nickname", "Round", "Stage", "Cum. Score", "Last Score"))
    print("-" * 140)

    message_lines = ["*Gensyn Leaderboard Update:*\n"]

    for key, item in result_dict.items():
        if item is None:
            is_id = key in id_list
            api_id = key if is_id else "N/A"
            display_nickname = key if not is_id else "N/A"
            round_str = stage_str = cum_score_str = last_score_str = "N/A"
        else:
            api_id = item.get("id", "N/A")
            display_nickname = item.get("nickname") or "N/A"
            round_str = str(item.get("recordedRound", "N/A"))
            stage_str = str(item.get("recordedStage", "N/A"))
            cum_score = item.get("cumulativeScore")
            last_score = item.get("lastScore")
            cum_score_str = f"{truncate_float(cum_score, 4):.4f}" if cum_score is not None else "N/A"
            last_score_str = f"{truncate_float(last_score, 4):.4f}" if last_score is not None else "N/A"

        print(row_format.format(api_id, display_nickname, round_str, stage_str, cum_score_str, last_score_str))
        message_lines.append(
            f"*{display_nickname}* (ID: `{api_id}`)\n"
            f"Round: {round_str}, Stage: {stage_str}\n"
            f"Cumulative: *{cum_score_str}*, Last: {last_score_str}\n"
        )

    send_telegram_message("\n".join(message_lines))

def main():
    while True:
        collect_and_send()
        print(f"\nWait {SEND_INTERVAL_SECONDS} seconds until the next check...\n")
        time.sleep(SEND_INTERVAL_SECONDS)

if __name__ == '__main__':
    main()
