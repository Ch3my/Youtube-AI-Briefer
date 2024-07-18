from globals import CONFIG_FILE
import json

def load_config():
    try:
        with open(CONFIG_FILE, "r") as f:
            return json.load(f)
    except FileNotFoundError:
        return {
            "resumeModel": "gpt-4o-mini",
            "condensaModel": "gpt-4o-mini",
            "resumeChunkSize": 5000,
            "ragModel": "gpt-4o-mini",
            "ragSearchType": "similarity",
            "ragSearchK": 3,
            "ragChunkSize": 400
        }
