frappe.pages['groomer-driver-dashboard'].on_page_load = function(wrapper) {
    var page = frappe.ui.make_app_page({
        parent: wrapper,
        title: 'Groomer Driver Dashboard',
        single_column: true
    });
    
    // Initialize variables at page level for access across functions
    page.selected_status = 'Scheduled';
    page.selected_date = frappe.datetime.get_today();
    
    // Add refresh button in the header
    page.set_primary_action('Refresh', () => {
        // Get current values from UI to ensure we have the latest
        page.selected_date = page.main.find('.date-picker').val() || frappe.datetime.get_today();
        page.selected_status = page.main.find('.status-filters .btn.active').data('status') || 'Scheduled';
        loadServiceRequests(page.selected_status, page.selected_date);
    }, 'refresh');
    
    // Add main content container
    page.main.html(`
        <div class="groomer-driver-dashboard-content">
            <div class="metrics-dashboard mb-4">
                <div class="row">
                    <div class="col-md-3">
                        <div class="metric-card">
                            <div class="metric-title">Scheduled Total</div>
                            <div class="metric-value" id="scheduled-total">₹0.00</div>
                        </div>
                    </div>
                    <div class="col-md-3">
                        <div class="metric-card">
                            <div class="metric-title">Completed Total</div>
                            <div class="metric-value" id="completed-total">₹0.00</div>
                        </div>
                    </div>
                    <div class="col-md-3">
                        <div class="metric-card">
                            <div class="metric-title">3-Day Average</div>
                            <div class="metric-value" id="three-day-avg">₹0.00</div>
                        </div>
                    </div>
                    <div class="col-md-3">
                        <div class="metric-card">
                            <div class="metric-title">7-Day Average</div>
                            <div class="metric-value" id="seven-day-avg">₹0.00</div>
                        </div>
                    </div>
                </div>
            </div>
            <div class="service-requests-list">
                <div class="filters mb-3">
                    <div class="row align-items-center">
                        <div class="col-md-4">
                            <div class="status-filters btn-group" role="group">
                                <button type="button" class="btn btn-default" data-status="Scheduled">Scheduled</button>
                                <button type="button" class="btn btn-default" data-status="Completed">Completed</button>
                                <button type="button" class="btn btn-default" data-status="Cancelled">Cancelled</button>
                            </div>
                        </div>
                        <div class="col-md-4">
                            <div class="date-filter">
                                <input type="date" class="form-control date-picker" value="${frappe.datetime.get_today()}">
                            </div>
                        </div>
                    </div>
                </div>
                <div class="requests-container">
                    <!-- Service requests will be loaded here -->
                </div>
            </div>
        </div>
    `);
    
    // Add styles
    page.main.prepend(`
        <style>
            .service-requests-list {
                padding: 15px;
                max-width: 1200px;
                margin: 0 auto;
            }
            .filters {
                margin-bottom: 1.5rem;
            }
            .status-filters {
                display: flex;
                gap: 8px;
            }
            .date-filter {
                width: 100%;
            }
            .date-picker {
                width: 100%;
                padding: 8px;
                border-radius: 6px;
                border: 1px solid var(--gray-300);
            }
            .btn-group .btn {
                border: none;
                padding: 8px 16px;
                font-size: 14px;
                font-weight: 500;
                border-radius: 6px;
                background: var(--gray-100);
                color: var(--gray-800);
            }
            .btn-group .btn:hover {
                background: var(--gray-200);
            }
            .btn-group .btn.active {
                background: var(--gray-800);
                color: white;
            }
            .request-card {
                border: none;
                border-radius: 12px;
                padding: 20px;
                margin-bottom: 15px;
                background: white;
                box-shadow: 0 1px 3px rgba(0,0,0,0.1);
            }
            .request-card:hover {
                box-shadow: 0 4px 6px rgba(0,0,0,0.1);
            }
            .status-badge {
                display: inline-flex;
                align-items: center;
                padding: 4px 12px;
                border-radius: 6px;
                font-size: 13px;
                font-weight: 500;
            }
            .status-badge.completed {
                background-color: #E8F5E9;
                color: #2E7D32;
            }
            .status-badge.scheduled {
                background-color: #E3F2FD;
                color: #1565C0;
            }
            .status-badge.cancelled {
                background-color: #FAFAFA;
                color: #616161;
            }
            .customer-name {
                font-size: 16px;
                font-weight: 600;
                color: var(--gray-900);
            }
            .territory {
                display: inline-flex;
                align-items: center;
                padding: 4px 12px;
                border-radius: 6px;
                font-size: 13px;
                background: var(--gray-100);
                color: var(--gray-700);
                margin-left: 12px;
                font-weight: 500;
            }
            .service-type {
                margin-top: 8px;
                color: var(--gray-600);
                font-size: 14px;
                display: flex;
                align-items: center;
                gap: 4px;
            }
            .schedule-time {
                margin-top: 6px;
                color: var(--gray-600);
                font-size: 14px;
                display: flex;
                align-items: center;
                gap: 4px;
            }
            .assigned-to {
                margin-top: 6px;
                color: var(--gray-600);
                font-size: 14px;
                display: flex;
                align-items: center;
                gap: 4px;
            }
            .amount {
                font-weight: 600;
                color: var(--gray-900);
                font-size: 15px;
            }
            .metrics-dashboard {
                padding: 15px;
                max-width: 1200px;
                margin: 0 auto;
            }
            .metric-card {
                background: white;
                border-radius: 12px;
                padding: 20px;
                box-shadow: 0 1px 3px rgba(0,0,0,0.1);
                text-align: center;
            }
            .metric-title {
                color: var(--gray-600);
                font-size: 14px;
                font-weight: 500;
                margin-bottom: 8px;
            }
            .metric-value {
                color: var(--gray-900);
                font-size: 24px;
                font-weight: 600;
            }
        </style>
    `);

    // Initialize the dashboard
    initializeDashboard(page);
};

function initializeDashboard(page) {
    // First set the date picker value
    const datePicker = page.main.find('.date-picker');
    datePicker.val(page.selected_date);

    // Set initial active status
    page.main.find('.status-filters .btn[data-status="Scheduled"]').addClass('active');

    // Add click handlers for filter buttons
    page.main.find('.status-filters .btn').on('click', function() {
        page.main.find('.status-filters .btn').removeClass('active');
        $(this).addClass('active');
        page.selected_status = $(this).data('status');
        loadServiceRequests(page.selected_status, datePicker.val());
    });

    // Add change handler for date picker
    datePicker.on('change', function() {
        page.selected_date = $(this).val();
        loadServiceRequests(page.selected_status, page.selected_date);
    });

    // Trigger initial load with both filters
    loadServiceRequests(page.selected_status, page.selected_date);
}

function loadServiceRequests(status, selected_date) {
    if (!status || !selected_date) {
        console.warn('Missing filters:', { status, selected_date });
        status = status || 'Scheduled';
        selected_date = selected_date || frappe.datetime.get_today();
    }

    const requestsContainer = $('.requests-container');
    requestsContainer.html('<div class="text-muted">Loading...</div>');

    // Load financial metrics
    frappe.call({
        method: 'petcare.petcare.page.groomer_driver_dashboard.groomer_driver_dashboard.get_financial_metrics',
        type: 'GET',
        args: {
            selected_date: selected_date
        },
        callback: function(response) {
            console.log("Financial metrics response:", response); // Debug log
            if (response.message) {
                updateMetrics(response.message);
            }
        },
        error: function(err) {
            console.error("Error loading financial metrics:", err); // Debug log
            // Continue loading requests even if metrics fail
        }
    });

    // Load service requests
    frappe.call({
        method: 'petcare.petcare.page.groomer_driver_dashboard.groomer_driver_dashboard.get_service_requests',
        args: {
            status: status,
            selected_date: selected_date
        },
        callback: function(response) {
            if (response.message) {
                displayServiceRequests(response.message);
            } else {
                requestsContainer.html('<div class="text-muted">No service requests found for ' + selected_date + '</div>');
            }
        },
        error: function(err) {
            console.error('Error loading requests:', err);
            frappe.msgprint(__('Error loading service requests'));
        }
    });
}

function displayServiceRequests(requests) {
    const requestsContainer = $('.requests-container');
    
    if (!requests.length) {
        requestsContainer.html('<div class="text-muted">No service requests found</div>');
        return;
    }

    const requestsHtml = requests.map(request => `
        <div class="request-card">
            <div class="d-flex justify-content-between align-items-start">
                <div class="flex-grow-1">
                    <div class="d-flex justify-content-between align-items-center">
                        <div>
                            <span class="customer-name">${request.customer_name || request.customer}</span>
                            ${request.territory ? `<span class="territory">${request.territory}</span>` : ''}
                        </div>
                        <span class="status-badge ${request.status.toLowerCase()}">
                            ${request.status}
                        </span>
                    </div>
                    <div class="service-type">
                        <i class="fa fa-tag"></i> ${request.service_request_type || 'Not specified'}
                        ${request.total_pets ? ` • ${request.total_pets} pets` : ''}
                    </div>
                    <div class="schedule-time">
                        <i class="fa fa-calendar"></i> ${request.scheduled_time}
                    </div>
                    <div class="assigned-to">
                        <i class="fa fa-user"></i> Driver: ${request.driver_name}
                        ${request.driver_phone ? ` (${request.driver_phone})` : ''}
                    </div>
                    <div class="mt-3">
                        <span class="amount">${request.formatted_amount}</span>
                    </div>
                </div>
            </div>
        </div>
    `).join('');

    requestsContainer.html(requestsHtml);
}

function updateMetrics(metrics) {
    $('#scheduled-total').text(format_currency(metrics.scheduled_total));
    $('#completed-total').text(format_currency(metrics.completed_total));
    $('#three-day-avg').text(format_currency(metrics.three_day_avg));
    $('#seven-day-avg').text(format_currency(metrics.seven_day_avg));
}

function format_currency(value) {
    return frappe.format(value, { 
        fieldtype: 'Currency',
        currency: 'INR' // Explicitly set to Indian Rupees
    });
} 