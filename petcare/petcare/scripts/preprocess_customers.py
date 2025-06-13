import frappe
import pandas as pd

def check_existing_customers():
    file_path = "/home/frappe-user/frappe-bench/apps/petcare/petcare/petcare/scripts/customers_with_invoices_preprocessed.csv"
    
    # Load the CSV file
    df = pd.read_csv(file_path)

    existing_customers = []
    new_customers = []

    for _, row in df.iterrows():
        customer_name = row["Customer Name"]
        mobile = row["Mobile"]

        if not mobile or pd.isna(mobile):  # Skip if mobile is empty
            continue

        # Check if the mobile number exists in any contact linked to a customer
        existing_contact = frappe.db.sql("""
            SELECT c.name 
            FROM `tabContact` c
            WHERE c.mobile_no = %s
        """, (mobile,), as_dict=True)

        if existing_contact:
            contact_name = existing_contact[0]["name"]
            
            # Find linked customer from `tabDynamic Link`
            linked_customer = frappe.db.sql("""
                SELECT dl.link_name 
                FROM `tabDynamic Link` dl
                WHERE dl.link_doctype = 'Customer' AND dl.parent = %s
            """, (contact_name,), as_dict=True)

            if linked_customer:
                existing_customers.append({"Customer Name": customer_name, "Mobile": mobile, "Linked Customer": linked_customer[0]["link_name"]})
            else:
                new_customers.append({"Customer Name": customer_name, "Mobile": mobile})

        else:
            new_customers.append({"Customer Name": customer_name, "Mobile": mobile})

    # Display results
    print("\nExisting Customers:")
    for customer in existing_customers:
        print(f"{customer['Customer Name']} - {customer['Mobile']} (Linked to {customer['Linked Customer']})")

    print("\nNew Customers (Not Found in System):")
    for customer in new_customers:
        print(f"{customer['Customer Name']} - {customer['Mobile']}")

    return {"existing_customers": existing_customers, "new_customers": new_customers}


def create_missing_customers():
    file_path = "/home/frappe-user/frappe-bench/apps/petcare/petcare/petcare/scripts/customers_with_invoices_preprocessed.csv"
    
    # Load the CSV file
    df = pd.read_csv(file_path, dtype={"Mobile": str})  # Ensure Mobile column is read as string

    for _, row in df.iterrows():
        customer_name = row["Customer Name"]
        territory = row["Territory"]
        mobile = row["Mobile"]

        if not mobile or pd.isna(mobile):  # Skip if mobile is empty
            continue

        # Ensure mobile is a string to avoid AttributeError
        mobile = str(mobile).strip()

        # Check if the mobile number exists in any contact linked to a customer
        existing_contact = frappe.db.sql("""
            SELECT c.name 
            FROM `tabContact` c
            WHERE c.name IN (
                SELECT dl.parent FROM `tabDynamic Link` dl WHERE dl.link_doctype = 'Customer'
            ) AND c.name IN (
                SELECT p.parent FROM `tabContact Phone` p WHERE p.phone = %s
            )
        """, (mobile,), as_dict=True)

        if existing_contact:
            frappe.logger().info(f"Customer with mobile {mobile} already exists. Skipping.")
            continue  # Skip if customer already exists

        # Check if the territory exists, if not create it under "Kochi"
        territory_exists = frappe.db.exists("Territory", territory)
        if not territory_exists:
            new_territory = frappe.get_doc({
                "doctype": "Territory",
                "territory_name": territory,
                "parent_territory": "Kochi",
                "is_group": 0
            })
            new_territory.insert(ignore_permissions=True)
            frappe.logger().info(f"Created new territory: {territory}")

        # Create a new customer
        customer = frappe.get_doc({
            "doctype": "Customer",
            "customer_name": customer_name,
            "territory": territory,
            "customer_type": "Individual",
        })
        customer.insert(ignore_permissions=True)

        # Create a new contact and link it to the customer
        contact = frappe.get_doc({
            "doctype": "Contact",
            "first_name": customer_name,
            "links": [{"link_doctype": "Customer", "link_name": customer.name}],
            "phone_nos": [
                {
                    "phone": mobile,
                    "is_primary_phone": 1,  # Mark first number as primary
                    "is_primary_mobile_no": 1
                }
            ]
        })
        contact.insert(ignore_permissions=True)

        frappe.db.commit()

        print(f"Created new Customer: {customer.name} with mobile {mobile} in territory {territory}.")
        return f"Break: Stopped after creating {customer.name} for verification."

    return "No new customers needed."