import frappe
from frappe.utils import today
from frappe.model.mapper import get_mapped_doc

@frappe.whitelist()
def make_sales_invoice_from_service_request(service_request_name):
    # Fetch the Service Request document
    service_request_doc = frappe.get_doc("Service Request", service_request_name)

    # Map fields from Service Request to Sales Invoice
    sales_invoice_doc = get_mapped_doc("Service Request", service_request_name, {
        "Service Request": {
            "doctype": "Sales Invoice",
            "field_map": {
                "customer": "customer",
                "customer_name": "customer_name",
                "completed_date": "posting_date",
                "apply_discount_on": "apply_discount_on",
                "discount_amount": "discount_amount"
            },
            "field_no_map": ["source"]  # Ignore if "source" is conflicting
        }
    })

    # If there's no completed_date, default to today's date
    if not sales_invoice_doc.posting_date:
        sales_invoice_doc.posting_date = today()

    # Enable the checkbox so ERPNext respects posting_date and posting_time
    sales_invoice_doc.set_posting_time = 1

    # Set the Posting Time to a fixed value
    sales_invoice_doc.posting_time = "00:00:00"

    # Set Payment Due Date = completed_date (or posting_date)
    sales_invoice_doc.due_date = sales_invoice_doc.posting_date

    # Prevent None-type issues in numeric fields
    sales_invoice_doc.base_grand_total = sales_invoice_doc.base_grand_total or 0.0
    sales_invoice_doc.grand_total = sales_invoice_doc.grand_total or 0.0
    sales_invoice_doc.base_write_off_amount = sales_invoice_doc.base_write_off_amount or 0.0
    sales_invoice_doc.write_off_amount = sales_invoice_doc.write_off_amount or 0.0

    # Ensure child tables are initialized
    sales_invoice_doc.taxes = sales_invoice_doc.taxes or []
    sales_invoice_doc.items = sales_invoice_doc.items or []
    sales_invoice_doc.payments = sales_invoice_doc.payments or []

    # Ensure services table exists
    if service_request_doc.get("services"):
        for service in service_request_doc.get("services"):
            sales_invoice_doc.append("items", {
                "item_code": service.get("item_code"),
                "item_name": service.get("item_name"),
                "qty": service.get("qty") or 1,  # Default to 1 if not set
                "rate": service.get("rate") or 0.0,  # Default to 0 if not set
                "amount": service.get("amount") or 0.0
            })

    # Auto-fill Sales Taxes and Charges based on the items
    sales_invoice_doc.run_method("set_missing_values")
    sales_invoice_doc.run_method("calculate_taxes_and_totals")
    
    # If the Service Request has is_tax_included_in_base_rate checked,
    # then check included_in_print_rate in each Sales Taxes and Charges row
    if service_request_doc.get("is_tax_included_in_base_rate"):
        for tax in sales_invoice_doc.taxes:
            tax.included_in_print_rate = 1
    
    # Insert the new Sales Invoice
    sales_invoice_doc.insert(ignore_permissions=True)
    
    # To set the Sales Invoice status as submitted, call the submit method.
    # To keep it as draft, comment out the submit() line below.
    sales_invoice_doc.submit()
    
    # Link the created Sales Invoice back to the Service Request
    service_request_doc.sales_invoice = sales_invoice_doc.name
    service_request_doc.save(ignore_permissions=True)
    
    frappe.db.commit()

    print(f"Created Sales Invoice: {sales_invoice_doc.name}")



# bench execute petcare.petcare.scripts.create_sales_invoice_from_service_request_test.make_sales_invoice_from_service_request --kwargs "{'service_request_name':'SR-2025-00004'}"
