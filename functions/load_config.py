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
            "resumeChunkSize": 10000,
            "ragModel": "gpt-4o-mini",
            "ragSearchType": "mmr",
            "ragSearchK": 2,
            "ragChunkSize": 1000,
            "useWhisper": "no",
        }
