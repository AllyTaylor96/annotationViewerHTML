import json


def load_json(json_path: str):
    with open(json_path, 'r') as f:
        json_data = json.load(f)
    return json_data


def write_json(output_data: dict, output_path: str):
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(output_data, f, ensure_ascii=False, indent=4)
