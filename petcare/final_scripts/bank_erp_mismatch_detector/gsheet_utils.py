import gspread
from oauth2client.service_account import ServiceAccountCredentials
from typing import List, Dict, Optional
from datetime import datetime
from .gsheet_config import SPREADSHEET_URL, DEFAULT_SHEET_NAME, SERVICE_ACCOUNT_JSON

def get_gsheet_client(service_account_json: str = SERVICE_ACCOUNT_JSON) -> gspread.client.Client:
    """Authenticate and return a gspread client using the given service account JSON file."""
    scope = [
        "https://spreadsheets.google.com/feeds",
        "https://www.googleapis.com/auth/drive"
    ]
    creds = ServiceAccountCredentials.from_json_keyfile_name(service_account_json, scope)
    return gspread.authorize(creds)

def get_sheet_data(
    sheet_name: str = DEFAULT_SHEET_NAME,
    spreadsheet_url: str = SPREADSHEET_URL,
    service_account_json: str = SERVICE_ACCOUNT_JSON
) -> List[Dict[str, str]]:
    """
    Fetch all data from the specified Google Sheet.
    Returns a list of dicts (one per row), using the headers as keys.
    """
    client = get_gsheet_client(service_account_json)
    spreadsheet = client.open_by_url(spreadsheet_url)
    worksheet = spreadsheet.worksheet(sheet_name)
    all_data = worksheet.get_all_values()
    headers = all_data[0] if all_data else []
    return [dict(zip(headers, row)) for row in all_data[1:]]

def fetch_gsheet_in_batches(
    sheet_name: str = DEFAULT_SHEET_NAME,
    spreadsheet_url: str = SPREADSHEET_URL,
    service_account_json: str = SERVICE_ACCOUNT_JSON,
    batch_size: int = 1000
):
    """
    Yield batches of rows (as dicts) from the Google Sheet.
    """
    client = get_gsheet_client(service_account_json)
    spreadsheet = client.open_by_url(spreadsheet_url)
    worksheet = spreadsheet.worksheet(sheet_name)
    headers = worksheet.row_values(1)
    non_empty_rows = len([v for v in worksheet.col_values(1) if v])
    start = 2  # Data starts from row 2 (after header)
    while start <= non_empty_rows:
        end = min(start + batch_size - 1, non_empty_rows)
        col_count = len(headers)
        col_end = chr(ord('A') + col_count - 1)
        cell_range = f"A{start}:{col_end}{end}"
        batch = worksheet.get(cell_range)
        if not batch or all(not any(row) for row in batch):
            break
        batch_dicts = [dict(zip(headers, row)) for row in batch]
        yield batch_dicts
        start += batch_size

def format_gsheet_date(date_str: str) -> Optional[str]:
    """Convert various date formats to 'YYYY-MM-DD'."""
    date_formats = ["%d/%b/%Y", "%d-%b-%Y", "%d/%m/%Y", "%d-%m-%Y", "%Y-%m-%d"]
    for fmt in date_formats:
        try:
            date_obj = datetime.strptime(date_str, fmt)
            return date_obj.strftime("%Y-%m-%d")
        except ValueError:
            continue
    print(f"⚠️ Invalid date format: {date_str}")
    return None 