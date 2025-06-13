import os
import re
import requests
import fitz  # pymupdf
import instructor
import openai
from pydantic import BaseModel, Field
from .google_sheet_fetcher import fetch_all_transactions

# --- Securely load OpenAI API key from file ---
def get_openai_api_key() -> str:
    """Load OpenAI API key from a secure file location."""
    key_path = "/home/frappe-user/frappe-bench/keys/openai_api_key.txt"
    with open(key_path, "r") as f:
        return f.read().strip()

os.environ["OPENAI_API_KEY"] = get_openai_api_key()

# --- Create OpenAI client instance ---
client = instructor.from_openai(openai.OpenAI())

# --- Utility Functions ---
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

def extract_pdf_text(pdf_path: str) -> str:
    """Extract text from a PDF file using pymupdf."""
    try:
        doc = fitz.open(pdf_path)
        text = "\n".join(page.get_text() for page in doc)
        doc.close()
        return text
    except Exception as e:
        return f"Error reading PDF: {e}"

# --- Pydantic Model for Insights ---
class InvoiceJournalEntryInsights(BaseModel):
    invoice_number: str = Field(..., description="The invoice number")
    invoice_date: str = Field(..., description="The date of the invoice")
    vendor: str = Field(..., description="The vendor or supplier name")
    total_amount: str = Field(..., description="The total amount on the invoice")
    gst_amount: str = Field(None, description="The GST amount, if available")
    # Add more fields as needed for ERPNext

def extract_insights_from_pdf_text(pdf_text: str) -> InvoiceJournalEntryInsights:
    """Extract invoice insights from PDF text using OpenAI GPT-4o."""
    prompt = (
        "You are an expert accountant. Extract the following details from the invoice text below for creating a journal entry in ERPNext:\n"
        "- Invoice number\n"
        "- Invoice date\n"
        "- Vendor name\n"
        "- Total amount\n"
        "- GST amount (if available)\n"
        "Return the result as JSON.\n\n"
        f"Invoice text:\n{pdf_text}"
    )
    try:
        model = client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": prompt}],
            response_model=InvoiceJournalEntryInsights,
            max_tokens=512,
            temperature=0
        )
    except Exception as e:
        return None
    return model

def get_invoice_insights_for_transaction_id(transaction_id: str) -> InvoiceJournalEntryInsights:
    """
    Given a transaction ID, fetches the transaction, downloads the invoice PDF, extracts text, and returns invoice insights.
    Returns None if any step fails.
    """
    transactions = fetch_all_transactions()
    columns = [
        "Tran. Id",
        "Value Date",
        "Transaction Remarks",
        "Withdrawal Amt (INR)",
        "Deposit Amt (INR)",
        "Notes",
        "Links to Invoice",
        "Supplier (Vendor)"
    ]
    filtered = [
        {col: txn.get(col, None) for col in columns}
        for txn in transactions if txn.get("Tran. Id") == transaction_id
    ]
    if not filtered:
        return None
    txn = filtered[0]
    link = txn.get("Links to Invoice")
    if not link:
        return None
    file_id = extract_drive_file_id(link)
    pdf_path = f"invoice_{transaction_id}.pdf"
    if not download_drive_pdf(file_id, pdf_path):
        return None
    pdf_text = extract_pdf_text(pdf_path)
    os.remove(pdf_path)
    if not pdf_text or len(pdf_text) < 50:
        return None
    insights = extract_insights_from_pdf_text(pdf_text)
    return insights 