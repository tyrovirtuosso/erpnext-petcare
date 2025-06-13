import frappe
from .list_chart_of_accounts import get_chart_of_accounts
from .invoice_insights import get_invoice_insights_for_transaction_id
from .google_sheet_fetcher import fetch_all_transactions
import openai
import instructor
import os
from petcare.api.google_sheet_api import format_transaction_date

# --- OpenAI setup (reuse your secure key loading if needed) ---
def get_openai_api_key() -> str:
    key_path = "/home/frappe-user/frappe-bench/keys/openai_api_key.txt"
    with open(key_path, "r") as f:
        return f.read().strip()

os.environ["OPENAI_API_KEY"] = get_openai_api_key()
client = instructor.from_openai(openai.OpenAI())


def get_transaction_by_id(tran_id: str, transactions):
    """Fetch a single transaction dict by Tran. Id from a list of transactions."""
    for txn in transactions:
        if txn.get("Tran. Id") == tran_id:
            return txn
    return None


def ai_select_accounts(transaction, chart_of_accounts, invoice_insights=None):
    """
    Use OpenAI to select the best accounts for the journal entry based on the chart of accounts and transaction details.
    Returns a list of dicts: [{account, debit, credit, party_type, party}]
    """
    usable_accounts = [a for a in chart_of_accounts if a.get("can_be_used_in_entry")]
    prompt = (
        "You are an expert ERPNext accountant. Only use accounts where can_be_used_in_entry is True (i.e., non-group accounts) for the journal entry. "
        "Given the following chart of accounts, transaction details, and (optionally) invoice insights, "
        "choose the most appropriate accounts for the journal entry. "
        "Return a JSON list of dicts, each with: account, debit, credit, party_type (optional), party (optional). "
        "If there is a GST/tax component, split it out. Always include a bank account for the balancing entry. "
        "\n\nChart of Accounts (non-group only):\n" +
        str(usable_accounts) +
        "\n\nTransaction Details:\n" + str(transaction) +
        ("\n\nInvoice Insights:\n" + str(invoice_insights) if invoice_insights else "") +
        "\n\nExample output: [\n  {\"account\": \"Expense Account\", \"debit\": 100, \"credit\": 0},\n  {\"account\": \"Input Tax IGST - MP\", \"debit\": 18, \"credit\": 0},\n  {\"account\": \"Bank Account - MP\", \"debit\": 0, \"credit\": 118}\n]"
    )
    try:
        openai_client = openai.OpenAI()
        response = openai_client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=512,
            temperature=0
        )
        # Parse the JSON from the response
        import json
        import re
        # Extract the first JSON array from the response
        match = re.search(r'\[.*\]', response.choices[0].message.content, re.DOTALL)
        if match:
            return json.loads(match.group(0))
        else:
            return None
    except Exception as e:
        print(f"AI account selection failed: {e}")
        return None


def create_journal_entry_with_ai(tran_id: str, company_name: str):
    """
    Fetches the chart of accounts, transaction, and invoice insights, uses AI to select accounts, and creates a Journal Entry in Frappe.
    Returns the Journal Entry doc or None.
    """
    chart_of_accounts = get_chart_of_accounts(company_name)
    # Fetch all transactions once
    all_transactions = fetch_all_transactions()
    transaction = get_transaction_by_id(tran_id, all_transactions)
    if not transaction:
        print(f"No transaction found for Tran. Id = {tran_id}")
        return None
    invoice_insights = None
    if transaction.get("Links to Invoice"):
        invoice_insights = get_invoice_insights_for_transaction_id(tran_id)
    if invoice_insights:
        print("\n[INVOICE INSIGHTS]")
        print(invoice_insights.model_dump_json(indent=2))
    else:
        print("\n[INVOICE INSIGHTS] None found or extracted.")
    ai_accounts = ai_select_accounts(transaction, chart_of_accounts, invoice_insights)
    if not ai_accounts:
        print("AI could not determine accounts for this journal entry.")
        return None
    print("\n[AI JOURNAL INSIGHTS]")
    import json
    print(json.dumps(ai_accounts, indent=2))
    # Prepare Journal Entry doc
    from petcare.api.google_sheet_config import COMPANY_GSTIN
    # Format the date for ERPNext
    posting_date = format_transaction_date(transaction.get("Transaction Date"))
    notes = transaction.get("Notes")
    remarks = transaction.get("Remarks")
    reference_number = transaction.get("Tran. Id")
    journal_entry = frappe.get_doc({
        "doctype": "Journal Entry",
        "title": notes,
        "company": company_name,
        "company_gstin": COMPANY_GSTIN,
        "posting_date": posting_date,
        "cheque_no": reference_number,
        "cheque_date": posting_date,
        "user_remark": remarks,
        "voucher_type": "Journal Entry",
        "accounts": []
    })
    for entry in ai_accounts:
        acc_args = {
            "account": entry["account"],
            "debit_in_account_currency": float(entry.get("debit", 0)),
            "credit_in_account_currency": float(entry.get("credit", 0)),
        }
        if entry.get("party_type"):
            acc_args["party_type"] = entry["party_type"]
        if entry.get("party"):
            acc_args["party"] = entry["party"]
        journal_entry.append("accounts", acc_args)
    print("\n[FINAL JOURNAL ENTRY DATA]")
    print(journal_entry.as_dict())
    
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

    return journal_entry

if __name__ == "__main__":
    TRAN_ID = "S982161419"  # Example Tran. Id
    COMPANY_NAME = "Masterpet Care Private Limited"
    create_journal_entry_with_ai(TRAN_ID, COMPANY_NAME) 