import frappe

frappe.utils.logger.set_log_level("DEBUG")
logger = frappe.logger("contact_hooks", allow_site=True, file_count=50)

def update_customer_mobile_no(doc, method):
    logger.info(f"Triggering update_customer_mobile_no for Contact: {doc.name}")
    # Check if this contact is a primary contact for any customer
    links = frappe.get_all(
        "Dynamic Link",
        filters={
            "parenttype": "Contact",
            "parent": doc.name,
            "link_doctype": "Customer"
        },
        fields=["link_name"]
    )

    for link in links:
        customer = frappe.get_doc("Customer", link.link_name)
        if customer.customer_primary_contact == doc.name:
            # Update the customer's mobile_no with the contact's mobile number
            frappe.db.set_value("Customer", customer.name, "mobile_no", doc.mobile_no)
            logger.info(
                f"Updated mobile_no for Customer '{customer.name}' to '{doc.mobile_no}'"
            )
            frappe.msgprint(
                f"Updated mobile number for customer '{customer.name}' to '{doc.mobile_no}'"
            )
