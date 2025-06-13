import csv
import frappe
from frappe.utils import getdate
from collections import defaultdict

def import_journal_entries():
    # Path to the CSV file
    csv_file_path = '/home/frappe-user/frappe-bench/apps/petcare/petcare/petcare/scripts/journal_entries_to_add.csv'

    # Specify the date range
    start_date = getdate("2024-01-01")
    end_date = getdate("2025-03-01")

    # Set filter for Journal Entry: only process entries with an ID <= this value.
    till_journal_entry = ""

    journal_entries = defaultdict(list)

    # Read the CSV and group entries by 'Journal Entry' ID
    with open(csv_file_path, 'r') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            posting_date = getdate(row['Posting Date'])
            # Filter by date range
            if start_date <= posting_date <= end_date:
                # If a till_journal_entry filter is set, only process rows with an ID <= that value
                if till_journal_entry and row['Journal Entry'] > till_journal_entry:
                    continue
                journal_entries[row['Journal Entry']].append(row)

    # Process each grouped Journal Entry
    for je_name, rows in journal_entries.items():
        first_row = rows[0]  # Get the first row for general details

        print("--------------------------------")
        print(f"Processing Journal Entry: {je_name}")
        print(rows)
        print("--------------------------------")

        # Construct account set for duplicate check
        account_set = set((row['Account'], float(row['Debit']), float(row['Credit'])) for row in rows)

        # Check if a Journal Entry with the same details exists
        existing_journal_entries = frappe.get_all(
            "Journal Entry",
            filters={
                "posting_date": getdate(first_row['Posting Date']),
                "company": first_row['Company'],
                "cheque_no": first_row.get('Reference Number (Cheque No)', None),
                "cheque_date": getdate(first_row.get('Reference Date (Cheque Date)', None)) if first_row.get('Reference Date (Cheque Date)') else None
            },
            fields=["name"]
        )

        duplicate_found = False
        for existing_je in existing_journal_entries:
            existing_je_doc = frappe.get_doc("Journal Entry", existing_je["name"])
            existing_account_set = set(
                (acc.account, acc.debit_in_account_currency, acc.credit_in_account_currency)
                for acc in existing_je_doc.accounts
            )

            # If accounts match exactly, flag as duplicate
            if account_set == existing_account_set:
                print(f"Skipping Journal Entry {je_name}: Duplicate entry already exists with name {existing_je['name']}")
                duplicate_found = True
                break

        if duplicate_found:
            continue

        # Create a new Journal Entry (Name will be auto-generated)
        je = frappe.new_doc("Journal Entry")
        je.posting_date = getdate(first_row['Posting Date'])
        je.voucher_type = first_row['Voucher Type']
        je.company = first_row['Company']
        je.user_remark = first_row.get('User Remark', '')

        # Assign cheque_no and cheque_date from first row
        je.cheque_no = first_row.get('Reference Number (Cheque No)', None)
        je.cheque_date = getdate(first_row.get('Reference Date (Cheque Date)', None)) if first_row.get('Reference Date (Cheque Date)') else None

        # Add multiple accounts for the Journal Entry
        allowed_party_types = ["Customer", "Employee", "Shareholder", "Supplier"]
        row_validation_error = False  # Flag to indicate a validation error in any row

        for row in rows:
            debit = float(row['Debit']) if row['Debit'] else 0
            credit = float(row['Credit']) if row['Credit'] else 0

            # Validate that the Account exists in ERPNext
            if not frappe.db.exists("Account", row['Account']):
                print(f"Account '{row['Account']}' does not exist for Journal Entry {je_name}. Skipping entry.")
                row_validation_error = True
                break

            # Retrieve party details from CSV row
            party_type = row.get('Party Type', None)
            party = row.get('Party', None)

            # Validate party_type and party if party_type is provided
            if party_type:
                if party_type not in allowed_party_types:
                    print(f"Invalid Party Type '{party_type}' for Journal Entry {je_name}. Skipping entry.")
                    row_validation_error = True
                    break
                if not party:
                    print(f"Party must be provided when Party Type '{party_type}' is specified for Journal Entry {je_name}. Skipping entry.")
                    row_validation_error = True
                    break
                if not frappe.db.exists(party_type, party):
                    print(f"The {party_type} '{party}' does not exist for Journal Entry {je_name}. Skipping entry.")
                    row_validation_error = True
                    break

            je.append("accounts", {
                "account": row['Account'],
                "party_type": party_type,
                "party": party,
                "debit_in_account_currency": debit,
                "credit_in_account_currency": credit
            })

        # If any row validation error occurred, skip this Journal Entry
        if row_validation_error:
            continue

        # Validate total debit and credit
        total_debit = sum(float(row['Debit']) if row['Debit'] else 0 for row in rows)
        total_credit = sum(float(row['Credit']) if row['Credit'] else 0 for row in rows)
        if total_debit != total_credit:
            print(f"Skipping Journal Entry {je_name}: Total Debit ({total_debit}) does not match Total Credit ({total_credit})")
            continue

        # Save and submit the Journal Entry
        try:
            je.insert()
            frappe.db.commit()  # Force commit to database
            je.submit()
            frappe.db.commit()
            print(f"Journal Entry {je.name} created successfully!")

            # Fetch and display the newly created Journal Entry
            created_je = frappe.get_doc("Journal Entry", je.name)
            print("\nFetched Journal Entry Details:")
            print(f"Name: {created_je.name}")
            print(f"Posting Date: {created_je.posting_date}")
            print(f"Voucher Type: {created_je.voucher_type}")
            print(f"Company: {created_je.company}")
            print(f"User Remark: {created_je.user_remark}")
            print(f"Cheque No: {created_je.cheque_no}")
            print(f"Cheque Date: {created_je.cheque_date}")
            print("\nAccounts Entries:")
            for acc in created_je.accounts:
                print(f"- Account: {acc.account}, Debit: {acc.debit_in_account_currency}, Credit: {acc.credit_in_account_currency}")

        except Exception as e:
            print(f"Error creating Journal Entry: {e}")
