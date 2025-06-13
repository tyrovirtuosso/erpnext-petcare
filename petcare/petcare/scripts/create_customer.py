import frappe
import csv
import os

CSV_FILE_PATH = "/home/frappe-user/frappe-bench/apps/petcare/petcare/petcare/scripts/customers_with_invoices_preprocessed.csv"

def format_phone_number(contact_number, country_code="+91"):
    """
    Formats the phone number correctly by ensuring it has the appropriate country code.
    """
    if not contact_number:
        return None
    
    contact_number = contact_number.strip()

    if contact_number.startswith("+"):
        return contact_number  # Already has a valid country code

    if contact_number.startswith("91"):
        return f"+{contact_number}"  # Convert '91xxx' to '+91xxx'
    
    return f"{country_code}{contact_number}"  # Default case: prepend country code

def ensure_territory_exists(territory_name, parent_territory="Kochi"):
    """
    Checks if a territory exists, and if not, creates it under the specified parent.
    """
    if not territory_name:
        return

    if not frappe.db.exists("Territory", territory_name):
        territory = frappe.get_doc({
            "doctype": "Territory",
            "territory_name": territory_name,
            "parent_territory": parent_territory,
            "is_group": 0
        })
        territory.insert(ignore_permissions=True)
        print(f"Created new territory: {territory_name} under {parent_territory}")
    else:
        print(f"Territory {territory_name} already exists.")

def customer_exists(contact_number):
    """
    Checks if a customer with the given phone number exists.
    """
    if not contact_number:
        return False

    formatted_number = format_phone_number(contact_number)

    existing_customer = frappe.db.sql("""
        SELECT parent FROM `tabContact Phone`
        WHERE phone = %s
    """, (formatted_number,), as_dict=True)

    return existing_customer[0]['parent'] if existing_customer else None

def create_customer(customer_name, contact_number, territory_name, custom_lead_status="Converted", parent_territory="Kochi"):
    """
    Creates a new customer with the given details, links primary contact, and sets lead status.
    """
    if not customer_name:
        print("Skipping entry due to missing customer name.")
        return

    formatted_number = format_phone_number(contact_number)

    # Check if customer exists
    if formatted_number and customer_exists(formatted_number):
        print(f"Customer with phone number {formatted_number} already exists.")
        return

    ensure_territory_exists(territory_name, parent_territory)

    # Create the new customer
    customer = frappe.get_doc({
        "doctype": "Customer",
        "customer_name": customer_name,
        "territory": territory_name or parent_territory,
        "customer_group": "Individual",
        "custom_lead_status": custom_lead_status  # Custom lead status
    })
    customer.insert(ignore_permissions=True)

    if formatted_number:
        # Create a new contact for the customer
        contact = frappe.get_doc({
            "doctype": "Contact",
            "first_name": customer_name,
            "links": [{"link_doctype": "Customer", "link_name": customer.name}],
            "phone_nos": [{"phone": formatted_number}]
        })
        contact.insert(ignore_permissions=True)

        # Update the customer with the primary contact and mobile number
        customer.customer_primary_contact = contact.name
        customer.mobile_no = formatted_number
        customer.save(ignore_permissions=True)

        print(f"Customer '{customer_name}' created with phone number {formatted_number}. Contact '{contact.name}' linked as primary contact.")

def create_customer_if_not_exists(customer_name, contact_number, territory_name, custom_lead_status="Converted", parent_territory="Kochi"):
    """
    Public function to create a customer if they do not exist.
    """
    create_customer(customer_name, contact_number, territory_name, custom_lead_status, parent_territory)

def process_customers_from_csv(file_path=CSV_FILE_PATH, limit=None, custom_lead_status="Converted"):
    """
    Reads customers from a CSV file and adds them if they do not exist.
    """
    if not os.path.exists(file_path):
        print(f"CSV file not found at {file_path}")
        return

    with open(file_path, mode="r", encoding="utf-8") as file:
        reader = csv.DictReader(file)
        count = 0

        for row in reader:
            customer_name = row.get("Customer Name", "").strip()
            contact_number = row.get("Mobile", "").strip()
            territory_name = row.get("Territory", "").strip()

            create_customer(customer_name, contact_number, territory_name, custom_lead_status)

            count += 1
            if limit and count >= limit:
                break

# Example Usage
# create_customer_if_not_exists("Vinodhini", "8220444986", "Athani")
# process_customers_from_csv(limit=10)  # Process first 10 customers from the CSV file


# from petcare.petcare.scripts.create_customer import process_customers_from_csv, create_customer_if_not_exists
