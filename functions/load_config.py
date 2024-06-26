from globals import CONFIG_FILE
import json

def load_config():
    try:
        with open(CONFIG_FILE, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        return {"resumeModel": "gpt-rubo", "condensaModel": "claude"}