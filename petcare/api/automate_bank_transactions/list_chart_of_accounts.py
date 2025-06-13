import frappe
from typing import List, Dict

def get_chart_of_accounts(company_name: str) -> List[Dict]:
    """
    Returns the chart of accounts for the given company as a list of dicts.
    Each dict contains: name, account_name, account_type, parent_account, is_group, can_be_used_in_entry.
    """
    accounts = frappe.get_all(
        "Account",
        filters={"company": company_name},
        fields=["name", "account_name", "account_type", "parent_account", "is_group"]
    )
    for account in accounts:
        account["can_be_used_in_entry"] = not account["is_group"]
    return accounts

if __name__ == "__main__":
    COMPANY_NAME = "Masterpet Care Private Limited"
    accounts = get_chart_of_accounts(COMPANY_NAME)
    for account in accounts:
        print(account) 
        
'''
bench execute "petcare.api.automate_bank_transactions.list_chart_of_accounts.get_chart_of_accounts" --kwargs "{'company_name': 'Masterpet Care Private Limited'}"
'''