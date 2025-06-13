import frappe

def reset_naming_series(series_name):
    """Reset the naming series count for a given series name."""
    frappe.db.sql("UPDATE `tabSeries` SET current = 0 WHERE name = %s", series_name)
    frappe.db.commit()
    print(f"Naming series '{series_name}' has been reset to start from 1.")

def get_naming_series_count(series_name):
    """Fetch and display the current count of a given naming series."""
    series_data = frappe.db.sql("SELECT name, current FROM `tabSeries` WHERE name = %s", series_name, as_dict=True)
    
    if series_data:
        print(f"Current count for '{series_name}': {series_data[0]['current']}")
        return series_data[0]['current']
    else:
        print(f"No record found for '{series_name}'. It may already be reset or unused.")
        return None

# Example Usage
series_name = "ACC-JV-2025-"  # Change this if needed
get_naming_series_count(series_name)  # Check current count before resetting
reset_naming_series(series_name)  # Reset the naming series count
get_naming_series_count(series_name)  # Verify reset
