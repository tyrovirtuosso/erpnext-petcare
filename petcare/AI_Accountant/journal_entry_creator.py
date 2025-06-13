import frappe
from .preprocessor import split_links

def create_and_insert_journal_entry(ai_fields: dict, transaction: dict, company_name: str, COMPANY_GSTIN: str):
    posting_date = transaction.get("Transaction Date")
    reference_number = transaction.get("Tran. Id")
    custom_vendor = transaction.get("Supplier (Vendor)")
    transaction_remarks = transaction.get("Transaction Remarks", "")
    notes = transaction.get("Notes", "")
    title = ai_fields.get("title", "")

    # Compose the common user_remark
    user_remark = f"{title}\n\n{transaction_remarks}"
    if notes:
        user_remark = f"{user_remark}\n\nNotes: {notes}"

    # Append invoice links to user_remark if present
    invoice_links = transaction.get("Links to Invoice", "")
    if invoice_links:
        links_list = split_links(invoice_links)
        if links_list:
            links_formatted = "\n".join(links_list)
            user_remark = f"{user_remark}\nInvoice Link(s):\n{links_formatted}"

    # Build accounts without individual user_remark
    accounts = []
    for acc in ai_fields["accounts"]:
        accounts.append({
            "account": acc["account"],
            "debit_in_account_currency": acc["debit_in_account_currency"],
            "credit_in_account_currency": acc["credit_in_account_currency"]
        })

    journal_entry = frappe.get_doc({
        "doctype": "Journal Entry",
        "company": company_name,
        "company_gstin": COMPANY_GSTIN,
        "posting_date": posting_date,
        "cheque_no": reference_number,
        "cheque_date": posting_date,
        "voucher_type": "Journal Entry",
        "accounts": accounts,
        "user_remark": user_remark,
        "title": title,
        "custom_vendor": custom_vendor
    })
    journal_entry.insert(ignore_permissions=True)
    frappe.db.commit()
    return journal_entry.name 