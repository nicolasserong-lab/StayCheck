import json
import os

SETTINGS_FILE = 'settings.json'

def get_settings():
    if os.path.exists(SETTINGS_FILE):
        with open(SETTINGS_FILE, 'r') as f:
            return json.load(f)
    return {
        'google_sheet_id': '',
        'google_credentials_json': '' # Para guardar el contenido del JSON de la cuenta de servicio
    }

def save_settings(settings):
    with open(SETTINGS_FILE, 'w') as f:
        json.dump(settings, f)
