from globals import CONFIG_FILE
import json

def load_config():
    try:
        with open(CONFIG_FILE, "r") as f:
            return json.load(f)
    except FileNotFoundError:
        return {
            "resumeModel": "gpt-3.5-turbo",
            "condensaModel": "gpt-3.5-turbo",
            "resumeChunkSize": 5000,
            "ragModel": "gpt-3.5-turbo",
            "ragSearchType": "similarity",
            "ragSearchK": 3,
            "ragChunkSize": 400
        }
