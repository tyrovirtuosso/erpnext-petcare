from .chart_of_accounts_cache import load_chart_of_accounts
from .utils import prune_chart_of_accounts_for_ai, summarize_transaction, summarize_ai_fields, summarize_link_summaries, TermColors
from .transaction_fetcher import fetch_transactions_in_batches
from .preprocessor import preprocess_transaction
from .ai_handler import generate_journal_entry_ai
from .journal_entry_creator import create_and_insert_journal_entry
from .config import SPREADSHEET_URL, COMPANY_NAME, COMPANY_GSTIN, DEFAULT_SHEET_NAME
import sys

# --- CONFIGURATION ---
BATCH_SIZE = 1000  # Set batch size here or import from config if you add it there
EXCLUDE_COLUMNS = ["Transaction Entered?", "Account Type", "Remarks", "Value Date", "Transaction Posted Date", "Cheque. No./Ref. No.", "Balance (INR)", "Supplier (Vendor) (not added previously)"]

# List of Tran. Ids to process; set to None or [] to process all
TRAN_ID_LIST = ["S99209031"]  # Example; replace with your list or leave empty for all

# Max number of transactions to process; set to None or 0 to process all
MAX_TRANSACTIONS = 0

def filter_fn(transaction):
    # Exclude if Account is "Sales - MP"
    if transaction.get("Account") == "Sales - MP":
        return False
    # Only process if Tran. Id is in the list (if list is set)
    if TRAN_ID_LIST:
        return transaction.get("Tran. Id") in TRAN_ID_LIST
    return True

def main():
    chart_of_accounts = load_chart_of_accounts()
    chart_of_accounts_for_ai = prune_chart_of_accounts_for_ai(chart_of_accounts)
    print("Loaded chart of accounts.")
    batch_num = 0
    processed_count = 0
    filtered_count = 0
    
    for batch in fetch_transactions_in_batches(
            DEFAULT_SHEET_NAME, BATCH_SIZE, filter_fn=filter_fn,
            spreadsheet_url=SPREADSHEET_URL, exclude_columns=EXCLUDE_COLUMNS):
        batch_num += 1
        print(f"{TermColors.HEADER}Processing batch {batch_num} with {len(batch)} transactions...{TermColors.ENDC}")
        
        for transaction in batch:
            if MAX_TRANSACTIONS and processed_count >= MAX_TRANSACTIONS:
                print(f"Reached MAX_TRANSACTIONS ({MAX_TRANSACTIONS}). Stopping.")
                break

            transaction_number = processed_count + 1
            tran_id = transaction.get('Tran. Id', 'N/A')
            print(f"\n{TermColors.BOLD}=== Processing Transaction {transaction_number} (Tran. Id: {tran_id}) ==={TermColors.ENDC}")            
            result = preprocess_transaction(transaction, skip_if_docstatus=[1, 0])
            if result['skip']:
                print(f"{TermColors.WARNING}SKIPPED: Tran. Id {tran_id} | Reason: {result['reason']}{TermColors.ENDC}")
                filtered_count += 1
                continue

            ai_fields = generate_journal_entry_ai(result['transaction'], result['pdf_text'], chart_of_accounts_for_ai)
            if not ai_fields.get('accounts') or (isinstance(ai_fields.get('title'), str) and ai_fields['title'].strip().lower().startswith('error:')):
                print(f"{TermColors.FAIL}AI ERROR: Tran. Id {tran_id} | {ai_fields.get('title')}{TermColors.ENDC}")
                filtered_count += 1
                continue

            print(f"{TermColors.OKBLUE}Summary: {summarize_transaction(result['transaction'])}{TermColors.ENDC}")
            print(f"{TermColors.OKCYAN}AI: {summarize_ai_fields(ai_fields)}{TermColors.ENDC}")
            print(f"{TermColors.HEADER}{summarize_link_summaries(result.get('link_summaries'))}{TermColors.ENDC}")

            je_name = create_and_insert_journal_entry(ai_fields, result['transaction'], COMPANY_NAME, COMPANY_GSTIN)
            print(f"{TermColors.OKGREEN}SUCCESS: Journal Entry '{je_name}' created for Tran. Id {tran_id}{TermColors.ENDC}")

            processed_count += 1
            print(f"{TermColors.BOLD}--- End of Transaction {transaction_number} ---{TermColors.ENDC}")
            
        if MAX_TRANSACTIONS and processed_count >= MAX_TRANSACTIONS:
            break
            
    print(f"\n{TermColors.BOLD}Processing Summary:{TermColors.ENDC}")
    print(f"Total transactions processed: {processed_count}")
    print(f"Total transactions filtered: {filtered_count}")
    print(f"Total batches processed: {batch_num}")
    print(f"{TermColors.OKGREEN}All batches processed.{TermColors.ENDC}")

if __name__ == "__main__":
    main()


# bench execute petcare.AI_Accountant.main_workflow.main