frappe.ui.form.on('Call Task', {
    customer: function(frm) {
        frm.trigger('fetch_voxbay_calls');
    },
    fetch_voxbay_calls: function(frm) {
        if (frm.doc.customer) {
            frappe.call({
                method: 'petcare.api.call_task.voxbay_call.get_voxbay_calls_for_customer',
                args: {
                    customer: frm.doc.customer
                },
                callback: function(r) {
                    if (r.message) {
                        frm.clear_table('voxbay_call');
                        r.message.forEach(function(call) {
                            var row = frm.add_child('voxbay_call');
                            row.voxbay_call_log = call.voxbay_call_log;
                            row.call_status = call.call_status;
                            row.call_type = call.call_type;
                            row.from_number = call.from_number;
                            row.to_number = call.to_number;
                            row.start_time = call.start_time;
                            row.end_time = call.end_time;
                            row.customer = call.customer;
                            row.customer_name = call.customer_name;
                            row.agent_number = call.agent_number;
                            row.recording_url = call.recording_url;
                        });
                        frm.refresh_field('voxbay_call');
                    }
                }
            });
        }
    }
}); 