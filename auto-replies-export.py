import requests
import json
import time
import os
from dotenv import load_dotenv

load_dotenv('auto-replies-export.env')

APP_ID = os.getenv('HELP_SCOUT_APP_ID')
APP_SECRET = os.getenv('HELP_SCOUT_APP_SECRET')
BASE_URL = 'https://api.helpscout.net/v2'

OUTPUT_FILENAME = "helpscout_saved_replies.json"

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
        print("Response from Help Scout:", response.text) 
        
    response.raise_for_status()
    return response.json()['access_token']

def get_mailboxes(headers):
    url = f"{BASE_URL}/mailboxes"
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    
    data = response.json()
    embedded = data.get("_embedded")
    
    # Apply type checking here as well for stability 
    if isinstance(embedded, dict):
        return embedded.get("mailboxes", [])
    return []

def get_saved_replies_for_mailbox(headers, mailbox_id):
    replies = []
    url = f"{BASE_URL}/mailboxes/{mailbox_id}/saved-replies"
    
    while url:
        response = requests.get(url, headers=headers)
        
        if response.status_code == 429:
            print("Rate limit reached. Sleeping for 5 seconds...")
            time.sleep(5)
            continue
            
        # Ignore 404s gracefully just in case a mailbox isn't configured for saved replies
        if response.status_code == 404:
            print(f"  -> Mailbox ID {mailbox_id} returned 404. Skipping.")
            break
            
        response.raise_for_status()
        data = response.json()
        
        current_replies = []
        
        # 1. Safely extract the list of replies whether it's a list or a dict
        if isinstance(data, list):
            current_replies = data
            url = None  # Direct lists don't have pagination links, so we end the loop
        elif isinstance(data, dict):
            embedded = data.get("_embedded", {})
            if not isinstance(embedded, dict):
                embedded = {}
            
            current_replies = embedded.get("saved-replies") or embedded.get("savedReplies") or []
            
            # Safely extract pagination links
            links = data.get("_links", {})
            if not isinstance(links, dict):
                links = {}
                
            next_link = links.get("next")
            if isinstance(next_link, dict):
                url = next_link.get("href")
            else:
                url = None
        else:
            break
            
        # 2. Fetch the full text for each individual reply
        if isinstance(current_replies, list):
            for basic_reply in current_replies:
                if not isinstance(basic_reply, dict):
                    continue
                    
                reply_id = basic_reply.get("id")
                if reply_id:
                    full_reply_url = f"{BASE_URL}/mailboxes/{mailbox_id}/saved-replies/{reply_id}"
                    full_resp = requests.get(full_reply_url, headers=headers)
                    
                    if full_resp.status_code == 200:
                        replies.append(full_resp.json())
                    elif full_resp.status_code == 429:
                        print("Rate limit reached on individual fetch. Sleeping for 5...")
                        time.sleep(5)
                        # Retry once
                        full_resp = requests.get(full_reply_url, headers=headers)
                        if full_resp.status_code == 200:
                            replies.append(full_resp.json())
                        else:
                            replies.append(basic_reply)
                    else:
                        replies.append(basic_reply)
                else:
                    replies.append(basic_reply)
                    
    return replies

def main():
    try:
        print("Authenticating with Help Scout...")
        token = get_access_token()
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
        
        print("Fetching mailboxes...")
        mailboxes = get_mailboxes(headers)
        print(f"Found {len(mailboxes)} mailbox(es).")
        
        all_saved_replies = []
        
        for mailbox in mailboxes:
            mailbox_id = mailbox["id"]
            mailbox_name = mailbox["name"]
            print(f"Fetching saved replies for mailbox: {mailbox_name} (ID: {mailbox_id})...")
            
            replies = get_saved_replies_for_mailbox(headers, mailbox_id)
            print(f"Retrieved {len(replies)} replies from {mailbox_name}.")
            
            # Append mailbox info to each reply for context
            for reply in replies:
                # Ensure the reply is actually a dictionary before appending data to it
                if isinstance(reply, dict):
                    reply["source_mailbox_name"] = mailbox_name
                
            all_saved_replies.extend([r for r in replies if isinstance(r, dict)])
            
        print(f"Total saved replies retrieved: {len(all_saved_replies)}")
        
        with open(OUTPUT_FILENAME, "w", encoding="utf-8") as f:
            json.dump(all_saved_replies, f, indent=4, ensure_ascii=False)
            
        print(f"Export complete. Data saved to {OUTPUT_FILENAME}")
        
    except requests.exceptions.RequestException as e:
        print(f"An API error occurred: {e}")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")

if __name__ == "__main__":
    main()