import json
import csv
import re
import html

def clean_html_for_monday(raw_text):
    if not raw_text:
        return ""
    
    # 1. Replace line breaks, list items, and paragraph ends with actual newlines 
    # to preserve the natural spacing of the message.
    text = re.sub(r'<(br|/p|/div|li)[^>]*>', '\n', raw_text, flags=re.IGNORECASE)
    
    # 2. Strip out all remaining HTML tags
    text = re.sub(r'<[^>]+>', '', text)
    
    # 3. Convert HTML entities (like &amp;, &nbsp;, &#39;) back to normal characters
    text = html.unescape(text)
    
    # 4. Clean up excessive whitespace (reduce 3+ blank lines down to standard double spacing)
    text = re.sub(r'\n\s*\n', '\n\n', text).strip()
    
    return text

def convert_helpscout_json_to_csv(json_filepath, csv_filepath):
    # Load the HelpScout JSON export
    with open(json_filepath, 'r', encoding='utf-8') as f:
        data = json.load(f)
        
    replies = data.get('savedReplies', data) if isinstance(data, dict) else data

    # Define the headers for Monday.com
    headers = ['Reply Name', 'Message Body', 'Category']

    with open(csv_filepath, 'w', newline='', encoding='utf-8') as f:
        # Use quoting to ensure newlines inside the CSV cells don't break the CSV structure
        writer = csv.DictWriter(f, fieldnames=headers, quoting=csv.QUOTE_MINIMAL)
        writer.writeheader()

        for reply in replies:
            # Look for the full 'text' first, but fallback to 'preview' if needed
            raw_message = reply.get('text') or reply.get('preview') or ''
            
            # Clean the message body
            clean_message = clean_html_for_monday(raw_message)
            
            writer.writerow({
                'Reply Name': reply.get('name', 'Untitled Reply'),
                'Message Body': clean_message,
                'Category': reply.get('source_mailbox_name', 'Uncategorized')
            })

    print(f"Successfully converted to {csv_filepath}")

# Execute the conversion
convert_helpscout_json_to_csv('helpscout_export.json', 'helpscout_export.csv')