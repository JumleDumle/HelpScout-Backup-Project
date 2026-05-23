```markdown
# Help Scout Conversation Backup Tool

A robust Python utility designed to automatically extract and back up all historical conversation threads across an entire Help Scout account. 

While Help Scout offers a native data export feature, it is limited to high-level metadata and explicitly excludes the actual back-and-forth message content. This script utilizes the Help Scout Inbox API (v2) to bypass that limitation, extracting full conversation histories and saving them into structured JSON files separated by mailbox.

## Features

* **Full Thread Extraction:** Uses the `embed=threads` parameter to capture complete message contents, not just metadata.
* **Dynamic Mailbox Discovery:** Automatically fetches all mailboxes associated with the account and iterates through them—no manual ID hunting required.
* **Smart Pagination:** Handles massive datasets by looping through pages and capturing all active, closed, and archived tickets.
* **Automated Rate Limiting:** Actively monitors the `X-RateLimit-Remaining-Minute` header and pauses execution gracefully to prevent 429 (Too Many Requests) errors.
* **Token Management:** Automatically handles OAuth2 Client Credentials flow and requests new Bearer tokens if the extraction exceeds the token's 48-hour lifespan.

## Prerequisites

* Python 3.x
* `requests` library
* `python-dotenv` library (for secure credential management)

You can install the required dependencies using:
```bash
pip install requests python-dotenv

```

## 1. Help Scout App Setup (OAuth2)

To access the API, you must first generate credentials within your Help Scout account using the Client Credentials flow.

1. Log into Help Scout.
2. Click your profile icon in the top right corner and select **Your Profile**.
3. In the left-hand sidebar menu, click on **My Apps**.
4. Click the **Create My App** button.
5. Fill out the configuration form:
* **App Name:** Give it a recognizable name (e.g., "Automated Backup Script").
* **Redirection URL:** Because this is an internal backend script and does not require web browser authentication, you can safely enter a placeholder URL (e.g., `https://www.google.com`).


6. Click **Create**. Help Scout will immediately generate your **App ID** and **App Secret**. Keep this page open for the next step.

## 2. Configuration (.env)

To keep your credentials secure and avoid hardcoding them into the script, this project uses a `.env` file.

1. In the root directory of this project, create a new file named exactly `.env`.
2. Add your newly generated Help Scout credentials to the file in the following format:

```env
HELP_SCOUT_APP_ID=paste_your_app_id_here
HELP_SCOUT_APP_SECRET=paste_your_app_secret_here

```

*(Note: Ensure that your `.gitignore` file includes `.env` so you do not accidentally commit your credentials to GitHub.)*

## 3. Usage

Run the script from your terminal:

```bash
python main.py

```

**What the script does when executed:**

1. Authenticates with Help Scout and retrieves a Bearer token.
2. Fetches a list of every mailbox in your account.
3. Loops through each mailbox, extracting all pages of conversations.
4. Saves a separate JSON file for each mailbox in the root directory (e.g., `support_helpscout_backup.json`, `sales_helpscout_backup.json`).

## Data Handling & CRM Mapping

The script outputs raw JSON payloads. Because the data is kept in a standardized format and segmented by mailbox, it is highly optimized for internal migrations.

The resulting JSON files can be parsed and mapped directly into workspace boards (like Monday.com) or imported as historical data into native CRM environments. By using this script to handle the raw extraction, you can build clean, direct data loops into your proprietary systems without relying on or paying for external third-party middleware applications.
