import frappe

def daily():
    frappe.log_error("Daily Scheduler Executed", "Scheduler Test")

def hourly():
    frappe.logger().info("Hourly task started")
    frappe.log_error("Hourly task executed", "Scheduler Debug")