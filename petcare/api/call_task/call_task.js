frappe.ui.form.on('Call Task', {
    customer: function(frm) {
        frm.trigger('fetch_call_history');
    },
    date: function(frm) {
        frm.trigger('fetch_call_history');
    },
    fetch_call_history: function(frm) {
        if (frm.doc.customer && frm.doc.date) {
            frappe.call({
                method: 'petcare.api.call_task.call_task.get_customer_call_history',
                args: {
                    customer: frm.doc.customer,
                    date: frm.doc.date,
                    exclude_task: frm.doc.name
                },
                callback: function(r) {
                    if (r.message) {
                        frm.clear_table('call_history');
                        r.message.forEach(function(task) {
                            var row = frm.add_child('call_history');
                            row.call_task = task.call_task;
                            row.date = task.date;
                            row.task_type = task.task_type;
                            row.agent = task.agent;
                            row.next_follow_up_date = task.next_follow_up_date;
                            row.customer = task.customer;
                            row.status = task.status;
                        });
                        frm.refresh_field('call_history');
                    }
                }
            });
        }
    }
}); 