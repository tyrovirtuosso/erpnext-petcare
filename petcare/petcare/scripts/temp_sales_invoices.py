import frappe

batch_size = 10  # Number of records per batch
start = 0  # Start index

while True:
    # Fetch the latest Sales Invoices first, paginated in batches of 10
    sales_invoices = frappe.get_all(
        "Sales Invoice",
        filters={"docstatus": 1},  # Only Submitted invoices
        fields=["name", "customer", "customer_name", "customer_address", "grand_total", 
                "outstanding_amount", "discount_amount", "taxes_and_charges", "posting_date"],
        limit_start=start,
        limit_page_length=batch_size,
        order_by="creation ASC"  # Fetch the latest invoices first
    )

    if not sales_invoices:
        print("No more records to show.")
        break  # Stop when there are no more invoices

    for invoice in sales_invoices:
        print("=" * 80)
        print(f"Sales Invoice: {invoice['name']}")
        print(f"Posting Date: {invoice['posting_date']}")
        print(f"Customer: {invoice['customer_name']} (ID: {invoice['customer']})")
        print(f"Customer Address: {invoice['customer_address']}")
        print(f"Grand Total: {invoice['grand_total']}, Outstanding: {invoice['outstanding_amount']}")
        print(f"Discount: {invoice['discount_amount']}")
        print(f"Taxes & Charges: {invoice['taxes_and_charges']}")
        
        # Fetch Customer Territory
        customer_details = frappe.get_value("Customer", invoice["customer"], ["territory"])

        if customer_details:
            print(f"Customer Territory: {customer_details}")
        else:
            print("Territory not found for this customer.")

        # Fetch Customer Contact Information
        contact_info = frappe.get_all(
            "Contact",
            filters={"link_name": invoice["customer"]},
            fields=["first_name", "last_name", "email_id", "phone", "mobile_no"]
        )

        if contact_info:
            for contact in contact_info:
                print(f"Customer Contact: {contact['first_name']} {contact['last_name']}")
                print(f"Email: {contact['email_id']}, Phone: {contact['phone']}, Mobile: {contact['mobile_no']}")
        else:
            print("No contact information found for this customer.")

        # Fetch Sales Invoice Items
        invoice_items = frappe.get_all(
            "Sales Invoice Item",
            filters={"parent": invoice["name"]},
            fields=["item_code", "item_name", "qty", "rate", "amount", "discount_percentage", "net_amount"]
        )

        print("\nItems:")
        for item in invoice_items:
            print(f"  - {item['item_code']} ({item['item_name']}) | Qty: {item['qty']}, Rate: {item['rate']}, Amount: {item['amount']}")
            print(f"    Discount: {item['discount_percentage']}%, Net Amount: {item['net_amount']}")

        # Fetch Payment Entries linked to this Sales Invoice
        payment_entries = frappe.get_all(
            "Payment Entry Reference",
            filters={"reference_name": invoice["name"], "reference_doctype": "Sales Invoice"},
            fields=["parent"]
        )

        if payment_entries:
            print("\nPayment Entries:")
            for pe in payment_entries:
                payment_entry = frappe.get_doc("Payment Entry", pe["parent"])
                print(f"  Payment Entry: {payment_entry.name}, Mode: {payment_entry.mode_of_payment}, Amount: {payment_entry.paid_amount}")

                # Fetch Account details from the Payment Entry
                if hasattr(payment_entry, "accounts") and payment_entry.accounts:
                    for pe_account in payment_entry.accounts:
                        print(f"    Account: {pe_account.account}, Amount: {pe_account.debit if pe_account.debit else pe_account.credit}")
                else:
                    print("    No account details found in Payment Entry.")
        else:
            print("No Payment Entries found for this invoice.")

        print("=" * 80)

    # Ask user if they want to fetch the next batch
    user_input = input("Press Enter to load the next batch (or type 'exit' to stop): ")
    if user_input.lower() == "exit":
        break

    start += batch_size  # Move to the next batch
