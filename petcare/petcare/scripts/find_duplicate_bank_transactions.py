import frappe
from typing import List, Dict

def find_duplicate_bank_transactions() -> None:
    """
    Finds and prints all Bank Transaction records with duplicate reference_number,
    grouped by reference_number.
    """
    # Step 1: Find all reference_numbers that appear more than once
    duplicate_refs = frappe.db.sql(
        """
        SELECT reference_number
        FROM `tabBank Transaction`
        WHERE reference_number IS NOT NULL AND reference_number != ''
        GROUP BY reference_number
        HAVING COUNT(*) > 1
        """,
        as_dict=True
    )

    if not duplicate_refs:
        print("No duplicate reference_number found in Bank Transaction.")
        return

    print(f"Found {len(duplicate_refs)} duplicate reference_number(s):\n")

    # Step 2: For each duplicate reference_number, fetch and print all transactions
    for ref in duplicate_refs:
        ref_number = ref['reference_number']
        transactions = frappe.get_all(
            "Bank Transaction",
            filters={"reference_number": ref_number},
            fields=[
                "name",
                "date",
                "bank_account",
                "deposit",
                "withdrawal",
                "reference_number",
                "transaction_id",
                "transaction_type",
                "status",
                "docstatus"
            ]
        )
        print(f"Reference Number: {ref_number}")
        for txn in transactions:
            print(
                f"  Name: {txn['name']}, Date: {txn['date']}, Bank Account: {txn['bank_account']}, "
                f"Deposit: {txn['deposit']}, Withdrawal: {txn['withdrawal']}, "
                f"Transaction ID: {txn['transaction_id']}, Type: {txn['transaction_type']}, "
                f"Status: {txn['status']}, DocStatus: {txn['docstatus']}"
            )
        print("-") 