import os
import datetime
import json
from google.oauth2 import service_account
from googleapiclient.discovery import build
import frappe
import pytz

# Path to your Google service account JSON key file
SERVICE_ACCOUNT_FILE = "/home/frappe-user/frappe-bench/keys/trusty-catbird-422603-h3-9451d86c31ef.json"
CALENDAR_ID = "masterpetindia@gmail.com"

def authenticate_google_calendar():
    """Authenticate using the service account JSON file."""
    credentials = service_account.Credentials.from_service_account_file(
        SERVICE_ACCOUNT_FILE, scopes=["https://www.googleapis.com/auth/calendar"]
    )
    return build("calendar", "v3", credentials=credentials)

@frappe.whitelist()
def create_service_request_event(service_request):
    """Creates a calendar event from a Service Request."""
    try:
        # Get the service request document
        doc = frappe.get_doc('Service Request', service_request)
        
        # Add debug logging
        frappe.logger().debug(f"Service Request Data: scheduled_date={doc.scheduled_date}, start={doc.scheduled_date_start}, end={doc.scheduled_date_end}")
        
        # Get customer contacts
        customer_contacts = frappe.get_all(
            'Contact',
            filters={
                'link_doctype': 'Customer',
                'link_name': doc.customer
            },
            fields=['first_name', 'last_name', 'phone', 'mobile_no']
        )
        
        # Format contacts information
        contacts_info = "\nCustomer Contacts:\n"
        for contact in customer_contacts:
            name = f"{contact.first_name or ''} {contact.last_name or ''}".strip()
            contacts_info += f"""
Name: {name}
Phone: {contact.phone or contact.mobile_no or 'N/A'}
-------------------"""
        
        # Format the event description with all required details
        description = f"""
Service Request Details:
Customer: {doc.customer_name}
Status: {doc.status}
Assigned Driver: {doc.assigned_driver}
Total Amount: {doc.total_amount}
Total Pets: {doc.total_pets}
Discount Amount: {doc.discount_amount}
Amount After Discount: {doc.amount_after_discount}
Google Maps Link: {doc.google_maps_link}
Territory: {doc.territory}
User Notes: {doc.user_notes}
Parking: {doc.parking}
Electricity: {doc.electricity}
Water: {doc.water}
Living Space: {doc.living_space}
Living Space Notes: {doc.living_space_notes}
Mobile: {doc.mobile}
{contacts_info}

Services:
"""
        # Add services details
        for service in doc.services:
            description += f"""
Pet: {service.pet_name}
Breed: {service.pet_breed}
Gender: {service.pet_gender}
Notes: {service.pet_notes}
Behaviour: {service.pet_behaviour}
Age: {service.pet_age}
Service: {service.item_name}
Amount: {service.amount}
-------------------
"""

        # Create the event
        service = authenticate_google_calendar()
        
        # Get the timezone
        ist = pytz.timezone('Asia/Kolkata')
        
        try:
            # Convert the date and time to datetime objects with error handling
            if not doc.scheduled_date or not doc.scheduled_date_start or not doc.scheduled_date_end:
                frappe.throw("Scheduled date, start time, and end time are required")

            # Debug logging for date/time values
            frappe.logger().debug(f"Before conversion - scheduled_date: {type(doc.scheduled_date)}, start: {type(doc.scheduled_date_start)}, end: {type(doc.scheduled_date_end)}")
            
            # Handle start time
            if isinstance(doc.scheduled_date_start, str):
                start_time = datetime.datetime.strptime(doc.scheduled_date_start, '%H:%M:%S').time()
            elif isinstance(doc.scheduled_date_start, datetime.datetime):
                start_time = doc.scheduled_date_start.time()
            else:
                start_time = doc.scheduled_date_start

            # Handle end time
            if isinstance(doc.scheduled_date_end, str):
                end_time = datetime.datetime.strptime(doc.scheduled_date_end, '%H:%M:%S').time()
            elif isinstance(doc.scheduled_date_end, datetime.datetime):
                end_time = doc.scheduled_date_end.time()
            else:
                end_time = doc.scheduled_date_end

            start_datetime = datetime.datetime.combine(doc.scheduled_date, start_time)
            end_datetime = datetime.datetime.combine(doc.scheduled_date, end_time)
            
            # Debug logging after conversion
            frappe.logger().debug(f"After conversion - start_datetime: {start_datetime}, end_datetime: {end_datetime}")

        except Exception as e:
            frappe.throw(f"Error processing date/time: {str(e)}\nTypes - date: {type(doc.scheduled_date)}, start: {type(doc.scheduled_date_start)}, end: {type(doc.scheduled_date_end)}")
        
        # Localize the datetime objects to IST
        start_datetime = ist.localize(start_datetime)
        end_datetime = ist.localize(end_datetime)

        # Create event title with specified fields
        event_title = f"SR: {doc.customer_name} - {doc.territory} - {doc.total_pets} Pets - W:{doc.water}, E:{doc.electricity}, P:{doc.parking}"

        # Set color based on status
        color_id = "11" if doc.status == "Cancelled" else "2"  # Red for Cancelled, Green for others

        event = {
            "summary": event_title,
            "description": description,
            "start": {
                "dateTime": start_datetime.isoformat(),
                "timeZone": "Asia/Kolkata",
            },
            "end": {
                "dateTime": end_datetime.isoformat(),
                "timeZone": "Asia/Kolkata",
            },
            "colorId": color_id,  # Dynamic color based on status
            "reminders": {
                "useDefault": False,
                "overrides": [
                    {"method": "popup", "minutes": 10},
                ],
            },
        }

        # Insert event into Google Calendar
        event_response = service.events().insert(calendarId=CALENDAR_ID, body=event).execute()
        return event_response.get('htmlLink')

    except Exception as e:
        # Enhanced error reporting
        import traceback
        error_msg = f"Error creating calendar event: {str(e)}\n\nTraceback:\n{traceback.format_exc()}"
        frappe.logger().error(error_msg)
        frappe.throw(error_msg)

# Keep the original create_event function for testing
def create_event():
    """Creates a test event in Google Calendar."""
    try:
        service = authenticate_google_calendar()
        
        event = {
            "summary": "Test Event from ERPNext",
            "description": "This is a test event added via Google Calendar API.",
            "start": {
                "dateTime": (datetime.datetime.utcnow() + datetime.timedelta(minutes=5)).isoformat() + "Z",
                "timeZone": "Asia/Kolkata",
            },
            "end": {
                "dateTime": (datetime.datetime.utcnow() + datetime.timedelta(minutes=65)).isoformat() + "Z",
                "timeZone": "Asia/Kolkata",
            },
            "reminders": {
                "useDefault": False,
                "overrides": [
                    {"method": "email", "minutes": 30},
                    {"method": "popup", "minutes": 10},
                ],
            },
        }

        event_response = service.events().insert(calendarId=CALENDAR_ID, body=event).execute()
        print(f"Event created: {event_response.get('htmlLink')}")

    except Exception as e:
        print(f"Error creating event: {str(e)}")

if __name__ == "__main__":
    create_event()
