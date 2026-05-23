"""
Help Scout API to Local JSON Backup Tool
Author: Julius Vendorf, FysioCamp
Description: Authenticates with the Help Scout API, retrieves all mailboxes, and 
safely downloads conversation histories. Handles pagination, rate-limiting, 
auto-retries, and outputs data page-by-page into memory-safe, organized JSON files.
"""

import requests
import time
import json
import os
from dotenv import load_dotenv
# I saved the .env file in the folder above this one, because I couldn't get .gitignore to work properly
load_dotenv('../api_Script.env')

# --- Configuration ---
# REMEMBER: Use your newly generated credentials!
APP_ID = 'HELP_SCOUT_APP_ID'
APP_SECRET = 'HELP_SCOUT_APP_SECRET'
BASE_URL = 'https://api.helpscout.net/v2'

def get_access_token():
    # 1. Safety check!
    if not APP_ID or not APP_SECRET:
        raise ValueError("CRITICAL ERROR: APP_ID or APP_SECRET is missing. Check your .env file!")

    auth_url = f"{BASE_URL}/oauth2/token"
    payload = {'grant_type': 'client_credentials', 'client_id': APP_ID, 'client_secret': APP_SECRET}
    
    response = requests.post(auth_url, data=payload)
    
    # 2. Better Error Reporting
    if response.status_code == 400:
        print("400 Bad Request! Help Scout rejected the credentials.")
        print("Response from Help Scout:", response.text) # This will print the exact reason!
        
    response.raise_for_status()
    return response.json()['access_token']

def handle_rate_limit(headers):
    remaining = int(headers.get('X-RateLimit-Remaining-Minute', 100))
    if remaining < 5:
        print("Rate limit approaching. Pausing for 60 seconds...")
        time.sleep(60)

def get_all_mailboxes(token):
    """Fetches all mailboxes associated with the Help Scout account."""
    headers = {'Authorization': f'Bearer {token}', 'Content-Type': 'application/json'}
    response = requests.get(f"{BASE_URL}/mailboxes", headers=headers)
    response.raise_for_status()
    return response.json()['_embedded']['mailboxes']

def fetch_conversations_for_mailbox(mailbox_id, mailbox_name, token):
    """Extracts conversations and saves them page-by-page to prevent RAM crashes."""
    headers = {'Authorization': f'Bearer {token}', 'Content-Type': 'application/json'}
    current_page = 1
    total_pages = 1
    
    # Create a clean string for filenames
    safe_name = mailbox_name.replace(" ", "_").lower()
    
    # Optional: Create a folder for the mailbox to keep things organized
    if not os.path.exists(safe_name):
        os.makedirs(safe_name)
    
    print(f"\n--- Starting backup for Mailbox: {mailbox_name} ---")
    
    while current_page <= total_pages:
        print(f"Fetching page {current_page} of {total_pages}...")
        endpoint = f"{BASE_URL}/conversations?status=all&embed=threads&mailbox={mailbox_id}&page={current_page}"
        
        # --- RETRY MECHANISM ---
        max_retries = 5
        retry_delay = 10 # seconds
        success = False
        
        for attempt in range(max_retries):
            response = requests.get(endpoint, headers=headers)
            
            # Handle token expiration
            if response.status_code == 401:
                print("Token expired. Requesting a new one...")
                token = get_access_token()
                headers['Authorization'] = f'Bearer {token}'
                continue
                
            # Handle temporary server errors
            if response.status_code in [500, 502, 503, 504]:
                print(f"Server error {response.status_code}. Retrying in {retry_delay} seconds (Attempt {attempt + 1} of {max_retries})...")
                time.sleep(retry_delay)
                continue
            
            response.raise_for_status()
            success = True
            break
            
        if not success:
            print(f"CRITICAL: Failed to fetch page {current_page} after {max_retries} attempts. Moving to next mailbox.")
            break 
        # ---------------------------
            
        handle_rate_limit(response.headers)
        data = response.json()
        
        if current_page == 1:
            total_pages = data.get('page', {}).get('totalPages', 1)
            total_elements = data.get('page', {}).get('totalElements', 0)
            print(f"Total conversations in {mailbox_name}: {total_elements}")
            
        # --- MEMORY-SAFE SAVE MECHANISM ---
        if '_embedded' in data and 'conversations' in data['_embedded']:
            page_data = data['_embedded']['conversations']
            
            # Save just this specific page to a file immediately
            filename = f'{safe_name}/helpscout_{safe_name}_page_{current_page}.json'
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(page_data, f, ensure_ascii=False, indent=4)
                
        # --------------------------------------
        
        current_page += 1

    print(f"Finished backing up {mailbox_name}. Files saved in the '{safe_name}' folder.")

def main():
    token = get_access_token()
    
    mailboxes = get_all_mailboxes(token)
    print(f"Found {len(mailboxes)} mailboxes to back up.")
    
    for mailbox in mailboxes:
        fetch_conversations_for_mailbox(mailbox['id'], mailbox['name'], token)

if __name__ == "__main__":
    main()