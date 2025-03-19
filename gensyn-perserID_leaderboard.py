import requests
import math

def load_ids(filename):
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            ids = []
            for line in f:
                line = line.strip()
                if not line:
                    continue
                if line.startswith("F-"):
                    line = line[2:]
                ids.append(line)
            return ids
    except FileNotFoundError:
        print(f"File {filename} not found.")
        return []

def truncate_float(value, decimals=4):
    factor = 10 ** decimals
    return math.trunc(value * factor) / factor

def main():
    id_list = load_ids('id.txt')
    if not id_list:
        print("No IDs found.")
        return

    url = 'https://swarm.gensyn.ai/api/leaderboard'
    try:
        response = requests.get(url)
        response.raise_for_status()
    except requests.RequestException as e:
        print("Request error:", e)
        return

    try:
        data = response.json()
    except ValueError as e:
        print("JSON parse error:", e)
        return

    leaders = data.get("leaders", [])
    if not isinstance(leaders, list):
        print("Unexpected data structure: expected a list.")
        return

    filtered_data = [item for item in leaders if isinstance(item, dict) and item.get("id") in id_list]
    
    if not filtered_data:
        print("None of the specified IDs found in the data.")
    else:
        header_format = "{:<40} | {:>12}"
        row_format = "{:<40} | {:>12}"
        print(header_format.format("ID", "Score"))
        print("-" * 55)
        for item in filtered_data:
            score = item.get('score', 0)
            truncated_score = truncate_float(score, decimals=4)
            print(row_format.format(item.get('id'), f"{truncated_score:.4f}"))

if __name__ == '__main__':
    main()
