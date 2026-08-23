import json

FILE_NAME = "scraped_annonce.json"


def read_json(file):
    try:
        with open(file, "r", encoding="utf-8") as f:
            data = json.load(f)
            return data
    except (FileNotFoundError, json.JSONDecodeError):
        data = []
        return data


def save_json(list, file):
    with open(file, "w", encoding="utf-8") as f:
        json.dump(list, f, indent=4, ensure_ascii=False)


def add_comp_to_json(file, comp, classe):
    f = read_json(file)
    f[classe].append(comp)
    save_json(f, file)


add_comp_to_json("prix_composants.json", "test test", "cpu")
