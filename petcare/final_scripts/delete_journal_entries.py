import frappe

def delete_linked_entries(doctype, linked_doctype, link_field):
    """
    Deletes all records of a Doctype along with its linked records in another Doctype.

    :param doctype: The main Doctype to delete (e.g., "Journal Entry").
    :param linked_doctype: The related Doctype storing linked records (e.g., "GL Entry").
    :param link_field: The field in the linked Doctype that references the main Doctype (e.g., "voucher_no").
    """
    entries = frappe.get_all(doctype, pluck="name")

    if not entries:
        print(f"No {doctype} records found to delete.")
        return

    for entry in entries:
        try:
            # Delete linked records
            frappe.db.sql(f"DELETE FROM `tab{linked_doctype}` WHERE {link_field}=%s", entry)
            
            # Delete main entry
            frappe.delete_doc(doctype, entry, force=True)
            print(f"Deleted {doctype}: {entry}")
        except Exception as e:
            print(f"Error deleting {entry}: {e}")

    frappe.db.commit()
    print(f"All {doctype} records and their linked {linked_doctype} entries have been deleted.")

# Example Usage
delete_linked_entries("Journal Entry", "GL Entry", "voucher_no")
