import frappe

def get_contact_permission_query(user):
    """
    Restrict contacts based on the 'custom_is_restricted' field.
    - Users without "Restricted Contact Viewer" cannot see restricted contacts.
    """
    
    if "Restricted Contact Viewer" in frappe.get_roles(user):
        return ""  # No restriction for this role

    return "(`tabContact`.custom_is_restricted = 0 OR `tabContact`.custom_is_restricted IS NULL)"
