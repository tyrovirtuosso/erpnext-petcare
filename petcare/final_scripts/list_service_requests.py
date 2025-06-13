import frappe

def list_service_requests_and_total(customer_id):
    # Fetch all Service Request records for the given customer
    service_requests = frappe.get_all(
        "Service Request",
        filters={"customer": customer_id},
        fields=["name", "amount_after_discount"]
    )

    if not service_requests:
        print(f"No service requests found for customer {customer_id}")
        return

    total_amount_after_discount = 0

    for sr in service_requests:
        # Get full document to access child table "services"
        sr_doc = frappe.get_doc("Service Request", sr.name)
        print(f"Service Request: {sr_doc.name}")
        print(f"  Amount After Discount: {sr_doc.amount_after_discount}")
        total_amount_after_discount += sr_doc.amount_after_discount or 0

        # Check if the Service Request has a "services" table
        if sr_doc.get("services"):
            print("  Items:")
            for item in sr_doc.services:
                # Each item has "item_code", "item_name", and "amount"
                print(f"    Item Code: {item.get('item_code', 'N/A')}")
                print(f"    Item Name: {item.get('item_name', 'N/A')}")
                print(f"    Amount: {item.get('amount', 'N/A')}")
                print("    ---")
        else:
            print("  No service items found in this request.")
        print("-" * 40)

    print(f"Total Amount After Discount for Customer {customer_id}: {total_amount_after_discount}")

if __name__ == "__main__":
    customer_id = "CUST-2025-00431"
    list_service_requests_and_total(customer_id)
