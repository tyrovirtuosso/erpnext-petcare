# File: handle_voxbay_event.py

import frappe
from frappe import _
import json
from datetime import datetime
import os

def load_api_key():
    """Load API key from configuration file"""
    config_path = "/home/frappe-user/frappe-bench/keys/voxbay_config.json"
    try:
        with open(config_path, 'r') as f:
            config = json.load(f)
            return config.get('api_key')
    except Exception as e:
        frappe.logger().error(f"Error loading API key: {str(e)}")
        return None

class DateTimeEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, datetime):
            return obj.strftime('%Y-%m-%d %H:%M:%S')
        return super().default(obj)

def format_phone_number(number):
    """Format phone number to ensure it has + prefix"""
    if not number:
        return number
    
    # Remove any spaces or special characters except +
    cleaned_number = ''.join(char for char in str(number) if char.isdigit() or char == '+')
    
    # Add + if it's not there
    if not cleaned_number.startswith('+'):
        cleaned_number = '+' + cleaned_number
        
    return cleaned_number

@frappe.whitelist(allow_guest=True)
def handle_voxbay_event():
    from frappe.utils import get_datetime
    from frappe.model.document import get_controller
    import traceback

    try:
        print("\n=== Starting Voxbay Event Processing ===")
        print(f"Request Method: {frappe.local.request.method}")
        print(f"Request Headers: {dict(frappe.local.request.headers)}")
        
        # Validate API key
        api_key = frappe.get_request_header('X-Api-Key')
        if not api_key:
            error_msg = "Missing API key in request headers"
            print(f"ERROR: {error_msg}")
            frappe.logger().error(error_msg)
            return {"message": "Error", "error": "Unauthorized", "details": "API key is required"}, 401

        valid_api_key = load_api_key()
        if not valid_api_key or api_key != valid_api_key:
            error_msg = "Invalid API key"
            print(f"ERROR: {error_msg}")
            frappe.logger().error(error_msg)
            return {"message": "Error", "error": "Unauthorized", "details": "Invalid API key"}, 401

        print("✓ API key validated")
        
        # Log the incoming request details
        frappe.logger().info("=== Starting Voxbay Event Processing ===")
        frappe.logger().info(f"Request Method: {frappe.local.request.method}")
        frappe.logger().info(f"Request Headers: {dict(frappe.local.request.headers)}")
        
        data = frappe.local.form_dict
        print(f"Received Voxbay data: {json.dumps(data, indent=2)}")
        frappe.logger().info(f"Received Voxbay data: {json.dumps(data)}")

        # Check if Voxbay Call Log doctype exists
        if not frappe.db.exists("DocType", "Voxbay Call Log"):
            error_msg = "Voxbay Call Log doctype does not exist"
            print(f"ERROR: {error_msg}")
            frappe.logger().error(error_msg)
            return {"message": "Error", "error": error_msg, "details": "Voxbay Call Log doctype not found in the system"}
        print("✓ Voxbay Call Log doctype exists")

        # Validate required fields
        required_fields = ["caller_number", "receiver_number", "start_time", "call_type", "call_status"]
        missing_fields = [field for field in required_fields if not data.get(field)]
        if missing_fields:
            error_msg = f"Missing required fields: {missing_fields}"
            print(f"ERROR: {error_msg}")
            frappe.logger().error(error_msg)
            return {"message": "Error", "error": error_msg, "details": f"Required fields missing: {', '.join(missing_fields)}"}
        print("✓ All required fields present")

        # Format phone numbers
        caller = format_phone_number(data.get("caller_number"))
        receiver = format_phone_number(data.get("receiver_number"))
        
        if not caller or not receiver:
            error_msg = "Invalid phone number format"
            print(f"ERROR: {error_msg}")
            frappe.logger().error(error_msg)
            return {"message": "Error", "error": error_msg, "details": "Phone numbers must be valid"}
        
        print(f"✓ Formatted caller number: {caller}")
        print(f"✓ Formatted receiver number: {receiver}")

        # Validate datetime format
        try:
            start_time = get_datetime(data.get("start_time"))
            print(f"✓ Parsed start_time: {start_time}")
            frappe.logger().info(f"Parsed start_time: {start_time}")
        except Exception as e:
            error_msg = f"Invalid start_time format: {str(e)}"
            print(f"ERROR: {error_msg}")
            frappe.logger().error(error_msg)
            return {"message": "Error", "error": error_msg, "details": f"Start time format error: {str(e)}"}

        try:
            end_time = get_datetime(data.get("end_time")) if data.get("end_time") else None
            print(f"✓ Parsed end_time: {end_time}")
            frappe.logger().info(f"Parsed end_time: {end_time}")
        except Exception as e:
            error_msg = f"Invalid end_time format: {str(e)}"
            print(f"ERROR: {error_msg}")
            frappe.logger().error(error_msg)
            return {"message": "Error", "error": error_msg, "details": f"End time format error: {str(e)}"}

        # Extract and validate other fields
        direction = data.get("call_type")
        status = data.get("call_status")
        duration = data.get("duration")
        recording_url = data.get("recording_url")
        call_id = data.get("call_id")

        print(f"\nProcessing call from {caller} to {receiver}")
        frappe.logger().info(f"Processing call from {caller} to {receiver}")
        if call_id:
            print(f"Call ID: {call_id}")
            frappe.logger().info(f"Call ID: {call_id}")

        # Validate call type
        if direction.lower() not in ["incoming", "outgoing"]:
            error_msg = f"Invalid call_type: {direction}. Must be 'incoming' or 'outgoing'"
            print(f"ERROR: {error_msg}")
            frappe.logger().error(error_msg)
            return {"message": "Error", "error": error_msg, "details": "Call type must be either 'incoming' or 'outgoing'"}
        print(f"✓ Valid call type: {direction}")

        # Map direction to ERPNext format
        call_type = "Incoming" if direction.lower() == "incoming" else "Outgoing"

        # Determine which number to use for customer lookup
        customer_number = caller if call_type == "Incoming" else receiver
        print(f"\nSearching for customer with number: {customer_number}")
        frappe.logger().info(f"Searching for customer with number: {customer_number}")
        
        # First try to find customer by mobile_no
        customer = frappe.db.get_value("Customer", {"mobile_no": ["like", f"%{customer_number}%"]})
        
        if not customer:
            print("Searching in Contact records...")
            # If not found in Customer, try to find in Contact records
            contacts = frappe.get_all(
                "Contact",
                filters={
                    "mobile_no": ["like", f"%{customer_number}%"],
                    "is_primary_contact": 1
                },
                fields=["name"]
            )
            
            if contacts:
                contact_name = contacts[0].name
                # Get linked customer from Dynamic Link table
                customer_link = frappe.get_all(
                    "Dynamic Link",
                    filters={
                        "parent": contact_name,
                        "parenttype": "Contact",
                        "link_doctype": "Customer"
                    },
                    fields=["link_name"]
                )
                
                if customer_link:
                    customer = customer_link[0].link_name
                    print(f"Found customer through Contact: {customer}")
                else:
                    # If still not found, create a new customer
                    print("No existing customer found, creating new customer...")
                    customer = create_new_customer(customer_number)
            else:
                # If no contact found, create a new customer
                print("No existing customer found, creating new customer...")
                customer = create_new_customer(customer_number)

        if not customer:
            error_msg = f"Could not find or create customer for number: {customer_number}"
            print(f"ERROR: {error_msg}")
            frappe.logger().warn(error_msg)
            return {"message": "Error", "error": error_msg, "details": "Failed to find or create customer"}

        print(f"✓ Found/created customer: {customer}")
        frappe.logger().info(f"Found/created customer: {customer}")

        # Check for duplicate logs using call_id
        if call_id:
            print(f"\nChecking for duplicate using call_id: {call_id}")
            existing_call = frappe.db.exists("Voxbay Call Log", {"call_id": call_id})
            
            if existing_call:
                print(f"✓ Duplicate found - existing call log: {existing_call}")
                frappe.logger().info(f"Duplicate Call Log found with call_id {call_id}: {existing_call}")
                return {"message": "Success", "status": "duplicate", "existing_log": existing_call}
            
            print("No duplicate found, proceeding with creation")

        # Create the Voxbay Call Log with detailed logging
        print("\nCreating new Voxbay Call Log document...")
        frappe.logger().info("Creating new Voxbay Call Log document")
        doc = frappe.new_doc("Voxbay Call Log")
        doc_data = {
            "from": caller,
            "to": receiver,
            "start_time": start_time,
            "end_time": end_time,
            "type": call_type,
            "status": status,
            "duration": duration,
            "customer": customer,
            "medium": "Voxbay",
            "recording_url": recording_url,
            "recording_html": f'<audio controls src="{recording_url}"></audio>' if recording_url else "",
            "agent_number": data.get("agent_number"),
            "button_pressed": data.get("button_pressed")
        }
        
        # Add call_id if provided
        if call_id:
            doc_data["call_id"] = call_id
            
        doc.update(doc_data)

        # Log the document data before insertion
        doc_dict = doc.as_dict()
        # Convert datetime objects to strings for JSON serialization
        if doc_dict.get('start_time'):
            doc_dict['start_time'] = doc_dict['start_time'].strftime('%Y-%m-%d %H:%M:%S')
        if doc_dict.get('end_time'):
            doc_dict['end_time'] = doc_dict['end_time'].strftime('%Y-%m-%d %H:%M:%S')
            
        print(f"Voxbay Call Log data to be inserted: {json.dumps(doc_dict, indent=2)}")
        frappe.logger().info(f"Voxbay Call Log data to be inserted: {json.dumps(doc_dict)}")

        try:
            print("\nAttempting to insert document...")
            doc.insert(ignore_permissions=True)
            frappe.db.commit()
            success_msg = f"✓ Voxbay Call log created successfully: {doc.name}"
            print(success_msg)
            frappe.logger().info(success_msg)
            return {"message": "Success", "call_log": doc.name}
        except Exception as e:
            error_msg = f"Error inserting Voxbay Call Log: {str(e)}"
            print(f"ERROR: {error_msg}")
            print(f"Traceback: {traceback.format_exc()}")
            frappe.logger().error(error_msg)
            frappe.log_error(frappe.get_traceback(), "Voxbay Call Log Insert Error")
            return {"message": "Error", "error": error_msg, "details": str(e), "traceback": traceback.format_exc()}

    except Exception as e:
        error_msg = f"Error processing Voxbay event: {str(e)}"
        print(f"ERROR: {error_msg}")
        print(f"Traceback: {traceback.format_exc()}")
        frappe.logger().error(error_msg)
        frappe.log_error(frappe.get_traceback(), "Voxbay Call Event Error")
        return {"message": "Error", "error": error_msg, "details": str(e), "traceback": traceback.format_exc()}

def create_new_customer(phone_number):
    """Create a new customer with the given phone number"""
    try:
        # Format the phone number before creating customer
        formatted_number = format_phone_number(phone_number)
        
        # Create new customer
        customer = frappe.new_doc("Customer")
        customer.customer_name = f"Customer {formatted_number}"
        customer.customer_type = "Individual"
        customer.mobile_no = formatted_number
        customer.insert(ignore_permissions=True)
        frappe.db.commit()
        return customer.name
    except Exception as e:
        error_msg = f"Error creating new customer: {str(e)}"
        print(f"ERROR: {error_msg}")
        print(f"Traceback: {traceback.format_exc()}")
        frappe.logger().error(error_msg)
        return None
