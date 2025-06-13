import frappe

def delete_cancelled_sales_invoices_and_payment_entries():
    try:
        # Step 1: Fetch all cancelled Sales Invoices and Payment Entries
        cancelled_sales_invoices = frappe.get_all("Sales Invoice", filters={"docstatus": 2}, pluck="name")
        cancelled_payment_entries = frappe.get_all("Payment Entry", filters={"docstatus": 2}, pluck="name")

        print(f"Cancelled Sales Invoices: {cancelled_sales_invoices}")
        print(f"Cancelled Payment Entries: {cancelled_payment_entries}")

        # Step 2: Handle dependencies - Identify and unlink linked Sales Invoices
        linked_invoices = {}
        for si_name in cancelled_sales_invoices:
            linked_sis = frappe.get_all("Sales Invoice", filters={"return_against": si_name}, pluck="name")
            if linked_sis:
                linked_invoices[si_name] = linked_sis
                for linked_si in linked_sis:
                    frappe.db.set_value("Sales Invoice", linked_si, "return_against", None)
                    print(f"Unlinked Sales Invoice {linked_si} from {si_name}")

        # Step 3: Delete Payment Ledger Entries and GL Entries linked to Payment Entries
        for pe_name in cancelled_payment_entries:
            frappe.db.sql("DELETE FROM `tabPayment Ledger Entry` WHERE voucher_no=%s", (pe_name,))
            frappe.db.sql("DELETE FROM `tabGL Entry` WHERE voucher_no=%s", (pe_name,))
            frappe.delete_doc("Payment Entry", pe_name)
            print(f"Deleted Payment Entry: {pe_name}")

        # Step 4: Delete Payment Ledger Entries and GL Entries linked to Sales Invoices
        for si_name in cancelled_sales_invoices:
            frappe.db.sql("DELETE FROM `tabPayment Ledger Entry` WHERE voucher_no=%s", (si_name,))
            frappe.db.sql("DELETE FROM `tabGL Entry` WHERE voucher_no=%s", (si_name,))

        # Step 5: Delete Linked Sales Invoices First (Child Invoices)
        for parent_si, linked_sis in linked_invoices.items():
            for linked_si in linked_sis:
                frappe.delete_doc("Sales Invoice", linked_si)
                print(f"Deleted linked Sales Invoice: {linked_si}")

        # Step 6: Delete Parent Sales Invoices
        for si_name in cancelled_sales_invoices:
            frappe.delete_doc("Sales Invoice", si_name)
            print(f"Deleted Sales Invoice: {si_name}")

        # Step 7: Commit changes
        frappe.db.commit()
        print("Successfully deleted all cancelled Sales Invoices and Payment Entries.")

    except frappe.LinkExistsError as e:
        frappe.db.rollback()
        print(f"Error: {str(e)}")
    except Exception as e:
        frappe.db.rollback()
        print(f"Unexpected Error: {str(e)}")

# Run the function
delete_cancelled_sales_invoices_and_payment_entries()
