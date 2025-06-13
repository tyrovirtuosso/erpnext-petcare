import frappe
import gspread
from datetime import datetime
from oauth2client.service_account import ServiceAccountCredentials
from petcare.api.google_sheet_config import (
    SPREADSHEET_URL, DEFAULT_SHEET_NAME, SERVICE_ACCOUNT_JSON, FILTER_SETS,
    BANK_ACCOUNT, DEFAULT_BANK_COST_CENTER, CREDITOR_ACCOUNT, COMPANY_NAME, COMPANY_GSTIN
)

# Define scope
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]

# Authenticate using the service account JSON file
def get_google_sheets_client():
    creds = ServiceAccountCredentials.from_json_keyfile_name(SERVICE_ACCOUNT_JSON, scope)
    return gspread.authorize(creds)

# Function to get all sheet names
def get_sheet_names():
    client = get_google_sheets_client()
    spreadsheet = client.open_by_url(SPREADSHEET_URL)
    return [sheet.title for sheet in spreadsheet.worksheets()]

# Function to get column headers from a specific sheet
def get_sheet_columns(sheet_name=DEFAULT_SHEET_NAME):
    client = get_google_sheets_client()
    spreadsheet = client.open_by_url(SPREADSHEET_URL)
    
    # Open the specific sheet
    worksheet = spreadsheet.worksheet(sheet_name)

    # Get the first row (header row)
    return worksheet.row_values(1)

def get_google_sheet_data(sheet_name=DEFAULT_SHEET_NAME):
    """Fetches Google Sheet data only once to avoid multiple API calls."""
    client = get_google_sheets_client()
    spreadsheet = client.open_by_url(SPREADSHEET_URL)
    worksheet = spreadsheet.worksheet(sheet_name)
    all_data = worksheet.get_all_values()  # Fetch all rows once
    headers = all_data[0] if all_data else []
    return headers, all_data[1:]  # Return headers & data (excluding header row)


def get_filtered_transactions(sheet_name=DEFAULT_SHEET_NAME, filter_type="truck_diesel"):
    """
    Fetches filtered transactions based on predefined filter sets.
    
    Args:
        sheet_name: Name of the sheet to fetch data from
        filter_type: Key from FILTER_SETS dictionary to use for filtering
    
    Returns:
        List of filtered transactions
    """
    # Get the appropriate filters or default to truck_diesel
    filters = FILTER_SETS.get(filter_type, FILTER_SETS["truck_diesel"])
    
    headers, all_data = get_google_sheet_data(sheet_name)  # Fetch data once

    if not all_data:
        return []

    column_indexes = {f["column"]: headers.index(f["column"]) for f in filters if f["column"] in headers}

    filtered_transactions = []
    for row in all_data:
        if len(row) < max(column_indexes.values()) + 1:
            continue

        match = all(
            (f["contains"].lower() in row[column_indexes[f["column"]]].strip().lower()) if "contains" in f else
            (f["not_equals"].lower() != row[column_indexes[f["column"]]].strip().lower()) if "not_equals" in f else True
            for f in filters
        )

        if match:
            filtered_transactions.append(row)

    return filtered_transactions


def format_transaction_date(date_str):
    """ Ensures 'Transaction Date' is in 'YYYY-MM-DD' format for ERPNext. """
    date_formats = ["%d/%b/%Y", "%d-%b-%Y", "%d/%m/%Y", "%d-%m-%Y"]

    for fmt in date_formats:
        try:
            date_obj = datetime.strptime(date_str, fmt)
            return date_obj.strftime("%Y-%m-%d")  # ERPNext expects YYYY-MM-DD format
        except ValueError:
            continue  # Try next format

    print(f"⚠️ Invalid date format: {date_str}")  # Debugging
    return None  # Return None if all formats fail

import time
import random

def update_transaction_status(reference_number, sheet_name=DEFAULT_SHEET_NAME):
    """
    Updates the 'Transaction Entered?' column for a given reference number in Google Sheets.
    Uses batch update to avoid multiple API requests.
    """
    client = get_google_sheets_client()
    spreadsheet = client.open_by_url(SPREADSHEET_URL)
    worksheet = spreadsheet.worksheet(sheet_name)

    headers, all_data = get_google_sheet_data(sheet_name)  # Use cached data

    # Find column indexes
    transaction_entered_col = headers.index("Transaction Entered?") if "Transaction Entered?" in headers else None
    reference_col = headers.index("Tran. Id") if "Tran. Id" in headers else None

    if transaction_entered_col is None or reference_col is None:
        print("⚠️ Required columns not found in the sheet.")
        return

    updates = []
    for row_index, row in enumerate(all_data, start=2):  # Start from row 2
        if row[reference_col] == reference_number:
            updates.append({
                "range": f"{gspread.utils.rowcol_to_a1(row_index, transaction_entered_col + 1)}",
                "values": [["YES"]]
            })

    if updates:
        worksheet.batch_update(updates)  # Single API call to update multiple rows
        print(f"✅ Updated Transaction Entered? for Transaction ID: {reference_number}")
    else:
        print(f"⚠️ Could not find Transaction ID {reference_number} in Google Sheets.")

    time.sleep(1)  # Add a small delay to prevent hitting API rate limits


    

def create_journal_entries(filter_type="truck_diesel"):
    """
    Creates Journal Entries for transactions with correct Debit & Credit allocations.
    
    Args:
        filter_type: Type of transactions to process (key from FILTER_SETS)
    """
    transactions = get_filtered_transactions(filter_type=filter_type)
    if not transactions:
        print(f"No transactions found for Journal Entry creation with filter: {filter_type}")
        return

    print(f"\n{'='*80}")
    print(f"🔍 PROCESSING {filter_type.upper()} TRANSACTIONS")
    print(f"{'='*80}")
    
    processed_count = 0
    skipped_count = 0
    
    # Add retry counter for API rate limits
    retry_count = 0
    max_retries = 5

    for transaction in transactions:
        try:
            headers = get_sheet_columns()  # Fetch headers dynamically
            column_map = {col: headers.index(col) for col in headers if col in headers}

            # Ensure we do not get out-of-bounds errors
            def safe_get(row, index):
                return row[index] if index >= 0 and index < len(row) else ""

            # Extract required values safely
            transaction_date = safe_get(transaction, column_map.get("Transaction Date", -1))
            reference_number = safe_get(transaction, column_map.get("Tran. Id", -1))
            notes = safe_get(transaction, column_map.get("Notes", -1))
            remarks = safe_get(transaction, column_map.get("Remarks", -1))
            cost_center = safe_get(transaction, column_map.get("Cost Center", -1))            
            account = safe_get(transaction, column_map.get("Account", -1))
            supplier = safe_get(transaction, column_map.get("Supplier (Vendor)", -1))
            
            # Get invoice links if available
            invoice_links_raw = safe_get(transaction, column_map.get("Links to Invoice", -1))
            
            print(f"\n{'-'*80}")
            print(f"📊 TRANSACTION: {reference_number}")
            print(f"{'-'*80}")
            
            # Check for required fields
            missing_fields = []
            if not remarks.strip():
                missing_fields.append("Remarks")
            if not cost_center.strip():
                missing_fields.append("Cost Center")
            if not account.strip():
                missing_fields.append("Account")
                
            if missing_fields:
                print(f"⚠️ SKIPPED: Missing required fields: {', '.join(missing_fields)}")
                skipped_count += 1
                continue
            
            # Process invoice links if available
            formatted_invoice_links = ""
            if invoice_links_raw.strip():
                # Split by common separators (comma, space, newline)
                links = []
                for separator in [',', ' ', '\n']:
                    if separator in invoice_links_raw:
                        links.extend([link.strip() for link in invoice_links_raw.split(separator) if link.strip()])
                        break
                else:
                    # If no separator found, treat as a single link
                    links = [invoice_links_raw.strip()]
                
                # Format links for markdown
                if links:
                    formatted_invoice_links = "\n\n📎 Invoice Links:\n" + "\n".join([f"🔗 [Invoice {i+1}]({link})" for i, link in enumerate(links)])
                    print(f"📎 Found {len(links)} invoice link(s)")
            
            # Prepare enhanced remarks with invoice links
            enhanced_remarks = remarks + formatted_invoice_links
            
            # Convert empty values to 0
            def to_float(value):
                try:
                    return float(value.replace(',', '')) if value.strip() else 0.0
                except ValueError:
                    return 0.0  # If conversion fails, return 0

            withdrawal_amt = to_float(safe_get(transaction, column_map.get("Withdrawal Amt (INR)", -1)))
            deposit_amt = to_float(safe_get(transaction, column_map.get("Deposit Amt (INR)", -1)))
            
            # Format the transaction date
            posting_date = format_transaction_date(transaction_date)
            if not posting_date:
                print(f"⚠️ SKIPPED: Invalid date format '{transaction_date}'")
                skipped_count += 1
                continue
            
            # Check for existing entries
            existing_entry = frappe.get_all(
                "Journal Entry",
                filters={"cheque_no": reference_number, "docstatus": 1},  # ✅ Only Submitted Entries
                fields=["name"]
            )

            if existing_entry:
                print(f"🔄 SKIPPED: Journal Entry already exists ({existing_entry[0]['name']})")
                skipped_count += 1
                continue  # Skip this transaction
            
            # Print transaction details in a structured format
            print(f"📅 Date: {posting_date} (Original: {transaction_date})")
            print(f"🔖 Reference: {reference_number}")
            print(f"📝 Description: {notes}")
            print(f"💼 Account: {account}")
            print(f"📊 Amount: {'₹'+str(withdrawal_amt) if withdrawal_amt else '₹0'} (Debit) | {'₹'+str(deposit_amt) if deposit_amt else '₹0'} (Credit)")
            print(f"🏢 Cost Center: {cost_center}")
            if supplier.strip():
                print(f"🏭 Supplier: {supplier}")
            if formatted_invoice_links:
                print(f"📎 Invoice links added to remarks")
            
            # Create Journal Entry
            journal_entry = frappe.get_doc({
                "doctype": "Journal Entry",
                "title": notes,
                "company": COMPANY_NAME,
                "company_gstin": COMPANY_GSTIN,
                "posting_date": posting_date,
                "cheque_no": reference_number,
                "cheque_date": posting_date,
                "user_remark": enhanced_remarks,  # Use enhanced remarks with invoice links
                "voucher_type": "Journal Entry",
                "accounts": []
            })
            
            # Handle supplier transactions differently
            if supplier.strip():
                # For supplier transactions, we need to create a different set of entries
                if withdrawal_amt:
                    # 1. Debit the expense account
                    journal_entry.append("accounts", {
                        "account": account,  # Expense account
                        "debit_in_account_currency": float(withdrawal_amt),
                        "cost_center": cost_center
                    })
                    
                    # 2. Credit the creditor account with supplier as party
                    journal_entry.append("accounts", {
                        "account": CREDITOR_ACCOUNT,
                        "credit_in_account_currency": float(withdrawal_amt),
                        "party_type": "Supplier",
                        "party": supplier,
                        "cost_center": cost_center
                    })
                    
                    # 3. Debit the creditor account with supplier as party
                    journal_entry.append("accounts", {
                        "account": CREDITOR_ACCOUNT,
                        "debit_in_account_currency": float(withdrawal_amt),
                        "party_type": "Supplier",
                        "party": supplier,
                        "cost_center": cost_center
                    })
                    
                    # 4. Credit the bank account
                    journal_entry.append("accounts", {
                        "account": BANK_ACCOUNT,
                        "credit_in_account_currency": float(withdrawal_amt),
                        "cost_center": DEFAULT_BANK_COST_CENTER
                    })
                    
                    print(f"🏭 Created supplier withdrawal transaction with 4 entries")
                
                # Handle deposit transactions for suppliers
                elif deposit_amt:
                    # 1. Debit the bank account
                    journal_entry.append("accounts", {
                        "account": BANK_ACCOUNT,
                        "debit_in_account_currency": float(deposit_amt),
                        "cost_center": DEFAULT_BANK_COST_CENTER
                    })
                    
                    # 2. Credit the creditor account with supplier as party
                    journal_entry.append("accounts", {
                        "account": CREDITOR_ACCOUNT,
                        "credit_in_account_currency": float(deposit_amt),
                        "party_type": "Supplier",
                        "party": supplier,
                        "cost_center": cost_center
                    })
                    
                    # 3. Debit the creditor account with supplier as party
                    journal_entry.append("accounts", {
                        "account": CREDITOR_ACCOUNT,
                        "debit_in_account_currency": float(deposit_amt),
                        "party_type": "Supplier",
                        "party": supplier,
                        "cost_center": cost_center
                    })
                    
                    # 4. Credit the income/asset account
                    journal_entry.append("accounts", {
                        "account": account,
                        "credit_in_account_currency": float(deposit_amt),
                        "cost_center": cost_center
                    })
                    
                    print(f"🏭 Created supplier deposit transaction with 4 entries")
            
            else:
                # Process regular withdrawal transactions (money going out)
                if withdrawal_amt and account:
                    journal_entry.append("accounts", {
                        "account": account,  # Expense or liability account
                        "debit_in_account_currency": float(withdrawal_amt or 0),
                        "cost_center": cost_center  # Assign cost center
                    })

                    journal_entry.append("accounts", {
                        "account": BANK_ACCOUNT,  # Bank is credited
                        "credit_in_account_currency": float(withdrawal_amt or 0),
                        "cost_center": DEFAULT_BANK_COST_CENTER  # Bank's cost center
                    })

                # Process deposit transactions (money coming in)
                if deposit_amt and account:
                    journal_entry.append("accounts", {
                        "account": BANK_ACCOUNT,  # Bank is debited
                        "debit_in_account_currency": float(deposit_amt),
                        "cost_center": DEFAULT_BANK_COST_CENTER  # Bank's cost center
                    })

                    journal_entry.append("accounts", {
                        "account": account,  # Income or asset account
                        "credit_in_account_currency": float(deposit_amt),
                        "cost_center": cost_center  # Assign cost center
                    })

            # Ensure the entry balances before saving
            total_debit = sum(float(entry.get("debit_in_account_currency", 0) or 0) for entry in journal_entry.get("accounts"))
            total_credit = sum(float(entry.get("credit_in_account_currency", 0) or 0) for entry in journal_entry.get("accounts"))

            if total_debit != total_credit:
                print(f"⚠️ SKIPPED: Unbalanced entry (Dr: ₹{total_debit}, Cr: ₹{total_credit})")
                skipped_count += 1
                continue

            # Insert the Journal Entry as a draft
            journal_entry.insert(ignore_permissions=True)

            # Submit the Journal Entry
            journal_entry.submit()

            # Commit the changes
            frappe.db.commit()
            
            # Verify that the Journal Entry has been submitted
            submitted_entry = frappe.get_value("Journal Entry", journal_entry.name, "docstatus")

            if submitted_entry == 1:
                print(f"✅ SUCCESS: Journal Entry {journal_entry.name} created and submitted")
                
                # Update Google Sheet with "YES"
                update_transaction_status(reference_number)
                processed_count += 1
                
                # Reset retry counter after successful operation
                retry_count = 0
                
                # Add a small delay between transactions
                time.sleep(1)
            else:
                print(f"⚠️ ERROR: Journal Entry {journal_entry.name} was not submitted properly")
                skipped_count += 1

        except Exception as e:
            error_message = str(e)
            print(f"❌ ERROR processing transaction {reference_number}: {error_message}")
            
            # Check if it's a rate limit error
            if "Quota exceeded" in error_message or "429" in error_message:
                retry_count += 1
                if retry_count <= max_retries:
                    # Exponential backoff with jitter
                    wait_time = (2 ** retry_count) + random.uniform(0, 1)
                    print(f"⏳ Rate limit exceeded. Waiting for {wait_time:.1f} seconds before retry ({retry_count}/{max_retries})...")
                    time.sleep(wait_time)
                    # Try the same transaction again
                    continue
                else:
                    print("⛔ Maximum retries exceeded. Please try again later.")
            
            skipped_count += 1
    
    # Print summary at the end
    print(f"\n{'='*80}")
    print(f"📊 SUMMARY: {filter_type.upper()} TRANSACTIONS")
    print(f"{'='*80}")
    print(f"✅ Successfully processed: {processed_count}")
    print(f"⚠️ Skipped/Failed: {skipped_count}")
    print(f"📈 Total transactions: {processed_count + skipped_count}")
    print(f"{'='*80}\n")
