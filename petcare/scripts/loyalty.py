import frappe
from petcare.scripts.generate_loyalty_message import generate_loyalty_message  # Import function

def update_loyalty_totals(doc, method):
    """
    Calculates and updates loyalty points for a Service Request and updates the Customer's total loyalty balance.
    Also, updates the loyalty message in the Customer Doctype.
    """

    frappe.logger().info(f"🔹 Running update_loyalty_totals for {doc.customer}, Service Request: {doc.name}")
    print(f"🔹 Running update_loyalty_totals for {doc.customer}, Service Request: {doc.name}")

    # Ensure all None values are converted to 0
    doc.loyalty_points_earned = doc.loyalty_points_earned or 0
    doc.loyalty_points_redeemed = doc.loyalty_points_redeemed or 0

    # ✅ Calculate loyalty points based on service items
    eligible_amount = 0
    points_earned = 0
    if doc.get("services"):
        for item in doc.services:
            if item.item_code not in ["TRAVEL_EXP", "Food", "TIP"]:
                item_points = int(item.amount / 27.5)  # 1 point per Rs. 27.5 spent
                eligible_amount += item.amount or 0
                points_earned += item_points
                print(f"✅ Item: {item.item_code} | Amount: {item.amount} | Points Earned: {item_points}")

    # ✅ Store calculated loyalty points in the Service Request
    doc.loyalty_points_earned = points_earned
    frappe.db.set_value("Service Request", doc.name, "loyalty_points_earned", points_earned)  # Ensure it gets saved

    print(f"📌 Eligible Amount for Loyalty: {eligible_amount}")
    print(f"🎯 Earned Points: {doc.loyalty_points_earned}")

    # ✅ Fetch all previous completed service requests for this customer
    previous_requests = frappe.get_all(
        "Service Request",
        filters={"customer": doc.customer, "status": "completed", "completed_date": ["<", doc.completed_date]},
        fields=["loyalty_points_earned", "loyalty_points_redeemed"]
    )

    print(f"📌 Found {len(previous_requests)} previous service requests for {doc.customer}")
    
    # ✅ Calculate cumulative loyalty points
    total_earned = sum(sr["loyalty_points_earned"] or 0 for sr in previous_requests) + doc.loyalty_points_earned
    total_redeemed = sum(sr["loyalty_points_redeemed"] or 0 for sr in previous_requests) + doc.loyalty_points_redeemed

    # ✅ Update the Service Request fields
    doc.lifetime_loyalty_points = total_earned
    doc.total_loyalty_points = total_earned - total_redeemed
    doc.total_loyalty_points_redeemable = max(doc.total_loyalty_points - doc.loyalty_points_earned, 0)

    frappe.db.set_value("Service Request", doc.name, "total_loyalty_points", doc.total_loyalty_points)
    frappe.db.set_value("Service Request", doc.name, "lifetime_loyalty_points", doc.lifetime_loyalty_points)
    frappe.db.set_value("Service Request", doc.name, "total_loyalty_points_redeemable", doc.total_loyalty_points_redeemable)

    print(f"✅ Customer: {doc.customer} | Lifetime: {doc.lifetime_loyalty_points}, Total: {doc.total_loyalty_points}, Redeemable: {doc.total_loyalty_points_redeemable}")

    # ✅ Fetch all service requests (past & future) for correct customer balance
    all_requests = frappe.get_all(
        "Service Request",
        filters={"customer": doc.customer, "status": "completed"},
        fields=["loyalty_points_earned", "loyalty_points_redeemed"]
    )

    if not all_requests:
        print(f"⚠️ No service requests found for {doc.customer}, skipping loyalty balance update.")
        return

    # ✅ Calculate total customer loyalty balance
    customer_total_earned = sum(sr["loyalty_points_earned"] or 0 for sr in all_requests)
    customer_total_redeemed = sum(sr["loyalty_points_redeemed"] or 0 for sr in all_requests)
    customer_total_loyalty_points = customer_total_earned - customer_total_redeemed

    print(f"🎯 Updating customer {doc.customer} balance to {customer_total_loyalty_points}")
    frappe.logger().info(f"🎯 Customer {doc.customer} balance updated to {customer_total_loyalty_points}")

    # ✅ Update customer loyalty balance
    frappe.db.set_value("Customer", doc.customer, "custom_loyalty_points_balance", customer_total_loyalty_points)
    
    # ✅ Generate and save loyalty message **after** the calculations
    generate_loyalty_message(doc.customer)

    # ✅ Commit changes to ensure all updates are saved
    frappe.db.commit()
    print(f"📩 Loyalty message updated for Customer {doc.customer}")
