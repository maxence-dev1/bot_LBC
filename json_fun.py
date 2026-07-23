import json

FILE_NAME = "scraped_annonce.json"


def read_json():
    try:
        with open(FILE_NAME, "r", encoding="utf-8") as f:
            data = json.load(f)
            return data
    except (FileNotFoundError, json.JSONDecodeError):
            data = []
            return data


def save_json(list):
     with open(FILE_NAME, "w", encoding="utf-8") as f:
        json.dump(list, f, indent=4, ensure_ascii=False)
