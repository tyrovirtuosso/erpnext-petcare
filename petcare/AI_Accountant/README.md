# AI Accountant

Automated journal entry creation for ERPNext using AI and Google Sheets/Drive integration.

## Overview
This module automates the process of fetching transaction data from Google Sheets, extracting and processing invoice data from Google Drive, and generating double-entry journal entries using AI (OpenAI API). The entries are then inserted into ERPNext, streamlining accounting workflows for Masterpet Care Private Limited.

## Directory Structure & File Roles

- **main_workflow.py**: Orchestrates the end-to-end workflow: loads chart of accounts, fetches transactions, preprocesses data, invokes AI, and creates journal entries.
- **ai_handler.py**: Handles communication with the OpenAI API to generate journal entry suggestions based on transaction and invoice data.
- **utils.py**: Utility functions for Google Sheets, Google Drive, PDF/text extraction, data cleaning, and summarization.
- **preprocessor.py**: Preprocesses each transaction, checks for duplicates, formats dates, and extracts invoice text from Drive links.
- **transaction_fetcher.py**: Fetches transactions from Google Sheets in batches, applies filters, and excludes specified columns.
- **google_drive_utils.py**: Utilities for authenticating with Google Drive, extracting file/folder IDs, listing files, and getting file extensions.
- **journal_entry_creator.py**: Creates and inserts journal entries into ERPNext using the processed data and AI output.
- **chart_of_accounts_cache.py**: Loads and caches the chart of accounts as a tree structure for efficient AI context.
- **config.py**: Central configuration for spreadsheet URL, sheet name, service account path, company details, etc.
- **chart_of_accounts.json**: Cached chart of accounts in a hierarchical (tree) format for AI and workflow use.
- **sample.pdf**: Example PDF file for testing invoice extraction and OCR routines.

## Setup

1. **Python Dependencies**
   - frappe
   - gspread
   - openai
   - instructor
   - pydantic
   - fitz (PyMuPDF)
   - Pillow (PIL)
   - pytesseract
   - google-api-python-client
   - oauth2client
   - requests

2. **Service Account & API Keys**
   - Place your Google service account JSON at the path specified in `config.py` and `google_drive_utils.py`.
   - Place your OpenAI API key in `/home/frappe-user/frappe-bench/keys/openai_api_key.txt`.

3. **ERPNext**
   - This module is designed to run within a Frappe/ERPNext environment.

## Configuration

All main configuration is in `config.py`:

| Variable Name              | Location         | Description                                                                 | How to Change                                                                                 |
|----------------------------|------------------|-----------------------------------------------------------------------------|-----------------------------------------------------------------------------------------------|
| `SPREADSHEET_URL`          | `config.py`      | URL of the Google Sheet containing transactions.                            | Replace with your own Google Sheet URL.                                                       |
| `DEFAULT_SHEET_NAME`       | `config.py`      | Name of the worksheet/tab to process.                                       | Change to the desired sheet/tab name.                                                         |
| `SERVICE_ACCOUNT_JSON`     | `config.py`      | Path to your Google service account JSON file.                              | Update the path if your service account file is elsewhere.                                    |
| `COMPANY_NAME`             | `config.py`      | Name of the company for ERPNext.                                            | Change to your company's name.                                                                |
| `COMPANY_GSTIN`            | `config.py`      | GSTIN for the company.                                                      | Update to your company's GSTIN.                                                               |
| `DEFAULT_BANK_COST_CENTER` | `config.py`      | Default cost center for bank transactions.                                  | Change as needed for your accounting structure.                                               |

Other configuration points in the workflow:

| Variable Name              | Location                | Description                                                                 | How to Change                                                                                 |
|----------------------------|-------------------------|-----------------------------------------------------------------------------|-----------------------------------------------------------------------------------------------|
| `BATCH_SIZE`               | `main_workflow.py`      | Number of transactions processed per batch.                                 | Change the value at the top of `main_workflow.py`.                                            |
| `EXCLUDE_COLUMNS`          | `main_workflow.py`      | Columns to exclude from processing.                                          | Edit the list in `main_workflow.py`.                                                          |
| `TRAN_ID_LIST`             | `main_workflow.py`      | List of transaction IDs to process (empty for all).                         | Set to a list of IDs or leave empty for all transactions.                                     |
| `MAX_TRANSACTIONS`         | `main_workflow.py`      | Maximum number of transactions to process (0 or None for all).              | Change the value at the top of `main_workflow.py`.                                            |
| `OPENAI_API_KEY`           | `/keys/openai_api_key.txt` | OpenAI API key for AI journal entry generation.                             | Place your API key in the specified file.                                                     |
| `SERVICE_ACCOUNT_FILE`     | `google_drive_utils.py` | Path to Google Drive service account JSON for Drive API.                    | Update the path if your service account file is elsewhere.                                    |

### How to Change Configuration

- **Edit `config.py`** for company, sheet, and service account settings.
- **Edit `main_workflow.py`** for batch size, transaction limits, and filtering.
- **Edit `google_drive_utils.py`** if your Drive service account file is in a different location.
- **Update `/keys/openai_api_key.txt** with your OpenAI API key.

### Common Scenarios

**1. Using a Different Google Sheet**
- Change `SPREADSHEET_URL` in `config.py` to your new sheet's URL.
- If the worksheet/tab name is different, update `DEFAULT_SHEET_NAME`.

**2. Switching to a New Company**
- Update `COMPANY_NAME` and `COMPANY_GSTIN` in `config.py`.
- If your chart of accounts is different, ensure the cache is rebuilt (delete `chart_of_accounts.json` if needed).

**3. Using a Different Google Service Account**
- Update `SERVICE_ACCOUNT_JSON` in `config.py` and `SERVICE_ACCOUNT_FILE` in `google_drive_utils.py` to the new file path.

**4. Changing Batch Size or Transaction Limits**
- Edit `BATCH_SIZE` and `MAX_TRANSACTIONS` at the top of `main_workflow.py`.

**5. Processing Only Specific Transactions**
- Set `TRAN_ID_LIST` in `main_workflow.py` to a list of transaction IDs you want to process.

**6. Excluding/Including Columns**
- Edit `EXCLUDE_COLUMNS` in `main_workflow.py` to add or remove columns from processing.

**7. Multiple Environments (Dev/Prod)**
- Use different `config.py` files for each environment, or manage with environment variables and a loader script.

**8. Changing OpenAI Model or Parameters**
- Edit `ai_handler.py` to change the model name or prompt as needed.

#### Example: Changing to a New Company and Sheet

1. Open `config.py`:
   ```python
   COMPANY_NAME = "New Company Pvt Ltd"
   COMPANY_GSTIN = "12ABCDE3456F7Z8"
   SPREADSHEET_URL = "https://docs.google.com/spreadsheets/d/your_new_sheet_id/edit"
   DEFAULT_SHEET_NAME = "NewSheet"
   ```
2. If your service account file is in a new location:
   ```python
   SERVICE_ACCOUNT_JSON = "/path/to/your/service_account.json"
   ```
3. If you want to process only 100 transactions at a time, open `main_workflow.py` and set:
   ```python
   BATCH_SIZE = 100
   MAX_TRANSACTIONS = 100
   ```

## Usage

- To run the main workflow:
  ```bash
  bench execute petcare.AI_Accountant.main_workflow.main
  ```
- Adjust configuration as needed in `config.py` (spreadsheet URL, company details, etc).
- Ensure Google Sheets and Drive access is set up for the service account.

## Notes

- **Security**: Keep your API keys and service account files secure. Do not commit them to version control.
- **Data Sensitivity**: This module processes sensitive accounting and company data. Handle with care.
- **Extensibility**: Add new features or integrations by extending the relevant modules (e.g., new data sources, AI models, or ERPNext doctypes).

---

For any issues or contributions, please contact the project maintainer. 