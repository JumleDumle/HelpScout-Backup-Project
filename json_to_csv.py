"""
Help Scout JSON to Master CSV Converter
Author: Julius Vendorf, FysioCamp
Description: Parses paginated Help Scout conversation JSON files, extracts 
metadata and thread history, strips HTML, and outputs a flat, Monday.com-ready CSV.
"""

import os
import json
import csv
import re
import glob

# --- Configuration ---
# Point this to the folder where your previous script saved the JSON files
JSON_FOLDER_PATH = './'  
OUTPUT_CSV_NAME = 'helpscout_master_archive.csv'

def strip_html_tags(text):
    """Removes HTML tags from Help Scout thread bodies for clean CRM/Monday.com reading."""
    if not text:
        return ""
    # Replace common HTML breaks with actual newlines before stripping tags
    text = text.replace('<br>', '\n').replace('<br/>', '\n').replace('</p>', '\n\n')
    
    # Strip remaining HTML tags
    clean_text = re.sub(r'<.*?>', '', text)
    
    # Clean up leftover HTML entities and excess whitespace
    clean_text = clean_text.replace('&nbsp;', ' ').replace('&amp;', '&')
    return clean_text.strip()

def process_json_to_csv():
    # Find all JSON files in the directory and subdirectories
    search_pattern = os.path.join(JSON_FOLDER_PATH, '**', '*.json')
    json_files = glob.glob(search_pattern, recursive=True)
    
    if not json_files:
        print(f"No .json files found in {JSON_FOLDER_PATH}. Please check the path.")
        return

    print(f"Found {len(json_files)} JSON files. Starting conversion...")

    # Define the columns for the Master CSV
    headers = [
        'Ticket ID', 
        'Created Date', 
        'Status', 
        'Subject', 
        'Customer Name', 
        'Customer Email', 
        'Assignee', 
        'Full Conversation History'
    ]

    # Use utf-8-sig to ensure Danish characters (æ, ø, å) render correctly in Excel/Monday.com
    with open(OUTPUT_CSV_NAME, 'w', newline='', encoding='utf-8-sig') as csv_file:
        writer = csv.writer(csv_file)
        writer.writerow(headers)

        total_tickets_processed = 0

        for file_path in json_files:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    conversations = json.load(f)
                    
                    # Ensure we are iterating over a list of conversations
                    if not isinstance(conversations, list):
                        print(f"Skipping {file_path}: Data is not a list of conversations.")
                        continue

                    for conv in conversations:
                        # 1. Safely extract metadata using .get() to prevent KeyErrors
                        ticket_id = conv.get('number', 'N/A')
                        created_date = conv.get('createdAt', 'N/A')
                        status = conv.get('status', 'N/A')
                        subject = conv.get('subject', 'No Subject')
                        
                        # 2. Extract Customer details (can be missing on internal tickets)
                        customer_data = conv.get('primaryCustomer', {})
                        first_name = customer_data.get('first', '')
                        last_name = customer_data.get('last', '')
                        customer_name = f"{first_name} {last_name}".strip()
                        customer_email = customer_data.get('email', 'N/A')

                        # 3. Extract Assignee
                        assignee_data = conv.get('assignee', {})
                        assignee_name = f"{assignee_data.get('first', '')} {assignee_data.get('last', '')}".strip() if assignee_data else 'Unassigned'

                        # 4. Compile the full conversation history from threads
                        compiled_history = []
                        threads = conv.get('_embedded', {}).get('threads', [])
                        
                        # Reverse threads so they read chronologically (oldest to newest)
                        for thread in reversed(threads):
                            thread_date = thread.get('createdAt', '')
                            author = thread.get('createdBy', {}).get('email', 'Unknown User')
                            raw_body = thread.get('body', '')
                            clean_body = strip_html_tags(raw_body)
                            
                            # Format each message block
                            message_block = f"--- {thread_date} | {author} ---\n{clean_body}\n"
                            compiled_history.append(message_block)

                        full_conversation_string = "\n".join(compiled_history)

                        # Write the compiled row to the CSV
                        writer.writerow([
                            ticket_id, 
                            created_date, 
                            status, 
                            subject, 
                            customer_name, 
                            customer_email, 
                            assignee_name, 
                            full_conversation_string
                        ])
                        
                        total_tickets_processed += 1

            except Exception as e:
                print(f"Error processing file {file_path}: {e}")

    print(f"\nSuccess! Compiled {total_tickets_processed} tickets into {OUTPUT_CSV_NAME}.")
    print("This file is now ready to be securely stored or imported as a new board.")

if __name__ == "__main__":
    process_json_to_csv()