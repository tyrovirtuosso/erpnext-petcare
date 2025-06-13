import logging
from typing import List, Dict
import gspread
from google.oauth2.service_account import Credentials

# Import Google Sheet config from the same folder
from .google_sheet_config import SPREADSHEET_URL, DEFAULT_SHEET_NAME, SERVICE_ACCOUNT_JSON

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def fetch_all_transactions() -> List[Dict[str, str]]:
    """
    Fetch all transactions from the configured Google Sheet and sheet name.
    Returns:
        List of transactions as dictionaries (header row as keys).
    Raises:
        Exception if unable to fetch transactions.
    """
    try:
        # Define the required scopes
        scopes = [
            "https://www.googleapis.com/auth/spreadsheets",
            "https://www.googleapis.com/auth/drive"
        ]
        credentials = Credentials.from_service_account_file(
            SERVICE_ACCOUNT_JSON, scopes=scopes
        )
        gc = gspread.authorize(credentials)
        logger.info(f"Opening spreadsheet: {SPREADSHEET_URL}")
        sh = gc.open_by_url(SPREADSHEET_URL)
        worksheet = sh.worksheet(DEFAULT_SHEET_NAME)
        logger.info(f"Fetching all records from sheet: {DEFAULT_SHEET_NAME}")
        records = worksheet.get_all_records()
        logger.info(f"Fetched {len(records)} transactions.")
        return records
    except Exception as e:
        logger.error(f"Error fetching transactions: {e}")
        raise 