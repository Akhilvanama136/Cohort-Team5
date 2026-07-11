import os
import json
import logging
import csv
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

# Logger setup
logger = logging.getLogger("SheetsLogger")

# Fallback local CSV log
FALLBACK_CSV = "sheets_log_fallback.csv"

def log_to_fallback_csv(timestamp, username, question, category, response_time, sources_summary):
    """Logs data to a local CSV file if Google Sheets is not configured."""
    file_exists = os.path.exists(FALLBACK_CSV)
    try:
        with open(FALLBACK_CSV, "a", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            if not file_exists:
                # Write header
                writer.writerow(["Timestamp (UTC)", "Username", "Question", "Disease Category", "Response Time (s)", "Sources Used"])
            writer.writerow([timestamp, username, question, category, response_time, sources_summary])
        logger.info(f"Successfully logged query locally to CSV fallback: {question[:30]}...")
    except Exception as e:
        logger.error(f"Failed to log locally to CSV: {e}")

def log_query_to_sheets(username: str, question: str, category: str, response_time: float, sources: list):
    """
    Logs medical query details to a Google Spreadsheet.
    Falls back to a local CSV if credentials.json is not found.
    """
    timestamp = datetime.utcnow().isoformat()
    
    # Format sources into a concise summary string
    sources_summary = "; ".join([f"{s['source']} (Pg {s['page']})" for s in sources]) if sources else "None"
    
    creds_path = os.getenv("GOOGLE_APPLICATION_CREDENTIALS", "credentials.json")
    sheet_name = os.getenv("GOOGLE_SHEET_NAME", "Medical RAG Audit Logs")
    sheet_url = os.getenv("GOOGLE_SHEET_URL")

    # If no credentials file exists, log to fallback CSV
    if not os.path.exists(creds_path):
        logger.warning(f"Google credentials file '{creds_path}' not found. Falling back to local CSV log...")
        log_to_fallback_csv(timestamp, username, question, category, response_time, sources_summary)
        return False

    try:
        import gspread
        from google.oauth2.service_account import Credentials
        
        # Define scopes
        scopes = [
            "https://www.googleapis.com/auth/spreadsheets",
            "https://www.googleapis.com/auth/drive"
        ]
        
        creds = Credentials.from_service_account_file(creds_path, scopes=scopes)
        client = gspread.authorize(creds)
        
        # Open the spreadsheet
        try:
            if sheet_url:
                sheet = client.open_by_url(sheet_url)
            else:
                sheet = client.open(sheet_name)
        except gspread.exceptions.SpreadsheetNotFound:
            if sheet_url:
                raise ValueError(f"Spreadsheet at URL '{sheet_url}' was not found or access was denied. Make sure you shared the sheet with your service account email.")
            # Create a new spreadsheet if not found by name
            logger.info(f"Spreadsheet '{sheet_name}' not found. Creating a new one...")
            sheet = client.create(sheet_name)
            # Share sheet with developer email if configured
            share_email = os.getenv("GOOGLE_SHARE_EMAIL")
            if share_email:
                sheet.share(share_email, perm_type='user', role='writer')
        
        # Get first worksheet
        worksheet = sheet.get_worksheet(0)
        if worksheet is None:
            worksheet = sheet.add_worksheet(title="Logs", rows="1000", cols="6")
            
        # Check if sheet is empty and needs headers
        existing_records = worksheet.get_all_values()
        if len(existing_records) == 0:
            worksheet.append_row([
                "Timestamp (UTC)", 
                "Username", 
                "Question", 
                "Disease Category", 
                "Response Time (s)", 
                "Sources Used"
            ])
            
        # Append log data row
        row = [
            timestamp, 
            username, 
            question, 
            category, 
            round(response_time, 4), 
            sources_summary
        ]
        worksheet.append_row(row)
        logger.info(f"Successfully logged query to Google Sheets '{sheet_name}' for user {username}.")
        return True

    except Exception as e:
        logger.error(f"Google Sheets logging failed: {e}. Falling back to CSV...")
        log_to_fallback_csv(timestamp, username, question, category, response_time, sources_summary)
        return False

if __name__ == "__main__":
    # Test logging fallback
    log_query_to_sheets("test_user", "What is Type 1 Diabetes?", "diabetes", 1.25, [{"source": "test.pdf", "page": 4}])
