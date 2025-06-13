import frappe

def get_naming_series_doc_types():
    """
    Retrieves a mapping of DocType to its allowed naming series options from the
    DocField where fieldname is 'naming_series'.
    """
    # Get all DocFields where the fieldname is 'naming_series'
    docfields = frappe.db.sql(
        "SELECT parent, options FROM `tabDocField` WHERE fieldname='naming_series'",
        as_dict=True
    )
    
    doc_type_series = {}
    for df in docfields:
        doctype = df['parent']
        if df['options']:
            # The options are typically newline-separated; split and trim them
            options = [opt.strip() for opt in df['options'].splitlines() if opt.strip()]
        else:
            options = []
        doc_type_series[doctype] = options
    return doc_type_series

def normalize_series(series_str):
    """Helper to normalize series string by stripping trailing '-' and whitespace."""
    return series_str.rstrip('-').strip()

def show_series_with_documents():
    # Retrieve all naming series from the tabSeries table
    series_list = frappe.db.sql("SELECT name, current FROM `tabSeries`", as_dict=True)
    
    # Build mapping of DocType to allowed naming series options
    doc_type_series = get_naming_series_doc_types()
    naming_series_doctypes = list(doc_type_series.keys())
    
    for series in series_list:
        series_name = series['name']
        normalized_series = normalize_series(series_name)
        
        # 1. Allowed usage from DocField options (normalize option strings too)
        allowed_in = []
        for doctype, options in doc_type_series.items():
            for option in options:
                if normalize_series(option) == normalized_series:
                    allowed_in.append(doctype)
                    break
        series['used_in'] = allowed_in
        
        # 2. Actual documents that use this series prefix:
        actual_usage = {}
        for doctype in naming_series_doctypes:
            # Count documents whose name starts with the series_name
            count = frappe.db.count(doctype, filters={"name": ("like", series_name + "%")})
            if count:
                actual_usage[doctype] = count
        series['actual_documents'] = actual_usage
        
        print(series)

show_series_with_documents()
