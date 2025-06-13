import frappe
import fitz  # pymupdf
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from .config import COMPANY_NAME, SPREADSHEET_URL, DEFAULT_SHEET_NAME, SERVICE_ACCOUNT_JSON
from typing import List, Dict, Optional
import time
from datetime import datetime
import re
import requests
import os
from .google_drive_utils import get_drive_file_extension
from PIL import Image
import pytesseract

class TermColors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

def get_chart_of_accounts(company_name: Optional[str] = None) -> List[Dict]:
    """
    Fetch all chart of accounts for the given company.
    If company_name is not provided, uses COMPANY_NAME from config.
    Returns a list of account dicts.
    """
    company = company_name or COMPANY_NAME
    accounts = frappe.get_all(
        "Account",
        filters={"company": company},
        fields=["name", "account_name", "account_type", "parent_account", "is_group"]
    )
    return accounts

def build_account_tree(accounts: List[Dict]) -> List[Dict]:
    """
    Convert a flat list of accounts into a nested tree structure for AI context.
    Preserves the original account names.
    Returns a list of root account nodes, each with nested 'children'.
    """
    # Create a mapping from name to account node
    name_to_node = {}
    for acc in accounts:
        node = {
            "name": acc["name"],
            "account_name": acc["account_name"],
            "account_type": acc["account_type"],
            "is_group": acc["is_group"],
            "children": []
        }
        name_to_node[acc["name"]] = node
    # Build the tree
    roots = []
    for acc in accounts:
        node = name_to_node[acc["name"]]
        parent_name = acc["parent_account"]
        if parent_name and parent_name in name_to_node:
            name_to_node[parent_name]["children"].append(node)
        else:
            roots.append(node)
    return roots

def extract_pdf_text(pdf_path: str) -> str:
    """
    Extract text from a PDF file using pymupdf (fitz). If no text is found, fallback to OCR using pytesseract.
    Returns the extracted text or an error message.
    """
    try:
        # First, try extracting text using fitz
        doc = fitz.open(pdf_path)
        text = "\n".join(page.get_text() for page in doc)
        if text and text.strip():
            doc.close()
            return text
        # If no text, fallback to OCR
        ocr_texts = []
        for page_num in range(len(doc)):
            page = doc.load_page(page_num)
            pix = page.get_pixmap()
            img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
            ocr_text = pytesseract.image_to_string(img)
            ocr_texts.append(ocr_text)
        doc.close()
        ocr_result = "\n".join(ocr_texts)
        return ocr_result if ocr_result.strip() else ""
    except Exception as e:
        return f"Error reading PDF: {e}"

def get_google_sheets_client(service_account_json: str = SERVICE_ACCOUNT_JSON) -> gspread.client.Client:
    """
    Authenticate and return a gspread client using the given service account JSON file.
    """
    scope = [
        "https://spreadsheets.google.com/feeds",
        "https://www.googleapis.com/auth/drive"
    ]
    creds = ServiceAccountCredentials.from_json_keyfile_name(service_account_json, scope)
    return gspread.authorize(creds)

def get_sheet_names(
    spreadsheet_url: str = SPREADSHEET_URL,
    service_account_json: str = SERVICE_ACCOUNT_JSON
) -> list[str]:
    """
    Return all sheet names in the spreadsheet.
    """
    client = get_google_sheets_client(service_account_json)
    spreadsheet = client.open_by_url(spreadsheet_url)
    return [sheet.title for sheet in spreadsheet.worksheets()]

def get_sheet_columns(
    sheet_name: str = DEFAULT_SHEET_NAME,
    spreadsheet_url: str = SPREADSHEET_URL,
    service_account_json: str = SERVICE_ACCOUNT_JSON
) -> list[str]:
    """
    Return the column headers (first row) from the specified sheet.
    """
    client = get_google_sheets_client(service_account_json)
    spreadsheet = client.open_by_url(spreadsheet_url)
    worksheet = spreadsheet.worksheet(sheet_name)
    return worksheet.row_values(1)

def get_google_sheet_data(
    sheet_name: str = DEFAULT_SHEET_NAME,
    spreadsheet_url: str = SPREADSHEET_URL,
    service_account_json: str = SERVICE_ACCOUNT_JSON
) -> tuple[list[str], list[list[str]]]:
    """
    Fetch all data from the specified Google Sheet.
    Returns (headers, data_rows) where headers is the first row and data_rows is a list of rows (excluding header).
    """
    client = get_google_sheets_client(service_account_json)
    spreadsheet = client.open_by_url(spreadsheet_url)
    worksheet = spreadsheet.worksheet(sheet_name)
    all_data = worksheet.get_all_values()
    headers = all_data[0] if all_data else []
    return headers, all_data[1:]

def check_journal_entry_by_cheque_no(cheque_no: str, docstatus: Optional[int] = None) -> List[Dict]:
    """
    Check if a Journal Entry with the given cheque_no exists.
    Optionally filter by docstatus (0: Draft, 1: Submitted).
    Returns a list of matching entries (with name and docstatus).
    """
    filters = {"cheque_no": cheque_no}
    if docstatus is not None:
        filters["docstatus"] = docstatus
    entries = frappe.get_all(
        "Journal Entry",
        filters=filters,
        fields=["name", "docstatus"]
    )
    return entries

def get_structured_transactions_from_sheet(
    sheet_name: str = DEFAULT_SHEET_NAME,
    spreadsheet_url: str = SPREADSHEET_URL,
    service_account_json: str = SERVICE_ACCOUNT_JSON
) -> List[Dict[str, str]]:
    """
    Fetch all transactions from the Google Sheet and return as a list of dicts (one per row),
    using the headers as keys. Allows optional override of sheet name, spreadsheet URL, and service account path.
    """
    headers, rows = get_google_sheet_data(sheet_name, spreadsheet_url, service_account_json)
    transactions = [dict(zip(headers, row)) for row in rows]
    return transactions

def fetch_google_sheet_in_batches(
    sheet_name: str = DEFAULT_SHEET_NAME,
    spreadsheet_url: str = SPREADSHEET_URL,
    service_account_json: str = SERVICE_ACCOUNT_JSON,
    batch_size: int = 1000,
    sleep_time: float = 1.5
):
    client = get_google_sheets_client(service_account_json)
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
        # Convert each row to a dict using headers
        batch_dicts = [dict(zip(headers, row)) for row in batch]
        yield batch_dicts
        start += batch_size
        print(f"Fetched {start} rows")
        time.sleep(sleep_time)

def format_transaction_date(date_str):
    """Ensures 'Transaction Date' is in 'YYYY-MM-DD' format for ERPNext."""
    date_formats = ["%d/%b/%Y", "%d-%b-%Y", "%d/%m/%Y", "%d-%m-%Y"]
    for fmt in date_formats:
        try:
            date_obj = datetime.strptime(date_str, fmt)
            return date_obj.strftime("%Y-%m-%d")
        except ValueError:
            continue
    print(f"⚠️ Invalid date format: {date_str}")
    return None

def get_openai_api_key() -> str:
    key_path = "/home/frappe-user/frappe-bench/keys/openai_api_key.txt"
    with open(key_path, "r") as f:
        return f.read().strip()

def extract_drive_file_id(url: str) -> str:
    """Extract the file ID from a Google Drive share link."""
    match = re.search(r"/d/([\w-]+)", url)
    if match:
        return match.group(1)
    match = re.search(r"id=([\w-]+)", url)
    if match:
        return match.group(1)
    return None

def download_drive_pdf(file_id: str, dest_path: str) -> bool:
    """Download a public Google Drive PDF by file ID. Returns True if successful."""
    if not file_id:
        return False
    url = f"https://drive.google.com/uc?export=download&id={file_id}"
    try:
        response = requests.get(url)
        if response.status_code == 200:
            with open(dest_path, "wb") as f:
                f.write(response.content)
            return True
        else:
            return False
    except Exception:
        return False

def get_drive_file_extension_util(drive_url_or_id: str) -> str:
    """
    Wrapper for get_drive_file_extension from google_drive_utils for convenient use in utils.py.
    Returns the file extension as a string, or an empty string if not found.
    """
    ext = get_drive_file_extension(drive_url_or_id)
    return ext or ""

IMAGE_EXTENSIONS = {"jpg", "jpeg", "png", "bmp", "gif", "tiff", "webp"}

def extract_text_from_drive_file(drive_url_or_id: str) -> str:
    """
    Given a Google Drive link or file ID, checks the extension. If it's an image, downloads and extracts text using Pillow and pytesseract.
    Returns the extracted text, or an error message.
    """
    ext = get_drive_file_extension_util(drive_url_or_id).lower()
    if ext in IMAGE_EXTENSIONS:
        file_id = extract_drive_file_id(drive_url_or_id)
        if not file_id:
            return "Could not extract file ID from the provided link."
        temp_path = f"/tmp/{file_id}.{ext}"
        if download_drive_pdf(file_id, temp_path):
            try:
                image = Image.open(temp_path)
                text = pytesseract.image_to_string(image)
                return text.strip()
            except Exception as e:
                return f"Failed to extract text from image: {e}"
        else:
            return "Failed to download image from Google Drive."
    else:
        return "Not an image file."

def clean_invoice_text(raw_text: str) -> str:
    # Remove non-printable characters
    cleaned = ''.join(c for c in raw_text if c.isprintable())
    # Remove repeated newlines and extra spaces
    cleaned = re.sub(r'\n+', '\n', cleaned)
    cleaned = re.sub(r'[ \t]+', ' ', cleaned)
    # Remove lines that are just UI artifacts or very short
    lines = cleaned.split('\n')
    lines = [line.strip() for line in lines if len(line.strip()) > 2 and not re.match(r'^[^a-zA-Z0-9]*$', line)]
    # Optionally, extract only the section between known markers
    # Example: between "Invoice Details" and "Total Amount"
    start, end = None, None
    for i, line in enumerate(lines):
        if 'Invoice Details' in line:
            start = i
        if 'Total Amount' in line or 'Grand Total' in line:
            end = i
            break
    if start is not None and end is not None and end > start:
        lines = lines[start:end+1]
    return '\n'.join(lines)

def prune_chart_of_accounts_for_ai(chart):
    """
    Recursively prune the chart of accounts tree to only include 'name' and 'children' fields.
    Returns a new tree structure suitable for AI context.
    """
    if isinstance(chart, list):
        return [prune_chart_of_accounts_for_ai(node) for node in chart]
    if isinstance(chart, dict):
        return {
            'name': chart['name'],
            'children': prune_chart_of_accounts_for_ai(chart.get('children', []))
        }
    return chart

def summarize_transaction(transaction: dict) -> str:
    fields = [
        ("Tran. Id", transaction.get("Tran. Id")),
        ("Date", transaction.get("Transaction Date")),
        ("Withdrawal", transaction.get("Withdrawal Amt (INR)")),
        ("Deposit", transaction.get("Deposit Amt (INR)")),
        ("Supplier", transaction.get("Supplier (Vendor)")),
        ("Notes", transaction.get("Notes")),
    ]
    summary = " | ".join(f"{label}: {value}" for label, value in fields if value)
    return summary

def summarize_ai_fields(ai_fields: dict) -> str:
    lines = []
    title = ai_fields.get('title')
    if title:
        lines.append(f"Title: {title}")
    accounts = ai_fields.get('accounts', [])
    if accounts:
        lines.append("Accounts:")
        for acc in accounts:
            acc_line = (
                f"  - Account: {acc.get('account')}, "
                f"Debit: {acc.get('debit_in_account_currency', 0)}, "
                f"Credit: {acc.get('credit_in_account_currency', 0)}, "
                f"Remark: {acc.get('user_remark', '')}"
            )
            lines.append(acc_line)
    else:
        lines.append("No accounts generated.")
    return "\n".join(lines)

def summarize_link_summaries(link_summaries):
    if not link_summaries:
        return "Invoice links: None"
    counts = {}
    errors = 0
    for l in link_summaries:
        t = l['type']
        counts[t] = counts.get(t, 0) + 1
        if l['status'] != 'success':
            errors += 1
    parts = [f"{v} {k.upper()}" for k, v in counts.items()]
    msg = f"Invoice links: {len(link_summaries)} found ({', '.join(parts)})"
    if errors:
        msg += f", {errors} error(s)"
    return msg

def parse_amount(value):
    if isinstance(value, str):
        value = value.replace(",", "")
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0 