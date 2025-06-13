chart_of_accounts = frappe.get_all(
    "Account", 
    filters={"company": "Masterpet Care Private Limited"}, 
    fields=["name", "account_name", "account_type", "parent_account"]
)
for account in chart_of_accounts:
    print(account)
