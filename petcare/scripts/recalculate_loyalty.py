import frappe
from petcare.scripts.loyalty import update_loyalty_totals

@frappe.whitelist()
def recalculate_loyalty_for_customer(customer_id):
    """
    Recalculates loyalty points for all completed Service Requests of a specific customer
    and updates their total loyalty balance.
    """

    print(f"🔄 Recalculating loyalty points for Customer: {customer_id}")

    # Fetch all completed service requests for the customer
    service_requests = frappe.get_all(
        "Service Request",
        filters={"customer": customer_id, "status": "completed"},
        fields=["name"],
        order_by="completed_date asc"
    )

    if not service_requests:
        print(f"⚠️ No completed service requests found for Customer {customer_id}")
        return

    # Process each Service Request in order
    for sr in service_requests:
        print(f"🔹 Processing Service Request: {sr['name']}")
        sr_doc = frappe.get_doc("Service Request", sr["name"])

        # Run the update_loyalty_totals function on each service request
        update_loyalty_totals(sr_doc, "validate")

        # ✅ Instead of .save(), use db_update() to avoid TimestampMismatchError
        sr_doc.db_update()

    # ✅ Commit all changes to ensure they are saved
    frappe.db.commit()

    print(f"✅ Loyalty recalculation completed for Customer: {customer_id}")

@frappe.whitelist()
def recalculate_loyalty_for_all_customers():
    """
    Runs `recalculate_loyalty_for_customer` for all customers who have at least one completed service request.
    """

    print("🔄 Starting loyalty recalculation for all customers...")

    # Fetch distinct customer IDs who have at least one completed service request
    customers = frappe.get_all(
        "Service Request",
        filters={"status": "completed"},
        fields=["distinct customer"]
    )

    if not customers:
        print("⚠️ No customers found with completed service requests.")
        return

    for customer in customers:
        recalculate_loyalty_for_customer(customer["customer"])

    print("✅ Loyalty recalculation completed for all customers.")
