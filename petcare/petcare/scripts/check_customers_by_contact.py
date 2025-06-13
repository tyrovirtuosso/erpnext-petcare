import frappe
import pandas as pd
import os

def check_customers_from_csv(file_path):
    """
    Reads a CSV file containing phone numbers and checks which customers exist in ERPNext.
    
    :param file_path: Path to the CSV file containing customer phone numbers.
    :return: Prints the found customers and numbers not found.
    """

    if not os.path.exists(file_path):
        print(f"Error: File not found at {file_path}")
        return

    # Load the CSV file
    df = pd.read_csv(file_path)

    # Extract phone numbers, dropping NaN values
    if "Mobile" not in df.columns:
        print("Error: 'Mobile' column not found in the CSV file.")
        return

    phone_numbers = df["Mobile"].dropna().astype(str).tolist()

    found_customers = {}
    not_found_numbers = []

    for contact_number in phone_numbers:
        # Normalize phone number variations
        number_variants = set([
            contact_number,              # Original number
            f"+91{contact_number}",      # +91 variant
            f"91{contact_number}",       # 91 variant
            contact_number.lstrip("+91") # Removes +91 if already there
        ])

        # Query to check if a customer with any of these numbers exists
        customers = frappe.db.sql("""
            SELECT parent FROM `tabContact Phone`
            WHERE phone IN ({})
        """.format(",".join(["%s"] * len(number_variants))), tuple(number_variants), as_dict=True)

        if customers:
            found_customers[contact_number] = [c['parent'] for c in customers]
        else:
            not_found_numbers.append(contact_number)

    # Print results
    print("\n=== Customers Found ===")
    for phone, customers in found_customers.items():
        print(f"{phone}: {', '.join(customers)}")

    print("\n=== Numbers Not Found ===")
    if not_found_numbers:
        print("\n".join(not_found_numbers))
    else:
        print("All numbers found.")

# Example usage in bench console
# check_customers_from_csv('/home/frappe-user/frappe-bench/sites/customers_with_invoices.csv')
