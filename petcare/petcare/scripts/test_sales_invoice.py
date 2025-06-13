import frappe
from frappe.utils import getdate, add_days


import frappe
from frappe.utils import getdate, add_days

def create_sales_invoice_with_posting_date(
    customer_id, 
    items, 
    tax_template, 
    custom_posting_date,
    cost_center="Main - MP",
    apply_discount_on=None,
    additional_discount_percentage=None,
    discount_amount=None,
    include_tax_in_rate=True
):
    # Validate discount parameters
    if additional_discount_percentage is not None and discount_amount is not None:
        frappe.throw("Cannot specify both additional_discount_percentage and discount_amount")

    # Parse the custom posting date
    posting_date = getdate(custom_posting_date)
    due_date = add_days(posting_date, 1)
    
    # Validate dates
    if due_date < posting_date:
        frappe.throw("Due Date cannot be before Posting Date")

    # Create new Sales Invoice
    sales_invoice = frappe.new_doc("Sales Invoice")
    sales_invoice.customer = customer_id
    sales_invoice.posting_date = posting_date
    sales_invoice.due_date = due_date
    sales_invoice.taxes_and_charges = tax_template
    sales_invoice.set_posting_time = 1
    sales_invoice.cost_center = cost_center

    # Add items
    for item in items:
        sales_invoice.append("items", {
            "item_code": item["item_code"],
            "qty": item["qty"],
            "rate": item["rate"],
            "amount": item["qty"] * item["rate"],
            "cost_center": cost_center
        })

    # Set taxes and modify tax inclusions
    sales_invoice.set_taxes()
    
    if include_tax_in_rate:
        for tax in sales_invoice.taxes:
            tax.included_in_print_rate = 1

    # Set discount configuration
    if apply_discount_on:
        sales_invoice.apply_discount_on = apply_discount_on
        
    if additional_discount_percentage is not None:
        sales_invoice.additional_discount_percentage = additional_discount_percentage
        
    if discount_amount is not None:
        sales_invoice.discount_amount = discount_amount

    # Save and submit
    sales_invoice.insert()
    sales_invoice.submit()
    frappe.db.commit()

    return sales_invoice.name

# Test function
def test_create_sales_invoice():
    # Test data
    customer_id = "CUST-2025-00002"
    items = [
        {"item_code": "AT_HOME_MG_PACK", "qty": 1, "rate": 1399},
        {"item_code": "TRAVEL_EXP", "qty": 1, "rate": 100},
    ]
    tax_template = "Output GST In-state - MP"
    custom_posting_date = "2025-01-10"

    # Valid example with percentage discount
    invoice_name = create_sales_invoice_with_posting_date(
        customer_id=customer_id,
        items=items,
        tax_template=tax_template,
        custom_posting_date=custom_posting_date,
        cost_center="Main - MP",
        apply_discount_on="Grand Total",
        additional_discount_percentage=10,
        include_tax_in_rate=True
    )
    
    print(f"Created Sales Invoice: {invoice_name}")
    
    # Valid example with amount discount
    invoice_name = create_sales_invoice_with_posting_date(
        customer_id=customer_id,
        items=items,
        tax_template=tax_template,
        custom_posting_date=custom_posting_date,
        cost_center="Main - MP",
        apply_discount_on="Net Total",
        discount_amount=150
    )
    
    print(f"Created Sales Invoice: {invoice_name}")
    
    # This will throw error:
    invoice_name = create_sales_invoice_with_posting_date(
        customer_id=customer_id,
        items=items,
        tax_template=tax_template,
        custom_posting_date=custom_posting_date,
        cost_center="Main - MP",
        additional_discount_percentage=10,
        discount_amount=150
    )
    
    print(f"Created Sales Invoice: {invoice_name}")

if __name__ == "__main__":
    test_create_sales_invoice()
    

# Function to create Payment Entry (unchanged)
def create_payment_entry(sales_invoice_name, amount, mode_of_payment, posting_date):
    # Fetch Sales Invoice
    sales_invoice = frappe.get_doc("Sales Invoice", sales_invoice_name)

    # Create Payment Entry
    payment_entry = frappe.new_doc("Payment Entry")
    payment_entry.payment_type = "Receive"
    payment_entry.party_type = "Customer"
    payment_entry.party = sales_invoice.customer
    payment_entry.posting_date = posting_date
    payment_entry.paid_amount = amount
    payment_entry.received_amount = amount
    payment_entry.mode_of_payment = mode_of_payment

    # Set default accounts
    payment_entry.paid_to = frappe.db.get_value(
        "Mode of Payment Account",
        {"parent": mode_of_payment, "company": sales_invoice.company},
        "default_account",
    )
    payment_entry.paid_from_account_currency = "INR"
    payment_entry.paid_to_account_currency = "INR"
    payment_entry.source_exchange_rate = 1  # For single-currency scenarios
    payment_entry.target_exchange_rate = 1  # For single-currency scenarios

    # Set Reference No and Reference Date for UPI (treated as Bank Transaction)
    payment_entry.reference_no = f"UPI-{frappe.generate_hash('', 5)}"
    payment_entry.reference_date = posting_date

    # Link to the Sales Invoice
    payment_entry.append(
        "references",
        {
            "reference_doctype": "Sales Invoice",
            "reference_name": sales_invoice_name,
            "allocated_amount": amount,
        },
    )

    # Save and submit the Payment Entry
    payment_entry.insert()
    payment_entry.submit()
    
    
    # Commit the transaction
    frappe.db.commit()

    print(f"Payment Entry {payment_entry.name} created successfully")
    return payment_entry.name

'''
from petcare.petcare.scripts.test_sales_invoice import create_sales_invoice, create_payment_entry

customer_id = "CUST-2025-00002"
items = [
    {"item_code": "AT_HOME_MG_PACK", "qty": 1, "rate": 1399},
    {"item_code": "TRAVEL_EXP", "qty": 1, "rate": 100},
]
tax_template = "Output GST In-state - MP"
posting_date = today()

print("Case 1: Percentage Discount")
invoice_name = create_sales_invoice(
    customer_id, items, tax_template, posting_date, discount_type="percentage", discount_value=10
)
print(f"Created Invoice: {invoice_name}")

'''


