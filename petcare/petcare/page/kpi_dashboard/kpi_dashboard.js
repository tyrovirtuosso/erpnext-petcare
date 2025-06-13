frappe.pages['kpi_dashboard'].on_page_load = function(wrapper) {
    // Create the app page
    var page = frappe.ui.make_app_page({
        parent: wrapper,
        title: 'KPI Dashboard',
        single_column: true
    });

    // Helper: format date as yyyy-mm-dd
    const formatDate = (date) => date.toISOString().slice(0, 10);

    // State
    let today = new Date();
    let startDate = formatDate(today);
    let endDate = formatDate(today);
    let lastPeriodRevenue = 0; // Will be set from backend
    let currentRevenue = 0; // Will be set from backend

    // Render UI
    function render() {
        // Calculate trend
        let trend = 0;
        if (lastPeriodRevenue > 0) {
            trend = ((currentRevenue - lastPeriodRevenue) / lastPeriodRevenue) * 100;
        }
        const trendIcon = trend >= 0
            ? `<span class='text-green-600' aria-label='Up'>▲</span>`
            : `<span class='text-red-600' aria-label='Down'>▼</span>`;
        const trendText = `<span class='ml-1 text-sm ${trend >= 0 ? 'text-green-600' : 'text-red-600'}'>${trendIcon} ${Math.abs(trend).toFixed(1)}% vs previous</span>`;

        page.main.html(`
            <div class="w-full flex flex-col items-center">
                <div class="flex flex-wrap gap-2 mb-6 items-center justify-center">
                    <label for="startDate" class="sr-only">Start Date</label>
                    <input id="startDate" type="date" value="${startDate}" class="border rounded px-2 py-1 focus:ring-2 focus:ring-blue-500" aria-label="Start Date">
                    <span class="mx-1 text-gray-500">to</span>
                    <label for="endDate" class="sr-only">End Date</label>
                    <input id="endDate" type="date" value="${endDate}" class="border rounded px-2 py-1 focus:ring-2 focus:ring-blue-500" aria-label="End Date">
                    <button class="ml-4 px-3 py-1 rounded bg-gray-100 hover:bg-blue-100 text-gray-700" id="todayBtn" tabindex="0" aria-label="Today">Today</button>
                    <button class="px-3 py-1 rounded bg-gray-100 hover:bg-blue-100 text-gray-700" id="monthBtn" tabindex="0" aria-label="This Month">This Month</button>
                    <button class="px-3 py-1 rounded bg-gray-100 hover:bg-blue-100 text-gray-700" id="yearBtn" tabindex="0" aria-label="This Year">This Year</button>
                </div>
                <div class="flex flex-col items-center justify-center bg-white rounded-lg shadow-md p-8 m-4 w-full max-w-xs border border-gray-200 focus:outline-none focus:ring-2 focus:ring-blue-500" tabindex="0" aria-label="Total Revenue" role="region" aria-live="polite">
                    <span>
                        <svg class="w-8 h-8 text-blue-500 mb-2" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24" aria-hidden="true"><path stroke-linecap="round" stroke-linejoin="round" d="M12 8c-2.21 0-4 1.343-4 3s1.79 3 4 3 4-1.343 4-3-1.79-3-4-3zm0 0V4m0 12v4m8-8a8 8 0 11-16 0 8 8 0 0116 0z"/></svg>
                    </span>
                    <span class="text-gray-600 text-lg font-medium mb-1">Total Revenue</span>
                    <span class="text-3xl font-bold text-gray-900">₹${currentRevenue.toLocaleString()}</span>
                    <span class="mt-2">${trendText}</span>
                </div>
            </div>
        `);

        // Event listeners
        page.main.find('#startDate').on('change', function() {
            startDate = this.value;
            updateRevenue();
        });
        page.main.find('#endDate').on('change', function() {
            endDate = this.value;
            updateRevenue();
        });
        page.main.find('#todayBtn').on('click keydown', function(e) {
            if (e.type === 'click' || e.key === 'Enter') {
                startDate = endDate = formatDate(new Date());
                updateRevenue();
            }
        });
        page.main.find('#monthBtn').on('click keydown', function(e) {
            if (e.type === 'click' || e.key === 'Enter') {
                const now = new Date();
                startDate = formatDate(new Date(now.getFullYear(), now.getMonth(), 1));
                endDate = formatDate(new Date(now.getFullYear(), now.getMonth() + 1, 0));
                updateRevenue();
            }
        });
        page.main.find('#yearBtn').on('click keydown', function(e) {
            if (e.type === 'click' || e.key === 'Enter') {
                const now = new Date();
                startDate = formatDate(new Date(now.getFullYear(), 0, 1));
                endDate = formatDate(new Date(now.getFullYear(), 11, 31));
                updateRevenue();
            }
        });
    }

    // Fetch revenue data from backend
    function updateRevenue() {
        // Calculate previous period
        const start = new Date(startDate);
        const end = new Date(endDate);
        const diff = (end - start) / (1000 * 60 * 60 * 24) + 1;
        const prevEnd = new Date(start);
        prevEnd.setDate(prevEnd.getDate() - 1);
        const prevStart = new Date(prevEnd);
        prevStart.setDate(prevStart.getDate() - diff + 1);

        frappe.call({
            method: "petcare.petcare.page.kpi_dashboard.kpi_dashboard.get_revenue",
            args: {
                from_date: startDate,
                to_date: endDate,
                prev_from_date: prevStart.toISOString().slice(0, 10),
                prev_to_date: prevEnd.toISOString().slice(0, 10)
            },
            callback: function(r) {
                if (r.message) {
                    lastPeriodRevenue = r.message.previous.grand_total;
                    currentRevenue = r.message.current.grand_total;
                    render();
                }
            }
        });
    }

    updateRevenue(); // Initial load
}; 