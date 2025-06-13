import frappe
from pprint import pprint
from petcare.api.service_request import calculate_service_distance

def test_calculate_service_distance(service_request_name):
    try:
        # Call the API method
        result = calculate_service_distance(service_request_name)
        # Print the result to the console
        print("Test Result:")
        pprint(result)
    except Exception as e:
        print(f"An error occurred during testing: {e}")

# Call the test function

def test_function():
    # Replace with an actual service request name in your database
    service_request_name = "SR-2025-00007"
    test_calculate_service_distance(service_request_name)

