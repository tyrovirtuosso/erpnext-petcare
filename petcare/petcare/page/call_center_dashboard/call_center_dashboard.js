frappe.pages['call-center-dashboard'].on_page_load = function(wrapper) {
    // Check if user has required role
    if (!frappe.user.has_role('Petcare')) {
        frappe.throw(__('You need Petcare role to access this dashboard'));
        return;
    }

    var page = frappe.ui.make_app_page({
        parent: wrapper,
        title: 'Call Center Dashboard',
        single_column: true
    });

    // Add page content
    page.main.html(`
        <div class="call-center-dashboard">
            <div class="filters-section">
                <div class="date-filters">
                    <div class="date-range">
                        <input type="date" class="form-control date-picker" id="startDate" placeholder="Start Date">
                        <span class="text-muted">to</span>
                        <input type="date" class="form-control date-picker" id="endDate" placeholder="End Date">
                    </div>
                    <div class="quick-filters">
                        <button class="btn btn-default btn-sm" data-days="0">Today</button>
                        <button class="btn btn-default btn-sm" data-days="1">Yesterday</button>
                    </div>
                </div>
            </div>
            <div class="stats-container">
                <!-- Stats will be populated here -->
            </div>
            <div class="detailed-view">
                <h3>Detailed Call Information</h3>
                <div class="call-filters">
                    <select class="form-control agent-filter">
                        <option value="">All Agents</option>
                    </select>
                    <select class="form-control status-filter">
                        <option value="">All Calls</option>
                        <option value="successful">Successful Calls</option>
                        <option value="missed">Missed/Failed Calls</option>
                    </select>
                </div>
                <div class="calls-table">
                    <!-- Table will be populated here -->
                </div>
            </div>
        </div>
    `);

    // Add custom styles
    frappe.dom.set_style(`
        .call-center-dashboard {
            padding: 20px;
        }
        .filters-section {
            margin-bottom: 20px;
        }
        .date-filters {
            display: flex;
            flex-direction: column;
            gap: 10px;
        }
        .date-range {
            display: flex;
            align-items: center;
            gap: 10px;
        }
        .date-range .text-muted {
            padding: 0 5px;
        }
        .quick-filters {
            display: flex;
            gap: 10px;
        }
        .stats-container {
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(350px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }
        .agent-card {
            background: white;
            border-radius: 8px;
            padding: 20px;
            box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
            cursor: pointer;
            transition: transform 0.2s;
        }
        .agent-card:hover {
            transform: translateY(-2px);
        }
        .agent-title {
            font-size: 18px;
            font-weight: bold;
            margin-bottom: 15px;
            color: var(--text-color);
        }
        .stat-grid {
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(120px, 1fr));
            gap: 15px;
        }
        .stat-item {
            text-align: center;
            padding: 10px;
            background: var(--bg-light-gray);
            border-radius: 6px;
        }
        .stat-value {
            font-size: 24px;
            font-weight: bold;
            color: var(--text-color);
            margin-bottom: 5px;
        }
        .stat-label {
            font-size: 12px;
            color: var(--text-muted);
        }
        .success-stat {
            color: var(--green-500);
        }
        .missed-stat {
            color: var(--red-500);
        }
        .detailed-view {
            margin-top: 30px;
        }
        .call-filters {
            display: flex;
            gap: 15px;
            margin: 20px 0;
        }
        .calls-table {
            overflow-x: auto;
        }
        .calls-table table {
            width: 100%;
            border-collapse: collapse;
        }
        .calls-table th, .calls-table td {
            padding: 10px;
            text-align: left;
            border-bottom: 1px solid var(--border-color);
        }
        .calls-table tr:hover {
            background-color: var(--bg-light-gray);
        }
        .customer-link {
            color: var(--text-color);
            text-decoration: none;
            border-bottom: 1px dashed var(--text-muted);
        }
        .customer-link:hover {
            text-decoration: none;
            border-bottom-style: solid;
        }
        .customer-link .text-muted {
            font-size: 0.9em;
        }
    `);

    // Initialize the dashboard
    initializeDashboard(page);
};

function initializeDashboard(page) {
    let currentStartDate = frappe.datetime.get_today();
    let currentEndDate = frappe.datetime.get_today();
    let currentAgent = '';
    let currentStatus = '';

    // Set default dates
    $('#startDate').val(currentStartDate);
    $('#endDate').val(currentEndDate);

    // Event handlers for quick filters
    $('.quick-filters button').click(function() {
        const days = $(this).data('days');
        const date = frappe.datetime.add_days(frappe.datetime.get_today(), -days);
        $('#startDate').val(date);
        $('#endDate').val(date);
        refreshDashboard();
    });

    // Event handlers for date filters
    $('#startDate, #endDate').change(() => {
        const startDate = $('#startDate').val();
        const endDate = $('#endDate').val();
        
        // Validate date range
        if (startDate && endDate && startDate > endDate) {
            frappe.msgprint('Start date cannot be after end date');
            return;
        }
        
        refreshDashboard();
    });

    // Event handlers for detailed view filters
    $('.agent-filter').change(function() {
        currentAgent = $(this).val();
        refreshDetailedView();
    });

    $('.status-filter').change(function() {
        currentStatus = $(this).val();
        refreshDetailedView();
    });

    // Add refresh button
    page.set_primary_action('Refresh', () => refreshDashboard(), 'refresh');

    // Initial load
    refreshDashboard();

    function refreshDashboard() {
        const startDate = $('#startDate').val();
        const endDate = $('#endDate').val();
        
        frappe.call({
            method: 'petcare.petcare.page.call_center_dashboard.call_center_dashboard.get_agent_call_stats',
            args: {
                start_date: startDate,
                end_date: endDate
            },
            callback: function(response) {
                if (response.message) {
                    renderStats(response.message);
                    updateAgentFilter(response.message);
                    refreshDetailedView();
                }
            },
            error: function(err) {
                // Handle permission errors gracefully
                frappe.msgprint({
                    title: __('Error'),
                    indicator: 'red',
                    message: __('You do not have permission to access this dashboard. Please contact your administrator.')
                });
            }
        });
    }

    function refreshDetailedView() {
        const startDate = $('#startDate').val();
        const endDate = $('#endDate').val();
        
        frappe.call({
            method: 'petcare.petcare.page.call_center_dashboard.call_center_dashboard.get_detailed_calls',
            args: {
                start_date: startDate,
                end_date: endDate,
                agent_number: currentAgent,
                status: currentStatus
            },
            callback: function(response) {
                if (response.message) {
                    renderDetailedCalls(response.message);
                }
            },
            error: function(err) {
                // Handle permission errors gracefully
                frappe.msgprint({
                    title: __('Error'),
                    indicator: 'red',
                    message: __('You do not have permission to access this dashboard. Please contact your administrator.')
                });
            }
        });
    }
}

function updateAgentFilter(data) {
    const agentFilter = $('.agent-filter');
    agentFilter.empty();
    agentFilter.append('<option value="">All Agents</option>');
    
    data.forEach(agent => {
        if (agent.agent_number) {
            agentFilter.append(`<option value="${agent.agent_number}">${agent.agent_name}</option>`);
        }
    });
}

function renderStats(data) {
    const statsContainer = $('.stats-container');
    statsContainer.empty();

    data.forEach(agent => {
        // Accessibility: Add ARIA and keyboard support for agent cards
        const isNoAgent = agent.agent_name === 'No Agent';
        const agentCard = $(`
            <div class="agent-card ${isNoAgent ? 'bg-gray-100 border border-dashed border-gray-400' : ''}"
                data-agent="${agent.agent_number}"
                role="button"
                tabindex="0"
                aria-label="${isNoAgent ? 'No Agent' : agent.agent_name}"
            >
                <div class="agent-title ${isNoAgent ? 'text-red-600' : ''}">${isNoAgent ? '<span class="sr-only">No Agent</span>No Agent' : agent.agent_name}</div>
                <div class="stat-grid">
                    <div class="stat-item">
                        <div class="stat-value success-stat">${agent.successful_incoming}</div>
                        <div class="stat-label">Success Incoming</div>
                    </div>
                    <div class="stat-item">
                        <div class="stat-value missed-stat">${agent.failed_incoming || 0}</div>
                        <div class="stat-label">Failed Incoming</div>
                    </div>
                    <div class="stat-item">
                        <div class="stat-value success-stat">${agent.successful_outgoing}</div>
                        <div class="stat-label">Success Outgoing</div>
                    </div>
                    <div class="stat-item">
                        <div class="stat-value missed-stat">${agent.failed_outgoing}</div>
                        <div class="stat-label">Failed Outgoing</div>
                    </div>
                    <div class="stat-item">
                        <div class="stat-value">${agent.total_successful}</div>
                        <div class="stat-label">Total Success</div>
                    </div>
                    <div class="stat-item">
                        <div class="stat-value missed-stat">${agent.total_failed || 0}</div>
                        <div class="stat-label">Total Failed</div>
                    </div>
                </div>
            </div>
        `);

        // Add click handler to filter by agent
        agentCard.on('click keydown', function(e) {
            if (e.type === 'click' || (e.type === 'keydown' && (e.key === 'Enter' || e.key === ' '))) {
                const agentNumber = $(this).data('agent');
                $('.agent-filter').val(agentNumber).trigger('change');
            }
        });

        statsContainer.append(agentCard);
    });
}

function formatCustomerNumber(call) {
    if (!call.customer_number) return '-';
    
    if (call.contact_info && call.contact_info.customers && call.contact_info.customers.length > 0) {
        let displayParts = [];
        
        // Add customer links with name and territory
        const customerLinks = call.contact_info.customers.map(customer => 
            `<a href="/app/customer/${customer.name}" class="customer-link">
                <span class="text-muted">[${customer.customer_name || customer.name} - ${customer.territory}]</span>
            </a>`
        );
        
        // Show phone number and customer links
        displayParts.push(`<span>(${call.customer_number})</span>`);
        displayParts.push(customerLinks.join(' '));
        
        return displayParts.join(' ');
    }
    
    return call.customer_number;
}

function formatDuration(duration) {
    if (!duration) return '-';
    
    // Duration is already in seconds
    const seconds = Math.round(duration);
    
    if (seconds < 60) {
        return `${seconds}s`;
    } else {
        const minutes = Math.floor(seconds / 60);
        const remainingSeconds = seconds % 60;
        return remainingSeconds > 0 ? 
            `${minutes}m ${remainingSeconds}s` : 
            `${minutes}m`;
    }
}

function renderDetailedCalls(calls) {
    const callsTable = $('.calls-table');
    
    if (calls.length === 0) {
        callsTable.html('<p class="text-muted">No calls found for the selected filters.</p>');
        return;
    }

    const table = $(`
        <table class="table">
            <thead>
                <tr>
                    <th>Time</th>
                    <th>Agent</th>
                    <th>Customer</th>
                    <th>Type</th>
                    <th>Status</th>
                    <th>Duration</th>
                    <th>Recording</th>
                </tr>
            </thead>
            <tbody>
            </tbody>
        </table>
    `);

    const tbody = table.find('tbody');

    calls.forEach(call => {
        const row = $(`
            <tr>
                <td>${frappe.datetime.str_to_user(call.creation)}</td>
                <td>${call.agent_name || '<span class="missed-stat">No Agent</span>'}</td>
                <td>${formatCustomerNumber(call)}</td>
                <td>${call.type || '-'}</td>
                <td>
                    <span class="${call.status === 'ANSWER' || call.status === 'Completed' ? 'success-stat' : 'missed-stat'}">
                        ${call.status}
                    </span>
                </td>
                <td>${formatDuration(call.duration)}</td>
                <td>
                    ${call.recording_url ? 
                        `<button class="btn btn-xs btn-default" onclick="window.open('${call.recording_url}', '_blank')">
                            Play Recording
                        </button>` : 
                        '-'
                    }
                </td>
            </tr>
        `);
        tbody.append(row);
    });

    callsTable.empty().append(table);
} 