import os
from dotenv import load_dotenv

# Go up one dir and load .env file
load_dotenv('../helpscout-api_to_json.env')

APP_ID = os.getenv('HELP_SCOUT_APP_ID')
APP_SECRET = os.getenv('HELP_SCOUT_APP_SECRET')

# --- TEMPORARY DEBUGGING ---
print(f"Loaded APP_ID: {APP_ID}")
print(f"Loaded APP_SECRET: {APP_SECRET}")
# ---------------------------