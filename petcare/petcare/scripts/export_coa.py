import csv
import frappe

def export_chart_of_accounts(file_name='chart_of_accounts.csv'):
    """
    Export Chart of Accounts to a CSV file
    """
    accounts = frappe.get_all(
        'Account',
        fields=['name', 'account_name', 'parent_account', 'company', 'is_group', 'account_type']
    )
    with open(file_name, mode='w', newline='', encoding='utf-8') as file:
        writer = csv.DictWriter(file, fieldnames=accounts[0].keys())
        writer.writeheader()
        writer.writerows(accounts)
    print(f"Exported to {file_name}")
