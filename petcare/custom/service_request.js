frappe.ui.form.on('Service Request', {
    refresh: function(frm) {
        if (!frm.is_new()) {
            frm.add_custom_button(__('Start Grooming Visit'), function() {
                frappe.set_route('grooming-visit', {
                    service_request: frm.doc.name
                });
            }, __('Actions'));
        }
    }
}); 