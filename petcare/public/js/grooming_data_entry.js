// Adapted for public website use: no frappe.call, no frappe.utils

function escapeHtml(text) {
  return String(text)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#039;');
}

document.addEventListener('DOMContentLoaded', function() {
    renderGroomingDataEntry();
});

const renderGroomingDataEntry = async () => {
    const $root = $('#grooming-data-entry-root');
    $root.empty();

    // State
    let groomingRequests = [];
    let filteredRequests = [];
    let drivers = [];
    let groomers = [];
    let selectedDriver = '';
    let selectedGroomer = '';
    let searchTerm = '';
    let savingId = null;
    let savedIds = new Set();

    // Fetch data
    async function fetchData() {
        // Fetch grooming requests
        const response = await fetch('/api/method/petcare.petcare.page.grooming_data_entry.grooming_data_entry.get_grooming_requests');
        const data = await response.json();
        groomingRequests = data.message || [];
        drivers = [...new Set(groomingRequests.map(r => r.driver).filter(Boolean))];
        groomers = [...new Set(groomingRequests.map(r => r.groomer).filter(Boolean))];
        savedIds = new Set(groomingRequests.filter(r => r.driver_suggestions && Object.keys(r.driver_suggestions).length > 0).map(r => r.name));
        filteredRequests = groomingRequests;
    }

    // Render a single card
    function renderCard(req) {
        const isSaved = savedIds.has(req.name);
        const isExpanded = false; // Will be set dynamically
        const cardHighlight = isSaved ? 'border-success shadow' : 'border-light';
        const cardBg = 'bg-white';
        const cardContainerBg = 'style="background:#f9f9f9;box-shadow:0 2px 8px rgba(0,0,0,0.03);"';
        const expandIcon = `<span class="mr-2">${isExpanded ? '▼' : '▶'}</span>`;
        const formatYesNo = val => val === 'Yes' ? '<span class="text-success font-weight-bold">Yes</span>' : val === 'No' ? '<span class="text-danger font-weight-bold">No</span>' : '<span class="text-muted">—</span>';
        const placeholder = '<span class="text-muted">—</span>';

        // Service Request link (always plain text for public)
        const serviceRequestLink = `<span class="font-weight-bold text-secondary" title="Login to view">${escapeHtml(req.name)}</span>`;
        const customerName = req.customer_name ? `<span class="font-weight-bold">${escapeHtml(req.customer_name)}</span>` : placeholder;
        let googleMapsLink = placeholder;
        if (req.google_maps_link) {
            googleMapsLink = `<a href="${escapeHtml(req.google_maps_link)}" target="_blank" rel="noopener noreferrer" class="text-primary font-weight-bold" aria-label="View on Map"><i class="fa fa-map-marker-alt mr-1"></i>View on Map</a>`;
        }

        // --- Sections ---
        const propertyInfo = `
            <div class="bg-light p-2 mb-2 rounded" style="border-bottom:1px solid #eee;">
                <div class="mb-2 font-weight-bold text-secondary" style="font-size:1.15rem;"><i class="fa fa-home mr-1"></i>Property Info</div>
                <div class="row">
                    <div class="col-12 col-md-3 small text-muted mb-2">Territory:<br><span class="text-dark">${escapeHtml(req.territory) || placeholder}</span></div>
                    <div class="col-12 col-md-3 small text-muted mb-2">Electricity:<br>${formatYesNo(req.electricity)}</div>
                    <div class="col-12 col-md-3 small text-muted mb-2">Water:<br>${formatYesNo(req.water)}</div>
                    <div class="col-12 col-md-3 small text-muted mb-2">Living Space:<br><span class="text-dark">${escapeHtml(req.living_space) || placeholder}</span></div>
                </div>
                <div class="row mt-1">
                    <div class="col-12 small text-muted">Living Space Notes:<br><span class="text-dark" style="font-size:0.92em;">${escapeHtml(req.living_space_notes) || placeholder}</span></div>
                </div>
            </div>
        `;
        let serviceItemsTable = '';
        if (req.service_items && req.service_items.length) {
            const isMobile = window.innerWidth < 576;
            if (isMobile) {
                serviceItemsTable = `
                    <div class="mb-2" style="border-bottom:1px solid #eee;">
                        <div class="mb-2 font-weight-bold text-secondary" style="font-size:1.15rem;"><i class="fa fa-paw mr-1"></i>Pet Services</div>
                        <div class="d-flex flex-column gap-2">
                            ${req.service_items.map(item => `
                                <div class="border rounded bg-light p-2 mb-2">
                                    <div><span class="font-weight-bold">${escapeHtml(item.pet_name || '')}</span> <span class="text-muted">(${escapeHtml(item.pet_breed || '')})</span></div>
                                    <div class="small">Item: ${escapeHtml(item.item_name || item.item_code || '')} | Qty: ${escapeHtml(item.quantity || '')} | Amount: ${escapeHtml(item.amount || '')}</div>
                                    <div class="small text-muted">Gender: ${escapeHtml(item.pet_gender || '')} | Behaviour: ${escapeHtml(item.pet_behaviour || '')} | Age: ${escapeHtml(item.pet_age || '')}</div>
                                    <div class="small text-muted">Notes: ${escapeHtml(item.pet_notes || '')}</div>
                                </div>
                            `).join('')}
                        </div>
                    </div>
                `;
            } else {
                serviceItemsTable = `
                    <div class="mb-2" style="border-bottom:1px solid #eee;">
                        <div class="mb-2 font-weight-bold text-secondary" style="font-size:1.15rem;"><i class="fa fa-paw mr-1"></i>Pet Services</div>
                        <div class="table-responsive">
                            <table class="table table-sm table-bordered bg-light mb-0">
                                <thead>
                                    <tr>
                                        <th style="min-width:80px;">Item</th><th style="min-width:40px;">Qty</th><th style="min-width:60px;">Amount</th>
                                        <th style="min-width:80px;">Name</th><th style="min-width:80px;">Breed</th><th class="d-none d-md-table-cell" style="min-width:60px;">Gender</th>
                                        <th class="d-none d-md-table-cell" style="min-width:80px;">Behaviour</th><th class="d-none d-md-table-cell" style="min-width:40px;">Age</th><th class="d-none d-md-table-cell" style="min-width:100px;">Notes</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    ${req.service_items.map(item => `
                                        <tr>
                                            <td>${escapeHtml(item.item_name || item.item_code || '')}</td>
                                            <td>${escapeHtml(item.quantity || '')}</td>
                                            <td>${escapeHtml(item.amount || '')}</td>
                                            <td>${escapeHtml(item.pet_name || '')}</td>
                                            <td>${escapeHtml(item.pet_breed || '')}</td>
                                            <td class="d-none d-md-table-cell">${escapeHtml(item.pet_gender || '')}</td>
                                            <td class="d-none d-md-table-cell">${escapeHtml(item.pet_behaviour || '')}</td>
                                            <td class="d-none d-md-table-cell">${escapeHtml(item.pet_age || '')}</td>
                                            <td class="d-none d-md-table-cell">${escapeHtml(item.pet_notes || '')}</td>
                                        </tr>
                                    `).join('')}
                                </tbody>
                            </table>
                        </div>
                    </div>
                `;
            }
        }
        const sessionLogistics = `
            <div class="bg-light p-2 mb-2 rounded" style="border-bottom:1px solid #eee;">
                <div class="mb-2 font-weight-bold text-secondary" style="font-size:1.15rem;"><i class="fa fa-car mr-1"></i>Session Logistics</div>
                <div class="row">
                    <div class="col-12 col-md-3 small text-muted mb-2">Driver Name:<br><span class="text-dark">${escapeHtml(req.driver) || placeholder}</span></div>
                    <div class="col-12 col-md-3 small text-muted mb-2">Groomer Name:<br><span class="text-dark">${escapeHtml(req.groomer) || placeholder}</span></div>
                    <div class="col-12 col-md-3 small text-muted mb-2">Parking Confirmed:<br>${formatYesNo(req.current_parking)}</div>
                    <div class="col-12 col-md-3 small text-muted mb-2">Google Maps:<br>${googleMapsLink}</div>
                </div>
            </div>
        `;
        const additionalNotes = `
            <div class="bg-light p-2 mb-2 rounded" style="border-bottom:1px solid #eee;">
                <div class="mb-2 font-weight-bold text-secondary" style="font-size:1.15rem;"><i class="fa fa-clipboard mr-1"></i>Additional Notes</div>
                <div class="row">
                    <div class="col-12 small text-muted">Driver Notes:<br><span class="text-dark" style="font-size:0.92em;">${escapeHtml(req.driver_notes) || placeholder}</span></div>
                    <div class="col-12 small text-muted">Living Space Notes:<br><span class="text-dark" style="font-size:0.92em;">${escapeHtml(req.living_space_notes) || placeholder}</span></div>
                </div>
            </div>
        `;
        const cardHeader = `
            <div class="d-flex flex-row align-items-center w-100" style="min-height:48px;">
                <span class="expand-icon" style="font-size:1.2em;cursor:pointer;">${expandIcon}</span>
                <span class="font-weight-bold mr-2">${customerName}</span>
                <span class="font-weight-bold text-primary mr-2">${serviceRequestLink}</span>
                <span class="font-weight-bold mr-2 ml-auto">${escapeHtml(req.scheduled_date)}</span>
                <span class="font-weight-bold mr-2">${escapeHtml(req.status)}</span>
                ${isSaved ? '<i class="fa fa-check-circle text-success ml-2" aria-label="Saved"></i>' : ''}
            </div>
        `;
        const suggestionForm = `
            <form class="parking-form mt-2" autocomplete="off">
                <div class="form-row align-items-end flex-wrap">
                    <div class="form-group col-sm-6 mb-2 d-flex align-items-end">
                        <label class="font-weight-bold mr-2 mb-0">Suggest Parking</label>
                        <select class="form-control parking-select mr-2" aria-label="Suggest Parking" required style="max-width:220px;">
                            <option value="">Select a parking suggestion</option>
                            <option value="Yes" ${req.driver_suggestions?.parking === 'Yes' ? 'selected' : ''}>Yes</option>
                            <option value="No" ${req.driver_suggestions?.parking === 'No' ? 'selected' : ''}>No</option>
                        </select>
                        <button type="submit" class="btn btn-primary save-btn ml-2" disabled aria-label="Save Suggestion">
                            <i class="fa fa-save"></i> Save Suggestion
                        </button>
                        <span class="ml-2 saved-indicator" style="min-width:24px;">${isSaved ? '<span class="text-success font-weight-bold">✓ Parking suggestion saved</span>' : ''}</span>
                    </div>
                    <div class="form-group col-sm-6 mb-2">
                        <label class="font-weight-bold">Driver Name</label>
                        <input type="text" class="form-control driver-input" placeholder="Enter driver name" value="${escapeHtml(req.driver_suggestions?.driver || '')}" aria-label="Driver Name" list="driver-list">
                        <datalist id="driver-list">
                            ${drivers.map(d => `<option value="${escapeHtml(d)}">`).join('')}
                        </datalist>
                    </div>
                    <div class="form-group col-sm-6 mb-2">
                        <label class="font-weight-bold">Groomer Name</label>
                        <input type="text" class="form-control groomer-input" placeholder="Enter groomer name" value="${escapeHtml(req.driver_suggestions?.groomer || '')}" aria-label="Groomer Name" list="groomer-list">
                        <datalist id="groomer-list">
                            ${groomers.map(g => `<option value="${escapeHtml(g)}">`).join('')}
                        </datalist>
                    </div>
                    <div class="form-group col-sm-4 mb-2">
                        <label class="font-weight-bold">Electricity</label>
                        <select class="form-control electricity-select" aria-label="Electricity">
                            <option value="">-- Select --</option>
                            <option value="Yes" ${req.driver_suggestions?.electricity === 'Yes' ? 'selected' : ''}>Yes</option>
                            <option value="No" ${req.driver_suggestions?.electricity === 'No' ? 'selected' : ''}>No</option>
                        </select>
                    </div>
                    <div class="form-group col-sm-4 mb-2">
                        <label class="font-weight-bold">Water</label>
                        <select class="form-control water-select" aria-label="Water">
                            <option value="">-- Select --</option>
                            <option value="Yes" ${req.driver_suggestions?.water === 'Yes' ? 'selected' : ''}>Yes</option>
                            <option value="No" ${req.driver_suggestions?.water === 'No' ? 'selected' : ''}>No</option>
                        </select>
                    </div>
                    <div class="form-group col-sm-4 mb-2">
                        <label class="font-weight-bold">Living Space</label>
                        <select class="form-control living-space-select" aria-label="Living Space">
                            <option value="">-- Select --</option>
                            <option value="Flat" ${req.driver_suggestions?.living_space === 'Flat' ? 'selected' : ''}>Flat</option>
                            <option value="House" ${req.driver_suggestions?.living_space === 'House' ? 'selected' : ''}>House</option>
                            <option value="Villa" ${req.driver_suggestions?.living_space === 'Villa' ? 'selected' : ''}>Villa</option>
                        </select>
                    </div>
                    <div class="form-group col-12 mb-2">
                        <label class="font-weight-bold">Living Space Notes</label>
                        <textarea class="form-control living-space-notes-input" placeholder="Enter living space notes" aria-label="Living Space Notes" style="font-size:0.92em;">${escapeHtml(req.driver_suggestions?.living_space_notes || '')}</textarea>
                    </div>
                    <div class="form-group col-12 mb-2">
                        <label class="font-weight-bold">Driver Notes</label>
                        <textarea class="form-control notes-input" placeholder="Enter notes" aria-label="Driver Notes" style="font-size:0.92em;">${escapeHtml(req.driver_suggestions?.notes || '')}</textarea>
                    </div>
                </div>
            </form>
        `;
        return `
            <div class="card mb-4 ${cardHighlight}" data-session-id="${escapeHtml(req.name)}" ${cardContainerBg}>
                <div class="card-header bg-white d-flex align-items-center" style="cursor:pointer; border-bottom:1px solid #eee;" tabindex="0" data-toggle="collapse" data-target="#collapse-${escapeHtml(req.name)}" aria-expanded="false" aria-controls="collapse-${escapeHtml(req.name)}">
                    ${cardHeader}
                </div>
                <div id="collapse-${escapeHtml(req.name)}" class="collapse">
                    <div class="card-body">
                        ${propertyInfo}
                        ${serviceItemsTable}
                        ${sessionLogistics}
                        ${additionalNotes}
                        ${suggestionForm}
                    </div>
                </div>
            </div>
        `;
    }

    function renderCards() {
        if (filteredRequests.length === 0) {
            return `<div class="alert alert-info mt-4">No grooming sessions found.</div>`;
        }
        return filteredRequests.map(renderCard).join('');
    }

    function renderProgress() {
        const total = groomingRequests.length;
        const done = savedIds.size;
        return `<div class="sticky-top bg-white py-2 mb-3 shadow-sm rounded d-flex align-items-center" style="z-index:20; border-bottom:1px solid #eee;"><span class="font-weight-bold">${done} of ${total} sessions updated</span></div>`;
    }

    async function renderAll() {
        await fetchData();
        $root.html(`
            <div id="progress-tracker">${renderProgress()}</div>
            <div id="grooming-cards">${renderCards()}</div>
        `);
        bindEvents();
    }

    function bindEvents() {
        $('.card-header').on('click keydown', function(e) {
            if (e.type === 'click' || e.key === 'Enter' || e.key === ' ') {
                const $header = $(this);
                const $card = $header.closest('.card');
                const $collapse = $card.find('.collapse');
                const expanded = $collapse.hasClass('show');
                $('.collapse').collapse('hide');
                if (!expanded) {
                    $collapse.collapse('show');
                }
            }
        });

        $('.parking-form').on('submit', async function(e) {
            e.preventDefault();
            const $form = $(this);
            const $card = $form.closest('.card');
            const sessionId = $card.data('session-id');
            const parking = $form.find('.parking-select').val();
            const driverName = $form.find('.driver-input').val();
            const groomerName = $form.find('.groomer-input').val();
            const notes = $form.find('.notes-input').val();
            const electricity = $form.find('.electricity-select').val();
            const water = $form.find('.water-select').val();
            const livingSpace = $form.find('.living-space-select').val();
            const livingSpaceNotes = $form.find('.living-space-notes-input').val();

            if (!parking) {
                alert("Please select a parking suggestion.");
                return;
            }

            $form.find('.save-btn').prop('disabled', true);
            $form.find('.spinner-border').remove();
            $form.find('.save-btn').after('<span class="spinner-border spinner-border-sm ml-2"></span>');

            try {
                const suggestion = {
                    parking,
                    driver: driverName,
                    groomer: groomerName,
                    notes,
                    electricity,
                    water,
                    living_space: livingSpace,
                    living_space_notes: livingSpaceNotes
                };
                await fetch('/api/method/petcare.petcare.page.grooming_data_entry.grooming_data_entry.save_driver_suggestion', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        service_request_id: sessionId,
                        driver_suggestions: JSON.stringify(suggestion)
                    })
                });
                savedIds.add(sessionId);
                alert("Parking suggestion saved!");
                $card.replaceWith(renderCard(groomingRequests.find(r => r.name === sessionId)));
                $('#progress-tracker').html(renderProgress());
            } catch (err) {
                alert("Failed to save suggestion.");
            } finally {
                $form.find('.save-btn').prop('disabled', false);
                $form.find('.spinner-border').remove();
            }
        });

        $('.parking-select').on('change', function() {
            const $form = $(this).closest('form');
            const $saveBtn = $form.find('.save-btn');
            if ($(this).val()) {
                $saveBtn.prop('disabled', false);
            } else {
                $saveBtn.prop('disabled', true);
            }
        });
    }

    renderAll();
}; 