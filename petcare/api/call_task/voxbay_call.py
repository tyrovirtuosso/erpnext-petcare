import frappe

@frappe.whitelist()
def get_voxbay_calls_for_customer(customer, date=None):
    voxbay_calls = frappe.get_all(
        "Voxbay Call Log",
        filters={
            "customer": customer
        },
        fields=[
            "name as voxbay_call_log",
            "status as call_status",
            "type as call_type",
            "from as from_number",
            "to as to_number",
            "start_time",
            "end_time",
            "customer",
            "customer_name",
            "agent_number",
            "recording_url"
        ]
    )
    return voxbay_calls 