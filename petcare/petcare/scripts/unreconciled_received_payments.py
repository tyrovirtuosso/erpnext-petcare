import frappe

def list_unreconciled_received_payments():
    # Query Payment Entries with payment_type "Receive", not Cash, and no linked Bank Transaction Payments
    payment_entries = frappe.get_all(
        "Payment Entry",
        filters={
            "payment_type": "Receive",
            "docstatus": 1,
            "mode_of_payment": ["!=", "Cash"]
        },
        fields=["name", "party", "party_name", "paid_amount", "posting_date", "mode_of_payment", "company", "reference_no"]
    )

    unreconciled_entries = []
    for entry in payment_entries:
        # Check if there is any Bank Transaction Payments record linked to this Payment Entry
        has_bank_txn = frappe.db.exists("Bank Transaction Payments", {"payment_entry": entry.name})
        if not has_bank_txn:
            unreconciled_entries.append(entry)

    if not unreconciled_entries:
        print("No unreconciled 'Receive' payment entries found (excluding Cash mode of payment and already linked to Bank Transaction Payments).")
        return

    print("Unreconciled 'Receive' Payment Entries (excluding Cash and not linked to Bank Transaction Payments):")
    for entry in unreconciled_entries:
        print(
            f"Name: {entry.name}, Party: {entry.party} ({entry.party_name}), "
            f"Amount: {entry.paid_amount}, Date: {entry.posting_date}, "
            f"Mode: {entry.mode_of_payment}, Company: {entry.company}, Ref: {entry.reference_no}"
        )

# No auto-run on import; call list_unreconciled_received_payments() from bench console