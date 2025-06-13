import frappe

def create_items():
    """Creates multiple items in ERPNext"""
    
    item_data = [
    {
        "item_code": "WAHL-UC-RAKE",
        "item_name": "Wahl Undercoat Rake",
        "item_group": "Grooming Tools",
        "gst_hsn_code": "96032900",
        "stock_uom": "Nos",
        "is_stock_item": 1,
        "brand": "Wahl",
        "is_purchase_item": 1,
        "is_sales_item": 0,
        "supplier": "Pet Essence",
        "price_list": "Pet Essence",
        "rate": 380
    },
    {
        "item_code": "WAHL-CV-NCLIP",
        "item_name": "Wahl Curved Nail Clipper",
        "item_group": "Grooming Tools",
        "gst_hsn_code": "96032900",
        "stock_uom": "Nos",
        "is_stock_item": 1,
        "brand": "Wahl",
        "is_purchase_item": 1,
        "is_sales_item": 0,
        "supplier": "Pet Essence",
        "price_list": "Pet Essence",
        "rate": 320
    },
    {
        "item_code": "WAHL-DS-BRUSH-L",
        "item_name": "Wahl Double Sided Brush Large",
        "item_group": "Grooming Tools",
        "gst_hsn_code": "96032900",
        "stock_uom": "Nos",
        "is_stock_item": 1,
        "brand": "Wahl",
        "is_purchase_item": 1,
        "is_sales_item": 0,
        "supplier": "Pet Essence",
        "price_list": "Pet Essence",
        "rate": 360
    },
    {
        "item_code": "WAHL-FLEA-COMB",
        "item_name": "Wahl Flea Comb",
        "item_group": "Grooming Tools",
        "gst_hsn_code": "96032900",
        "stock_uom": "Nos",
        "is_stock_item": 1,
        "brand": "Wahl",
        "is_purchase_item": 1,
        "is_sales_item": 0,
        "supplier": "Pet Essence",
        "price_list": "Pet Essence",
        "rate": 260
    },
    {
        "item_code": "WAHL-CC-MG-COMBS",
        "item_name": "Wahl Color-Code Metal Guide Combs",
        "item_group": "Grooming Tools",
        "gst_hsn_code": "96032900",
        "stock_uom": "Nos",
        "is_stock_item": 1,
        "brand": "Wahl",
        "is_purchase_item": 1,
        "is_sales_item": 0,
        "supplier": "Pet Essence",
        "price_list": "Pet Essence",
        "rate": 1440
    },
    {
        "item_code": "WAHL-CDM-CLIPPER-PERF",
        "item_name": "Wahl Cdm Cordless Clipper-Performer",
        "item_group": "Grooming Tools",
        "gst_hsn_code": "96032900",
        "stock_uom": "Nos",
        "is_stock_item": 1,
        "brand": "Wahl",
        "is_purchase_item": 1,
        "is_sales_item": 0,
        "supplier": "Pet Essence",
        "price_list": "Pet Essence",
        "rate": 4500
    },
    {
        "item_code": "WAHL-CDM-CLIPPER-PERF-OFFER",
        "item_name": "Wahl Cdm Cordless Clipper-Performer (Buy 2 Get 1 Free)",
        "item_group": "Grooming Tools",
        "gst_hsn_code": "96032900",
        "stock_uom": "Nos",
        "is_stock_item": 1,
        "brand": "Wahl",
        "is_purchase_item": 1,
        "is_sales_item": 0,
        "supplier": "Pet Essence",
        "price_list": "Pet Essence",
        "rate": 0.45
    },
    {
        "item_code": "WAHL-SLICKER-BRUSH-XL",
        "item_name": "Wahl Slicker Brush XL",
        "item_group": "Grooming Tools",
        "gst_hsn_code": "96032900",
        "stock_uom": "Nos",
        "is_stock_item": 1,
        "brand": "Wahl",
        "is_purchase_item": 1,
        "is_sales_item": 0,
        "supplier": "Pet Essence",
        "price_list": "Pet Essence",
        "rate": 360
    },
    {
        "item_code": "WAHL-NCLIP-L",
        "item_name": "Wahl Nail Clipper Large",
        "item_group": "Grooming Tools",
        "gst_hsn_code": "96032900",
        "stock_uom": "Nos",
        "is_stock_item": 1,
        "brand": "Wahl",
        "is_purchase_item": 1,
        "is_sales_item": 0,
        "supplier": "Pet Essence",
        "price_list": "Pet Essence",
        "rate": 440
    },
    {
        "item_code": "STORY-TAILS-WIPES",
        "item_name": "Story Tails Pet Wipes",
        "item_group": "Grooming Supplies",
        "gst_hsn_code": "34022010",
        "stock_uom": "Nos",
        "is_stock_item": 1,
        "brand": "Story Tails",
        "is_purchase_item": 1,
        "is_sales_item": 0,
        "supplier": "Pet Essence",
        "price_list": "Pet Essence",
        "rate": 169.07
    },
    {
        "item_code": "WAHL-PUPPY-SHAMPOO",
        "item_name": "Wahl Puppy Shampoo",
        "item_group": "Grooming Supplies",
        "gst_hsn_code": "33051090",
        "stock_uom": "Nos",
        "is_stock_item": 1,
        "brand": "Wahl",
        "is_purchase_item": 1,
        "is_sales_item": 0,
        "supplier": "Pet Essence",
        "price_list": "Pet Essence",
        "rate": 504.24
    },
    {
        "item_code": "DELIVERY-CHARGE",
        "item_name": "Delivery Charge",
        "item_group": "Service",
        "gst_hsn_code": "996812",
        "stock_uom": "Nos",
        "is_stock_item": 0,
        "brand": "N/A",
        "is_purchase_item": 1,
        "is_sales_item": 0,
        "supplier": "Pet Essence",
        "price_list": "Pet Essence",
        "rate": 8.47
    }
    ]

    
    for data in item_data:
        try:
            # Check if item already exists
            if frappe.db.exists("Item", data["item_code"]):
                print(f"Item '{data['item_code']}' already exists. Skipping...")
                continue

            # Create Item
            item = frappe.get_doc({
                "doctype": "Item",
                "item_code": data["item_code"],
                "item_name": data["item_name"],
                "item_group": data["item_group"],
                "gst_hsn_code": data["gst_hsn_code"],
                "stock_uom": data["stock_uom"],
                "is_stock_item": data["is_stock_item"],
                "brand": data["brand"],
                "is_purchase_item": data["is_purchase_item"],
                "is_sales_item": data["is_sales_item"],
                "supplier_items": [{
                    "supplier": data["supplier"],
                    "supplier_part_no": data.get("supplier_part_no", "")
                }]
            })
            item.insert(ignore_permissions=True)
            frappe.db.commit()
            print(f"Item '{data['item_code']}' created successfully.")

            # Create Item Price
            item_price = frappe.get_doc({
                "doctype": "Item Price",
                "item_code": data["item_code"],
                "price_list": data["price_list"],
                "price_list_rate": data["rate"]
            })
            item_price.insert(ignore_permissions=True)
            frappe.db.commit()
            print(f"Item Price for '{data['item_code']}' added successfully.")
        
        except Exception as e:
            print(f"Error creating item '{data['item_code']}': {str(e)}")
            frappe.db.rollback()

