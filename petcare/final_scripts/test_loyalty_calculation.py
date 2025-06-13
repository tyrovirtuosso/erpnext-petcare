import frappe

def test_loyalty_for_customer(customer_id):
    # Fetch the Customer document
    customer = frappe.get_doc("Customer", customer_id)
    customer_name = customer.customer_name

    # Fetch all completed Service Requests for the customer, sorted by completed_date
    service_requests = frappe.get_all(
        "Service Request",
        filters={"customer": customer_id, "status": "completed"},
        fields=["name", "completed_date", "amount_after_discount", "loyalty_points_redeemed"],
        order_by="completed_date asc"
    )

    if not service_requests:
        print(f"No completed Service Requests found for customer {customer_name} ({customer_id})")
        return

    total_points = 0
    print("\n" + "=" * 100)
    print(f"Loyalty Points Calculation for Customer: {customer_name} ({customer_id})")
    print("=" * 100)
    print("{:<15} {:<15} {:<15} {:<20} {:<12} {:<10} {:<12} {:<12}".format(
        "Service Req.", "Completed Date", "Pet Name", "Item", "Cost (Rs)", "Points", "Redeemed", "Final Amount"
    ))
    print("-" * 100)

    # Process each Service Request
    for sr in service_requests:
        sr_doc = frappe.get_doc("Service Request", sr.name)
        eligible_amount = 0
        points_earned = 0
        historical_total = sr_doc.amount_after_discount  # Save original amount before any redemption
        redeemed_points = sr_doc.loyalty_points_redeemed or 0

        if sr_doc.get("services"):
            for item in sr_doc.services:
                # Exclude items with these item codes
                if item.item_code not in ["TRAVEL_EXP", "Food", "TIP"]:
                    item_points = int(item.amount / 27.5)  # 1 point per Rs. 27.5 spent
                    eligible_amount += item.amount or 0
                    points_earned += item_points
                    total_points += item_points

                    # Print row for each item
                    print("{:<15} {:<15} {:<15} {:<20} {:<12} {:<10} {:<12} {:<12}".format(
                        sr_doc.name, str(sr.completed_date), item.pet_name, item.item_code,
                        round(item.amount, 2), item_points, redeemed_points if item == sr_doc.services[-1] else "-", 
                        historical_total - redeemed_points if item == sr_doc.services[-1] else "-"
                    ))

        else:
            print(f"{sr_doc.name} has no service items.")

        # Store final historical total before redemption
        frappe.db.set_value("Service Request", sr_doc.name, "historical_total", historical_total)

        # Update loyalty points earned in this service request
        frappe.db.set_value("Service Request", sr_doc.name, "loyalty_points_earned", points_earned)

    print("-" * 100)
    print(f"Total Loyalty Points Earned: {total_points} (1 point = ₹1)")
    print("=" * 100 + "\n")

    # Update the total points in the Customer document
    frappe.db.set_value("Customer", customer_id, "custom_loyalty_points_balance", total_points)
    frappe.db.commit()

    print(f"Updated Customer {customer_name} ({customer_id}) with {total_points} loyalty points.\n")

# test_loyalty_for_customer("CUST-2025-00431")
