import frappe

def create_accounts():
    accounts = [
        {
            "account_name": "Equity - Investment by Directors",
            "parent_account": "Equity - MP",
            "company": "Masterpet Care Private Limited",
            "account_type": "Equity",
            "is_group": 1
        },
        {
            "account_name": "Loan from Directors",
            "parent_account": "Loans (Liabilities) - MP",
            "company": "Masterpet Care Private Limited",
            "account_type": "Liability",
            "is_group": 1
        },
        {
            "account_name": "Professional Fees",
            "parent_account": "Indirect Expenses - MP",
            "company": "Masterpet Care Private Limited",
            "account_type": "Indirect Expense",
            "is_group": 1
        },
        {
            "account_name": "Intangible Assets",
            "parent_account": "Application of Funds (Assets) - MP",
            "company": "Masterpet Care Private Limited",
            "is_group": 1
        },
        {
            "account_name": "Grooming Truck Expense",
            "parent_account": "Indirect Expenses - MP",
            "company": "Masterpet Care Private Limited",
            "is_group": 1
        },
        
        ############################################################
        ############ Investment by Directors ####################
        ############################################################    
        {
            "account_name": "Investment - PRITHVIRAJ RAJESH GOPAL",
            "parent_account": "Equity - Investment by Directors - MP",
            "company": "Masterpet Care Private Limited",
            "account_type": "Equity",
            "is_group": 0
        },
        {
            "account_name": "Investment - SHANE JAMES",
            "parent_account": "Equity - Investment by Directors - MP",
            "company": "Masterpet Care Private Limited",
            "account_type": "Equity",
            "is_group": 0
        },
        {
            "account_name": "Investment - CARRON PHIL JOJU",
            "parent_account": "Equity - Investment by Directors - MP",
            "company": "Masterpet Care Private Limited",
            "account_type": "Equity",
            "is_group": 0
        },
        {
            "account_name": "Investment - AKASH MANUJI",
            "parent_account": "Equity - Investment by Directors - MP",
            "company": "Masterpet Care Private Limited",
            "account_type": "Equity",
            "is_group": 0
        },
        {
            "account_name": "Investment - SEBASTIAN KOIKKARA",
            "parent_account": "Equity - Investment by Directors - MP",
            "company": "Masterpet Care Private Limited",
            "account_type": "Equity",
            "is_group": 0
        },
        
        ############################################################
        ############ Loan from Directors ##########################
        ############################################################
        {
            "account_name": "Loan from Director - SEBASTIAN KOIKKARA",
            "parent_account": "Loan from Directors - MP",
            "company": "Masterpet Care Private Limited",
            "account_type": "Liability",
            "is_group": 0
        },
        {
            "account_name": "Loan from Director - AKASH MANUJI",
            "parent_account": "Loan from Directors - MP",
            "company": "Masterpet Care Private Limited",
            "account_type": "Liability",
            "is_group": 0
        },
        {
            "account_name": "Loan from Director - CARRON PHIL JOJU",
            "parent_account": "Loan from Directors - MP",
            "company": "Masterpet Care Private Limited",
            "account_type": "Liability",
            "is_group": 0
        },
        {
            "account_name": "Loan from Director - SHANE JAMES",
            "parent_account": "Loan from Directors - MP",
            "company": "Masterpet Care Private Limited",
            "account_type": "Liability",
            "is_group": 0
        },
        {
            "account_name": "Loan from Director - PRITHVIRAJ RAJESH GOPAL",
            "parent_account": "Loan from Directors - MP",
            "company": "Masterpet Care Private Limited",
            "account_type": "Liability",
            "is_group": 0
        },
        
        ############################################################
        ############ Professional Fees ############################
        ############################################################
        {
            "account_name": "Architect Consulting Fees",
            "parent_account": "Professional Fees - MP",
            "company": "Masterpet Care Private Limited",
            "is_group": 0  
        },
        {
            "account_name": "Consulting Fees",
            "parent_account": "Professional Fees - MP",
            "company": "Masterpet Care Private Limited",
            "is_group": 0 
        },
        
        ############################################################
        ############ Intangible Assets ###########################
        ############################################################
        {
            "account_name": "Mobile App WIP",
            "parent_account": "Intangible Assets - MP",
            "company": "Masterpet Care Private Limited",
            "is_group": 0
        },
        {
            "account_name": "Mobile App (Completed)",
            "parent_account": "Intangible Assets - MP",
            "company": "Masterpet Care Private Limited",
            "is_group": 0
        },
        {
            "account_name": "Branding WIP",
            "parent_account": "Intangible Assets - MP",
            "company": "Masterpet Care Private Limited",
            "is_group": 0
        },
        {
            "account_name": "Branding (Completed)",
            "parent_account": "Intangible Assets - MP",
            "company": "Masterpet Care Private Limited",
            "is_group": 0
        },
        
        ############################################################
        ############ Grooming Truck Expense #####################
        ############################################################
        {
            "account_name": "Grooming Truck Petrol Expense",
            "parent_account": "Grooming Truck Expense - MP",
            "company": "Masterpet Care Private Limited",
            "is_group": 0
        },
        
        ############################################################
        ############ Indirect Expenses - MP #####################
        ############################################################
        
        {
            "account_name": "Groomer Consultant - Food Expense",
            "parent_account": "Indirect Expenses - MP",
            "company": "Masterpet Care Private Limited",
            "is_group": 0
        },
        {
            "account_name": "Groomer Consultant - Travel/Conveyance Expense",
            "parent_account": "Indirect Expenses - MP",
            "company": "Masterpet Care Private Limited",
            "is_group": 0
        },
        {
            "account_name": "Groomer Consultant - Accommodation Expense",
            "parent_account": "Indirect Expenses - MP",
            "company": "Masterpet Care Private Limited",
            "is_group": 0
        },
        {
            "account_name": "Preliminary Expense",
            "parent_account": "Indirect Expenses - MP",
            "company": "Masterpet Care Private Limited",
            "is_group": 0
        },
        {
            "account_name": "Bank Charges",
            "parent_account": "Indirect Expenses - MP",
            "company": "Masterpet Care Private Limited",
            "is_group": 0
        },
        {
            "account_name": "Meeting Expense",
            "parent_account": "Indirect Expenses - MP",
            "company": "Masterpet Care Private Limited",
            "is_group": 0
        },
        {
            "account_name": "Hiring Expense",
            "parent_account": "Indirect Expenses - MP",
            "company": "Masterpet Care Private Limited",
            "is_group": 0
        },
        {
            "account_name": "IT Expense",
            "parent_account": "Indirect Expenses - MP",
            "company": "Masterpet Care Private Limited",
            "is_group": 0
        },
        {
            "account_name": "Sim Recharge Expense",
            "parent_account": "Indirect Expenses - MP",
            "company": "Masterpet Care Private Limited",
            "is_group": 0
        },
        {
            "account_name": "Staff Expense",
            "parent_account": "Indirect Expenses - MP",
            "company": "Masterpet Care Private Limited",
            "is_group": 0
        },
        {
            "account_name": "Loan Interest Expense",
            "parent_account": "Indirect Expenses - MP",
            "company": "Masterpet Care Private Limited",
            "is_group": 0
        },
        {
            "account_name": "Commission on Sales Revenue",
            "parent_account": "Indirect Expenses - MP",
            "company": "Masterpet Care Private Limited",
            "is_group": 0
        },
        
        ############################################################
        ############ Loans and Advances (Assets) - MP #####################
        ############################################################
        
        {
            "account_name": "Advance against Vehicle",
            "parent_account": "Loans and Advances (Assets) - MP",
            "company": "Masterpet Care Private Limited",
            "account_type": "Current Asset",
            "is_group": 0
        },
        {
            "account_name": "Vendor Advances",
            "parent_account": "Loans and Advances (Assets) - MP",
            "company": "Masterpet Care Private Limited",
            "is_group": 0
        },
        {
            "account_name": "Advance Rent",
            "parent_account": "Loans and Advances (Assets) - MP",
            "company": "Masterpet Care Private Limited",
            "is_group": 0
        },
        
        ############################################################
        ############ Securities and Deposits - MP #####################
        ############################################################
        
        {
            "account_name": "Rent Security Deposits",
            "parent_account": "Securities and Deposits - MP",
            "company": "Masterpet Care Private Limited",
            "is_group": 0
        },
        
        ############################################################
        ############ Fixed Assets - MP #####################
        ############################################################
        
        {
            "account_name": "Vehicles",
            "parent_account": "Fixed Assets - MP",
            "company": "Masterpet Care Private Limited",
            "is_group": 0
        },
        {
            "account_name": "Equipment - Grooming Truck",
            "parent_account": "Fixed Assets - MP",
            "company": "Masterpet Care Private Limited",
            "is_group": 0
        },
        
        ############################################################
        ############ Grooming Truck Expense - MP #####################
        ############################################################
        
        {
            "account_name": "Grooming Truck Road Tax Expense",
            "parent_account": "Grooming Truck Expense - MP",
            "company": "Masterpet Care Private Limited",
            "is_group": 0
        },
        {
            "account_name": "Other Expenses - Mobile Grooming",
            "parent_account": "Grooming Truck Expense - MP",
            "company": "Masterpet Care Private Limited",
            "is_group": 0
        },
        {
            "account_name": "Maintenance - Mobile Truck",
            "parent_account": "Grooming Truck Expense - MP",
            "company": "Masterpet Care Private Limited",
            "is_group": 0
        },
        
        ############################################################
        ############ Direct Expenses - MP #####################
        ############################################################
            
        {
            "account_name": "Sales Refunds",
            "parent_account": "Direct Expenses - MP",
            "company": "Masterpet Care Private Limited",
            "is_group": 0
        },
        {
            "account_name": "Pet Grooming Consumables",
            "parent_account": "Direct Expenses - MP",
            "company": "Masterpet Care Private Limited",
            "is_group": 0
        },
        {
            "account_name": "Pet Grooming Tools",
            "parent_account": "Direct Expenses - MP",
            "company": "Masterpet Care Private Limited",
            "is_group": 0
        },
        {
            "account_name": "Fuel Expense - Mobile Truck",
            "parent_account": "Direct Expenses - MP",
            "company": "Masterpet Care Private Limited",
            "is_group": 0
        },
        
        ############################################################
        ############ Direct Income - MP #####################
        ############################################################
        
        {
            "account_name": "Sales Revenue",
            "parent_account": "Direct Income - MP",
            "company": "Masterpet Care Private Limited",
            "is_group": 0
        }
    ]

    for account in accounts:
        if not frappe.db.exists("Account", {"account_name": account["account_name"], "company": account["company"]}):
            new_account = frappe.get_doc({
                "doctype": "Account",
                "account_name": account["account_name"],
                "parent_account": account["parent_account"],
                "company": account["company"],
                "account_type": account.get("account_type"),
                "is_group": account["is_group"]
            })
            new_account.insert(ignore_permissions=True)
            frappe.db.commit()
            print(f"Created account: {account['account_name']}")

if __name__ == "__main__":
    create_accounts()


'''
from petcare.petcare.scripts.add_missing_accounts import create_accounts
create_accounts()
'''