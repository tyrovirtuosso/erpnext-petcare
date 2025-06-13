import frappe
import time
from frappe import _
from petcare.petcare.page.customer_location_map.customer_location_map import extract_coordinates_from_url

def get_pending_customers_count():
    """Get count of converted customers without coordinates"""
    return frappe.db.count('Customer', {
        'custom_lead_status': 'Converted',
        'custom_google_maps_link': ['is', 'set'],
        'custom_latitude': 0.000,
        'custom_longitude': 0.000
    })

def get_pending_customers(batch_size=10):
    """Get batch of converted customers without coordinates"""
    return frappe.get_all(
        'Customer',
        filters={
            'custom_lead_status': 'Converted',
            'custom_google_maps_link': ['is', 'set'],
            'custom_latitude': 0.000,
            'custom_longitude': 0.000
        },
        fields=['name', 'customer_name', 'custom_google_maps_link'],
        limit=batch_size
    )

def update_customer_coordinates(batch_size=10, delay_seconds=2):
    """
    Update coordinates for converted customers in batches
    Args:
        batch_size: Number of customers to process in each batch
        delay_seconds: Delay between batches to prevent system overload
    """
    total_pending = get_pending_customers_count()
    if not total_pending:
        print("No customers found that need coordinate updates.")
        return

    print(f"\nTotal customers pending update: {total_pending}")
    print("\nStarting coordinate update process...")
    
    processed = 0
    success = 0
    failed = 0
    
    while True:
        customers = get_pending_customers(batch_size)
        if not customers:
            break
            
        print(f"\nProcessing batch of {len(customers)} customers...")
        
        for customer in customers:
            try:
                print(f"\nProcessing {customer.customer_name} ({customer.name})")
                
                coordinates_str = extract_coordinates_from_url(customer.custom_google_maps_link)
                if coordinates_str:
                    try:
                        lat, lng = map(float, coordinates_str.split(','))
                        
                        # Update customer
                        doc = frappe.get_doc('Customer', customer.name)
                        doc.custom_latitude = lat
                        doc.custom_longitude = lng
                        doc.save()
                        
                        frappe.db.commit()
                        success += 1
                        print(f"✓ Successfully updated coordinates: {lat}, {lng}")
                        
                    except Exception as e:
                        failed += 1
                        error_msg = f"Error updating coordinates for customer {customer.name}: {str(e)}"
                        print(f"✗ {error_msg}")
                        frappe.log_error(
                            message=error_msg,
                            title="Customer Coordinate Update Error"
                        )
                else:
                    failed += 1
                    error_msg = f"Could not extract coordinates from map link for customer {customer.name}"
                    print(f"✗ {error_msg}")
                    frappe.log_error(
                        message=error_msg,
                        title="Customer Coordinate Update Error"
                    )
            except Exception as e:
                failed += 1
                error_msg = f"Error processing customer {customer.name}: {str(e)}"
                print(f"✗ {error_msg}")
                frappe.log_error(
                    message=error_msg,
                    title="Customer Coordinate Update Error"
                )
            
            processed += 1
            
        # Print batch summary
        print(f"\nBatch Summary:")
        print(f"Processed: {processed}/{total_pending}")
        print(f"Success: {success}")
        print(f"Failed: {failed}")
        
        # Delay between batches
        if delay_seconds > 0:
            print(f"\nWaiting {delay_seconds} seconds before next batch...")
            time.sleep(delay_seconds)
    
    # Print final summary
    print(f"\nFinal Summary:")
    print(f"Total Processed: {processed}")
    print(f"Total Success: {success}")
    print(f"Total Failed: {failed}")
    print(f"Remaining: {total_pending - processed}")

def update_single_customer_coordinates(doc, method=None):
    """
    Update coordinates for a single customer when Google Maps link changes
    Args:
        doc: Customer document
        method: Trigger method (not used but required for hooks)
    """
    try:
        # Check if Google Maps link exists and coordinates need updating
        if doc.custom_google_maps_link:
            coordinates_str = extract_coordinates_from_url(doc.custom_google_maps_link)
            if coordinates_str:
                try:
                    lat, lng = map(float, coordinates_str.split(','))
                    
                    # Only update if coordinates have changed
                    if doc.custom_latitude != lat or doc.custom_longitude != lng:
                        doc.custom_latitude = lat
                        doc.custom_longitude = lng
                        print(f"✓ Successfully updated coordinates for {doc.name}: {lat}, {lng}")
                        
                        # Show success message to user
                        frappe.msgprint(
                            msg=f'Coordinates updated successfully to: {lat}, {lng}',
                            title='Coordinates Updated',
                            indicator='green'
                        )
                    
                except Exception as e:
                    error_msg = f"Error updating coordinates for customer {doc.name}: {str(e)}"
                    print(f"✗ {error_msg}")
                    frappe.log_error(
                        message=error_msg,
                        title="Customer Coordinate Update Error"
                    )
                    # Show error message to user
                    frappe.msgprint(
                        msg='Failed to update coordinates. Please check the error log.',
                        title='Coordinate Update Failed',
                        indicator='red'
                    )
            else:
                error_msg = f"Could not extract coordinates from map link for customer {doc.name}"
                print(f"✗ {error_msg}")
                frappe.log_error(
                    message=error_msg,
                    title="Customer Coordinate Update Error"
                )
                # Show error message to user
                frappe.msgprint(
                    msg='Could not extract coordinates from the Google Maps link. Please verify the link format.',
                    title='Coordinate Update Failed',
                    indicator='red'
                )
    except Exception as e:
        error_msg = f"Error processing customer {doc.name}: {str(e)}"
        print(f"✗ {error_msg}")
        frappe.log_error(
            message=error_msg,
            title="Customer Coordinate Update Error"
        )
        # Show error message to user
        frappe.msgprint(
            msg='An unexpected error occurred while updating coordinates. Please check the error log.',
            title='Coordinate Update Failed',
            indicator='red'
        )

if __name__ == '__main__':
    # Example usage:
    # bench execute petcare.scripts.update_customer_coordinates.update_customer_coordinates --args "[10, 2]"
    update_customer_coordinates() 