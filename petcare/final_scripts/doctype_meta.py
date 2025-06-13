import frappe
import json

def get_doctype_meta(doctype):
    """
    Retrieve and print the meta details of the given DocType.

    Usage from the bench console:
        bench execute path.to.doctype_meta.get_doctype_meta --args '["YourDocTypeName"]'
    """
    meta = frappe.get_meta(doctype)
    
    # Prepare meta details as a dictionary
    meta_details = {
        "doctype": meta.name,
        "fields": []
    }
    
    for field in meta.fields:
        meta_details["fields"].append({
            "fieldname": field.fieldname,
            "label": field.label,
            "fieldtype": field.fieldtype,
            "options": field.options
        })

    # Print the meta details in a pretty JSON format
    print(json.dumps(meta_details, indent=4))


if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("Usage: bench execute path.to.doctype_meta.get_doctype_meta --args '\"YourDocTypeName\"'")
    else:
        get_doctype_meta(sys.argv[1])

# bench execute petcare.final_scripts.doctype_meta.get_doctype_meta --args '["Voxbay Call Log"]'