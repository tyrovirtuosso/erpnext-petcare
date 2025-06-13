# Configuration file for Google Sheets API
SPREADSHEET_URL = "https://docs.google.com/spreadsheets/d/1rXx6ePZJi3DmmhYyibundy0LkGbDYmiveizeAkozjjQ/edit?usp=sharing"

# Default sheet to analyze (can be modified as needed)
DEFAULT_SHEET_NAME = "Transactions"

# Path to the service account JSON file
SERVICE_ACCOUNT_JSON = "/home/frappe-user/frappe-bench/keys/trusty-catbird-422603-h3-89486159ee2c.json"

# Account settings
BANK_ACCOUNT = "Bank Account - MP"
DEFAULT_BANK_COST_CENTER = "Main - MP"
CREDITOR_ACCOUNT = "Creditors - MP"

# Company details
COMPANY_NAME = "Masterpet Care Private Limited"
COMPANY_GSTIN = "32AARCM6917C1ZG"

# Common filter to exclude already processed transactions
NOT_PROCESSED_FILTER = {
    "column": "Transaction Entered?",
    "not_equals": "yes"  # Case-insensitive match
}

# Dictionary of predefined filter sets for different transaction types
FILTER_SETS = {
    "truck_diesel": [
        {
            "column": "Notes",
            "contains": "Truck Diesel",  # Case-insensitive match
        },
        NOT_PROCESSED_FILTER
    ],
    "generator_petrol": [
        {
            "column": "Notes",
            "contains": "Generator Petrol",  # Case-insensitive match
        },
        NOT_PROCESSED_FILTER
    ],
    "sim_card": [
        {
            "column": "Notes",
            "contains": "SIM",  # Case-insensitive match
        },
        NOT_PROCESSED_FILTER
    ],
    "grooming_truck_maintenance": [
        {
            "column": "Notes",
            "contains": "Grooming Truck Maintenance",  # Case-insensitive match
        },
        NOT_PROCESSED_FILTER
    ],
    "grooming_truck": [
        {
            "column": "Notes",
            "contains": "Grooming Truck",  # Case-insensitive match
        },
        NOT_PROCESSED_FILTER
    ],
    "all_unprocessed": [
        NOT_PROCESSED_FILTER
    ],
    "pet_essence_transactions": [
        {
            "column": "Notes",
            "contains": "Pet Essence"  # Contains Pet Essence in notes
        },
        {
            "column": "Supplier (Vendor)",
            "not_equals": ""  # Has a supplier
        },
        NOT_PROCESSED_FILTER
    ],
    "abk_transactions": [
        {
            "column": "Notes",
            "contains": "abk"  # Contains Pet Essence in notes
        },
        {
            "column": "Supplier (Vendor)",
            "not_equals": ""  # Has a supplier
        },
        NOT_PROCESSED_FILTER
    ],
    "sim": [
        {
            "column": "Notes",
            "contains": "sim",  # Case-insensitive match
        },
        NOT_PROCESSED_FILTER
    ],
    "grooming_food": [
        {
            "column": "Notes",
            "contains": "grooming food",  # Case-insensitive match
        },
        NOT_PROCESSED_FILTER
    ],
    "staff_welfare": [
        {
            "column": "Notes",
            "contains": "staff welfare",  # Case-insensitive match
        },
        NOT_PROCESSED_FILTER
    ],
    "hiring": [
        {
            "column": "Notes",
            "contains": "hiring",  # Case-insensitive match
        },
        NOT_PROCESSED_FILTER
    ],
    "microsoft": [
        {
            "column": "Notes",
            "contains": "microsoft"  # Contains Pet Essence in notes
        },
        {
            "column": "Supplier (Vendor)",
            "not_equals": ""  # Has a supplier
        },
        NOT_PROCESSED_FILTER
    ],
    "justdial": [
        {
            "column": "Notes",
            "contains": "justdial"  # Contains Pet Essence in notes
        },
        {
            "column": "Supplier (Vendor)",
            "not_equals": ""  # Has a supplier
        },
        NOT_PROCESSED_FILTER
    ],
    "voxbay": [
        {
            "column": "Notes",
            "contains": "voxbay"  # Contains Pet Essence in notes
        },
        {
            "column": "Supplier (Vendor)",
            "not_equals": ""  # Has a supplier
        },
        NOT_PROCESSED_FILTER
    ],
    
    
    # Add more filter sets as needed
}

# Default filters (for backward compatibility)
FILTERS = FILTER_SETS["truck_diesel"]
