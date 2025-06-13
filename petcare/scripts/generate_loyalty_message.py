import frappe
from datetime import datetime

def generate_loyalty_message(customer_id, save_to_customer=True):
    """
    Generates a WhatsApp-friendly loyalty history message for a customer
    and optionally saves it in the Customer Doctype.
    """

    # Fetch customer details
    customer = frappe.get_doc("Customer", customer_id)
    customer_name = customer.customer_name
    total_redeemable_points = customer.custom_loyalty_points_balance or 0

    # Fetch all completed service requests for the customer, ordered by date
    service_requests = frappe.get_all(
        "Service Request",
        filters={"customer": customer_id, "status": "completed"},
        fields=["name", "completed_date", "amount_after_discount", "loyalty_points_earned", "loyalty_points_redeemed"],
        order_by="completed_date asc"
    )

    if not service_requests:
        message = f"Dear {customer_name},\n\nYou have no completed service requests yet. Your total redeemable points: {total_redeemable_points}."
    else:
        # Generate WhatsApp-friendly message
        message = f"✨ *Loyalty History - Masterpet* ✨\n\n"
        message += f"🐾 *Dear {customer_name},*\n"
        message += f"Here's your loyalty history with us:\n\n"

        running_balance = 0  # Keep track of the loyalty points history

        for sr in service_requests:
            # ✅ Convert datetime.date to formatted string
            sr_date = sr["completed_date"].strftime("%d-%b-%Y") if sr["completed_date"] else "N/A"

            earned = sr["loyalty_points_earned"] or 0
            redeemed = sr["loyalty_points_redeemed"] or 0
            running_balance += earned - redeemed

            # ✅ Fetch pet names for this service request, skipping NULL values
            service_items = frappe.get_all(
                "Service Items Child Table",
                filters={"parent": sr["name"], "pet_name": ["is", "set"]},  # Ensures pet_name is not NULL
                fields=["pet_name"]
            )

            # ✅ Extract unique pet names, skipping empty values
            pet_names = sorted(set(item["pet_name"] for item in service_items if item["pet_name"])) if service_items else []
            pet_names_str = f"🐶 *Pet(s):* {', '.join(pet_names)}\n" if pet_names else ""  # Only add if pets exist

            # ✅ Format WhatsApp-friendly message
            message += f"📌 *Service Request:* {sr['name']}\n"
            message += f"📅 *Date:* {sr_date}\n"
            message += pet_names_str  # Add only if pets exist
            message += f"💰 *Amount Paid:* ₹{round(sr['amount_after_discount'] or 0, 2)}\n"
            message += f"✨ *Loyalty Earned:* {earned} points\n"
            message += f"🔻 *Loyalty Redeemed:* {redeemed} points\n"
            message += f"🎯 *Balance after this request:* {running_balance} points\n"
            message += "----------------------------------\n"

        message += f"\n🎉 *Total Redeemable Loyalty Points:* {total_redeemable_points} points\n"
        message += "🙏 Thank you for being a valued Masterpet customer! We appreciate your love for pets. 🐾❤️\n"

    # ✅ Save the generated message to Customer Doctype
    if save_to_customer:
        frappe.db.set_value("Customer", customer_id, "custom_loyalty_message", message)
        frappe.db.commit()
        frappe.logger().info(f"📩 Loyalty message updated for Customer {customer_id}")

    return message
