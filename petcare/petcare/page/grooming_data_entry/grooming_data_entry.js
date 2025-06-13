const getTodayDate = () => {
    const today = new Date();
    return today.toISOString().slice(0, 10);
};

frappe.pages['grooming_data_entry'].on_page_load = function(wrapper) {
    $(wrapper).html('<div id="grooming-data-entry-root"></div>');
    renderGroomingDataEntry();
};

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
    let selectedDate = getTodayDate();
    let tempDriverInputs = {};

    // Render date picker
    function renderDatePicker() {
        return `
            <div class="flex items-center gap-2 mb-4">
                <label for="grooming-date-picker" class="font-bold text-gray-700" aria-label="Select date for grooming sessions">Date:</label>
                <input id="grooming-date-picker" type="date" class="form-control w-auto" value="${selectedDate}" aria-label="Select date for grooming sessions" tabindex="0" />
            </div>
        `;
    }

    // Fetch data
    async function fetchData() {
        groomingRequests = await frappe.call('petcare.petcare.page.grooming_data_entry.grooming_data_entry.get_grooming_requests', { date: selectedDate })
            .then(r => r.message || []);
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
        // Collapsed/expanded state icon
        const expandIcon = `<span class="mr-2">${isExpanded ? '▼' : '▶'}</span>`;

        // Binary field formatter
        const formatYesNo = val => val === 'Yes' ? '<span class="text-success font-weight-bold">Yes</span>' : val === 'No' ? '<span class="text-danger font-weight-bold">No</span>' : '<span class="text-muted">—</span>';
        // Placeholder for empty fields
        const placeholder = '<span class="text-muted">—</span>';

        // Service Request link
        let serviceRequestLink = '';
        const userRoles = frappe.user_roles || [];
        const isOnlyDriver = userRoles.length === 1 && userRoles[0] === 'Driver';
        if (!isOnlyDriver && frappe.session && frappe.session.user && frappe.session.user !== 'Guest') {
            serviceRequestLink = `<a href="/app/service-request/${req.name}" target="_blank" rel="noopener noreferrer" class="font-weight-bold text-primary" aria-label="Open Service Request ${req.name} in new tab">${req.name}</a>`;
        } else if (isOnlyDriver) {
            serviceRequestLink = `<span class="font-weight-bold text-secondary" title="Not available for Driver-only users">${req.name}</span>`;
        } else {
            serviceRequestLink = `<span class="font-weight-bold text-secondary" title="Login to view">${req.name}</span>`;
        }
        // Customer Name
        const customerName = req.customer_name ? `<span class="font-weight-bold">${req.customer_name}</span>` : placeholder;

        // Google Maps link with icon, label
        let googleMapsLink = placeholder;
        if (req.google_maps_link) {
            googleMapsLink = `<a href="${req.google_maps_link}" target="_blank" rel="noopener noreferrer" class="text-primary font-weight-bold" aria-label="View on Map"><i class="fa fa-map-marker-alt mr-1"></i>View on Map</a>`;
        }

        // Add this function near the top, after other render helpers
        const renderServiceRequestInfoTable = (req) => {
            const driver = req.driver_suggestions || {};
            return `
                <div class="mb-2" style="border-bottom:1px solid #eee;">
                    <div class="mb-2 font-weight-bold text-secondary" style="font-size:1.15rem;">
                        <i class="fa fa-info-circle mr-1"></i>Service Request Info
                    </div>
                    <div class="table-responsive">
                        <table class="table table-sm table-bordered bg-white mb-0">
                            <thead>
                                <tr>
                                    <th>Field</th>
                                    <th>Original</th>
                                    <th>Driver Input</th>
                                </tr>
                            </thead>
                            <tbody>
                                <tr>
                                    <th>Electricity</th>
                                    <td>${req.electricity || '-'}</td>
                                    <td>
                                        <select class="form-control driver-info-electricity">
                                            <option value="">--</option>
                                            <option value="Yes" ${driver.electricity === 'Yes' ? 'selected' : ''}>Yes</option>
                                            <option value="No" ${driver.electricity === 'No' ? 'selected' : ''}>No</option>
                                        </select>
                                    </td>
                                </tr>
                                <tr>
                                    <th>Water</th>
                                    <td>${req.water || '-'}</td>
                                    <td>
                                        <select class="form-control driver-info-water">
                                            <option value="">--</option>
                                            <option value="Yes" ${driver.water === 'Yes' ? 'selected' : ''}>Yes</option>
                                            <option value="No" ${driver.water === 'No' ? 'selected' : ''}>No</option>
                                        </select>
                                    </td>
                                </tr>
                                <tr>
                                    <th>Parking</th>
                                    <td>${req.current_parking ? req.current_parking : (req.parking ? req.parking : '-')}</td>
                                    <td>
                                        <select class="form-control driver-info-parking">
                                            <option value="">--</option>
                                            <option value="Yes" ${driver.parking === 'Yes' ? 'selected' : ''}>Yes</option>
                                            <option value="No" ${driver.parking === 'No' ? 'selected' : ''}>No</option>
                                        </select>
                                    </td>
                                </tr>
                                <tr>
                                    <th>Living Space</th>
                                    <td>${req.living_space || '-'}</td>
                                    <td>
                                        <input type="text" class="form-control driver-info-living_space" value="${driver.living_space || ''}" />
                                    </td>
                                </tr>
                                <tr>
                                    <th>Living Space Notes</th>
                                    <td>${req.living_space_notes || '-'}</td>
                                    <td>
                                        <textarea class="form-control driver-info-living_space_notes" style="min-height:48px; resize:vertical; overflow:auto;">${driver.living_space_notes || ''}</textarea>
                                    </td>
                                </tr>
                                <tr>
                                    <th>Mobile</th>
                                    <td>
                                        ${req.mobile
                                            ? `<a href="tel:${req.mobile}" class="text-primary" aria-label="Call ${req.mobile}">${req.mobile}</a>`
                                            : '-'}
                                    </td>
                                    <td>
                                        <input type="text" class="form-control driver-info-mobile" value="${driver.mobile || ''}" />
                                    </td>
                                </tr>
                                <tr>
                                    <th>Google Maps</th>
                                    <td>
                                        ${req.google_maps_link
                                            ? `<a href="${req.google_maps_link}" target="_blank" rel="noopener noreferrer" aria-label="Google Maps Link">[Link]</a>`
                                            : '-'}
                                    </td>
                                    <td>
                                        <input type="text" class="form-control driver-info-google_maps_link" value="${driver.google_maps_link || ''}" />
                                    </td>
                                </tr>
                                <tr>
                                    <th>Territory</th>
                                    <td>${req.territory || '-'}</td>
                                    <td>
                                        <input type="text" class="form-control driver-info-territory" value="${driver.territory || ''}" />
                                    </td>
                                </tr>
                                <tr>
                                    <th>User Notes</th>
                                    <td>${req.user_notes || '-'}</td>
                                    <td>
                                        <textarea class="form-control driver-info-user_notes">${driver.user_notes || ''}</textarea>
                                    </td>
                                </tr>
                                <tr>
                                    <th>Total Pets</th>
                                    <td>${req.total_pets || '-'}</td>
                                    <td>
                                        <input type="number" class="form-control driver-info-total_pets" value="${driver.total_pets || ''}" min="0" />
                                    </td>
                                </tr>
                            </tbody>
                        </table>
                    </div>
                    <div class="d-flex justify-content-end mt-2">
                        <button type="button" class="btn btn-primary save-driver-info-btn" aria-label="Save Driver Info">Save</button>
                    </div>
                </div>
            `;
        };

        // --- Visit Verification & Inputs Section ---
        function renderVisitVerificationSection(req, tempInput = null) {
            const getRowClass = (erpVal, driverVal, label) => {
                const highlightFields = ['Electricity', 'Water', 'Parking', 'Living Space'];
                if (!highlightFields.includes(label)) return '';
                if (!driverVal || erpVal === driverVal) return '';
                return 'bg-[#FFF6D8]'; // Soft yellow background
            };
            const getWarnIcon = (erpVal, driverVal, label) => {
                const highlightFields = ['Electricity', 'Water', 'Parking', 'Living Space'];
                if (!highlightFields.includes(label)) return '';
                if (!driverVal || erpVal === driverVal) return '';
                return `<span aria-label="Changed" class="ml-2 text-yellow-600" title="Changed from original value">⚠️</span><span class="ml-2 text-xs text-orange-700 font-semibold">Changed from original value</span>`;
            };
            const formatYesNoIcon = val => val === 'Yes' ? '<span class="text-green-600 font-bold">Yes</span>' : val === 'No' ? '<span class="text-red-600 font-bold">No</span>' : '<span class="text-gray-400">—</span>';
            const placeholder = '<span class="text-gray-400">—</span>';
            const driver = tempInput || req.driver_suggestions || {};
            // Home Setup & Amenities
            const homeRows = [
                {
                    label: 'Electricity',
                    erp: formatYesNoIcon(req.electricity),
                    driver: `<select class="form-control driver-electricity" aria-label="Electricity" tabindex="0">
                        <option value="">--</option>
                        <option value="Yes" ${driver.electricity === 'Yes' ? 'selected' : ''}>Yes</option>
                        <option value="No" ${driver.electricity === 'No' ? 'selected' : ''}>No</option>
                    </select>`
                },
                {
                    label: 'Water',
                    erp: formatYesNoIcon(req.water),
                    driver: `<select class="form-control driver-water" aria-label="Water" tabindex="0">
                        <option value="">--</option>
                        <option value="Yes" ${driver.water === 'Yes' ? 'selected' : ''}>Yes</option>
                        <option value="No" ${driver.water === 'No' ? 'selected' : ''}>No</option>
                    </select>`
                },
                {
                    label: 'Parking',
                    erp: formatYesNoIcon(req.current_parking),
                    driver: `<select class="form-control driver-parking" aria-label="Parking" tabindex="0">
                        <option value="">--</option>
                        <option value="Yes" ${driver.parking === 'Yes' ? 'selected' : ''}>Yes</option>
                        <option value="No" ${driver.parking === 'No' ? 'selected' : ''}>No</option>
                    </select>`
                },
                {
                    label: 'Living Space',
                    erp: req.living_space ? `<span>${req.living_space}</span>` : placeholder,
                    driver: `<select class="form-control driver-living-space" aria-label="Living Space" tabindex="0">
                        <option value="">--</option>
                        <option value="Flat" ${driver.living_space === 'Flat' ? 'selected' : ''}>Flat</option>
                        <option value="House" ${driver.living_space === 'House' ? 'selected' : ''}>House</option>
                        <option value="Villa" ${driver.living_space === 'Villa' ? 'selected' : ''}>Villa</option>
                        <option value="Other" ${driver.living_space === 'Other' ? 'selected' : ''}>Other</option>
                    </select>`
                },
                {
                    label: 'Living Space Notes',
                    erp: req.living_space_notes ? `<span class="text-gray-400">${req.living_space_notes}</span>` : placeholder,
                    driver: `<textarea class="form-control driver-living-space-notes resize-y min-h-[32px]" aria-label="Living Space Notes" tabindex="0">${driver.living_space_notes || ''}</textarea>`
                },
            ];
            // Team
            const teamRows = [
                {
                    label: 'Groomer Name',
                    erp: placeholder,
                    driver: `<input type="text" class="form-control driver-groomer-name" aria-label="Groomer Name" tabindex="0" value="${driver.groomer || ''}" />`
                },
                {
                    label: 'Driver Name',
                    erp: placeholder,
                    driver: `<input type="text" class="form-control driver-driver-name" aria-label="Driver Name" tabindex="0" value="${driver.driver || ''}" />`
                },
            ];
            // Driver Notes
            const notesRow = {
                label: 'Driver Notes',
                erp: placeholder,
                driver: `<textarea class="form-control driver-notes resize-y min-h-[48px]" aria-label="Driver Notes" tabindex="0">${driver.notes || ''}</textarea>`
            };
            // Render rows
            const renderRows = (rows) => rows.map(row => {
                const erpVal = row.label === 'Electricity' ? req.electricity :
                    row.label === 'Water' ? req.water :
                    row.label === 'Parking' ? req.current_parking :
                    row.label === 'Living Space' ? req.living_space :
                    row.label === 'Living Space Notes' ? req.living_space_notes : '';
                const driverVal = row.label === 'Electricity' ? driver.electricity :
                    row.label === 'Water' ? driver.water :
                    row.label === 'Parking' ? driver.parking :
                    row.label === 'Living Space' ? driver.living_space :
                    row.label === 'Living Space Notes' ? driver.living_space_notes :
                    row.label === 'Groomer Name' ? driver.groomer :
                    row.label === 'Driver Name' ? driver.driver :
                    row.label === 'Driver Notes' ? driver.notes : '';
                return `<div class="grid grid-cols-3 gap-2 items-center py-2 px-2 border-b ${getRowClass(erpVal, driverVal, row.label)}" title="${erpVal !== driverVal && ['Electricity','Water','Parking','Living Space'].includes(row.label) ? 'Changed from original value' : ''}">
                    <div class="text-sm font-medium text-gray-700">${row.label}</div>
                    <div class="text-sm flex items-center">${row.erp}${getWarnIcon(erpVal, driverVal, row.label)}</div>
                    <div class="text-sm">${row.driver}</div>
                </div>`;
            }).join('');
            // Section wrappers
            return `
                <div class="bg-white rounded shadow p-2 mb-4 border border-gray-200">
                    <div class="font-bold text-lg mb-2 flex items-center gap-2 mt-4"><span class="mr-2">🔎</span>Visit Verification & Inputs</div>
                    <div class="mb-4">
                        <div class="font-semibold text-gray-600 mb-1">🏠 Home Setup & Amenities</div>
                        ${renderRows(homeRows)}
                    </div>
                    <div class="mb-4">
                        <div class="font-semibold text-gray-600 mb-1">👥 Team</div>
                        ${renderRows(teamRows)}
                    </div>
                    <div class="mb-4">
                        <div class="font-semibold text-gray-600 mb-1">📝 Driver Notes</div>
                        ${renderRows([notesRow])}
                    </div>
                    <div class="flex justify-end mt-6">
                        <button type="button" class="btn btn-primary w-full mt-3 py-2 text-lg font-bold save-verification-btn" aria-label="Save Visit Verification & Inputs">Save</button>
                    </div>
                </div>
            `;
        }

        // Pet Services
        let serviceItemsTable = '';
        if (req.service_items && req.service_items.length) {
            // Mobile: stack each row as a mini card
            const isMobile = window.innerWidth < 576;
            if (isMobile) {
                serviceItemsTable = `
                    <div class="mb-2" style="border-bottom:1px solid #eee;">
                        <div class="mb-2 font-weight-bold text-secondary" style="font-size:1.15rem;"><i class="fa fa-paw mr-1"></i>Pet Services</div>
                        <div class="d-flex flex-column gap-2">
                            ${req.service_items.map(item => `
                                <div class="border rounded bg-light p-2 mb-2">
                                    <div><span class="font-weight-bold">${frappe.utils.escape_html(item.pet_name || '')}</span> <span class="text-muted">(${frappe.utils.escape_html(item.pet_breed || '')})</span></div>
                                    <div class="small">Item: ${frappe.utils.escape_html(item.item_name || item.item_code || '')} | Qty: ${frappe.utils.escape_html(item.quantity || '')} | Amount: ${frappe.utils.escape_html(item.amount || '')}</div>
                                    <div class="small text-muted">Gender: ${frappe.utils.escape_html(item.pet_gender || '')} | Behaviour: ${frappe.utils.escape_html(item.pet_behaviour || '')} | Age: ${frappe.utils.escape_html(item.pet_age || '')} | Birthday: ${frappe.utils.escape_html(item.birthday || '')}</div>
                                    <div class="small text-muted">Notes: ${frappe.utils.escape_html(item.pet_notes || '')}</div>
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
                                        <th class="d-none d-md-table-cell" style="min-width:80px;">Behaviour</th><th class="d-none d-md-table-cell" style="min-width:40px;">Age</th><th class="d-none d-md-table-cell" style="min-width:100px;">Notes</th><th class="d-none d-md-table-cell" style="min-width:100px;">Birthday</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    ${req.service_items.map(item => `
                                        <tr>
                                            <td>${frappe.utils.escape_html(item.item_name || item.item_code || '')}</td>
                                            <td>${frappe.utils.escape_html(item.quantity || '')}</td>
                                            <td>${frappe.utils.escape_html(item.amount || '')}</td>
                                            <td>${frappe.utils.escape_html(item.pet_name || '')}</td>
                                            <td>${frappe.utils.escape_html(item.pet_breed || '')}</td>
                                            <td class="d-none d-md-table-cell">${frappe.utils.escape_html(item.pet_gender || '')}</td>
                                            <td class="d-none d-md-table-cell">${frappe.utils.escape_html(item.pet_behaviour || '')}</td>
                                            <td class="d-none d-md-table-cell">${frappe.utils.escape_html(item.pet_age || '')}</td>
                                            <td class="d-none d-md-table-cell">${frappe.utils.escape_html(item.pet_notes || '')}</td>
                                            <td class="d-none d-md-table-cell">${frappe.utils.escape_html(item.birthday || '')}</td>
                                        </tr>
                                    `).join('')}
                                </tbody>
                            </table>
                        </div>
                    </div>
                `;
            }
        }

        // --- Pet Details Table ---
        const renderUniquePetsTable = (req) => {
            // Extract unique pets by pet ID
            const uniquePets = {};
            (req.service_items || []).forEach(item => {
                if (item.pet && !uniquePets[item.pet]) {
                    uniquePets[item.pet] = item;
                }
            });
            const driverPetDetails = (req.driver_suggestions && req.driver_suggestions.pets) || {};
            const driverSuggestions = req.driver_suggestions || {};

            // Team/Notes section above table
            const teamSection = `
                <div class="mb-4 p-3 bg-gray-50 rounded border">
                    <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
                        <div>
                            <label class="block font-semibold mb-1" for="driver-name-${req.name}">Driver Name</label>
                            <input type="text" id="driver-name-${req.name}" class="form-control driver-info-driver" value="${driverSuggestions.driver || ''}" />
                        </div>
                        <div>
                            <label class="block font-semibold mb-1" for="groomer-name-${req.name}">Groomer Name</label>
                            <input type="text" id="groomer-name-${req.name}" class="form-control driver-info-groomer" value="${driverSuggestions.groomer || ''}" />
                        </div>
                        <div>
                            <label class="block font-semibold mb-1" for="driver-notes-${req.name}">Driver Notes</label>
                            <textarea id="driver-notes-${req.name}" class="form-control driver-info-notes">${driverSuggestions.notes || ''}</textarea>
                        </div>
                    </div>
                    <div class="flex justify-end mt-2">
                        <button type="button" class="btn btn-primary save-driver-info-btn" aria-label="Save Driver Info">Save</button>
                    </div>
                </div>
            `;

            return `
                ${teamSection}
                <div class="mb-2" style="border-bottom:1px solid #eee;">
                    <div class="mb-2 font-weight-bold text-secondary" style="font-size:1.15rem;">
                        <i class="fa fa-dog mr-1"></i>Pet Details
                    </div>
                    <div class="table-responsive">
                        <table class="table table-sm table-bordered bg-white mb-0">
                            <thead>
                                <tr>
                                    <th>Pet Name</th>
                                    <th>Breed</th>
                                    <th>Age</th>
                                    <th>Gender</th>
                                    <th>Behaviour</th>
                                    <th>Birthday</th>
                                    <th>Package</th>
                                    <th>Add On</th>
                                    <th>Amount</th>
                                    <th>Coat/Skin</th>
                                    <th>Ears</th>
                                    <th>Eyes</th>
                                    <th>Teeth</th>
                                    <th>Ticks</th>
                                    <th>Fleas</th>
                                    <th>Weight</th>
                                    <th>Groomer Comments</th>
                                    <th>Photos</th>
                                </tr>
                            </thead>
                            <tbody>
                                ${Object.values(uniquePets).map(pet => {
                                    const driverPet = driverPetDetails[pet.pet] || {};
                                    const photos = Array.isArray(driverPet.photos) ? driverPet.photos : (driverPet.photo ? [driverPet.photo] : []);
                                    return `
                                        <tr>
                                            <td><input type="text" class="form-control w-100 driver-pet-name" style="min-width:120px;max-width:200px;" maxlength="50" data-pet-id="${pet.pet}" value="${driverPet.name || pet.pet_name || ''}" /></td>
                                            <td><input type="text" class="form-control w-100 driver-pet-breed" style="min-width:120px;max-width:200px;" maxlength="50" data-pet-id="${pet.pet}" value="${driverPet.breed || pet.pet_breed || ''}" /></td>
                                            <td><input type="number" class="form-control w-100 driver-pet-age" style="min-width:80px;max-width:120px;" data-pet-id="${pet.pet}" value="${driverPet.age || pet.pet_age || ''}" min="0" /></td>
                                            <td>
                                                <select class="form-control w-100 driver-pet-gender" style="min-width:100px;max-width:140px;" data-pet-id="${pet.pet}">
                                                    <option value="">--</option>
                                                    <option value="Male" ${((driverPet.gender || pet.pet_gender) === 'Male') ? 'selected' : ''}>Male</option>
                                                    <option value="Female" ${((driverPet.gender || pet.pet_gender) === 'Female') ? 'selected' : ''}>Female</option>
                                                </select>
                                            </td>
                                            <td>
                                                <select class="form-control w-100 driver-pet-behaviour" style="min-width:120px;max-width:200px;" data-pet-id="${pet.pet}">
                                                    <option value="">--</option>
                                                    <option value="Calm" ${((driverPet.behaviour || pet.pet_behaviour) === 'Calm') ? 'selected' : ''}>Calm</option>
                                                    <option value="Aggressive" ${((driverPet.behaviour || pet.pet_behaviour) === 'Aggressive') ? 'selected' : ''}>Aggressive</option>
                                                    <option value="Anxious" ${((driverPet.behaviour || pet.pet_behaviour) === 'Anxious') ? 'selected' : ''}>Anxious</option>
                                                    <option value="Playful" ${((driverPet.behaviour || pet.pet_behaviour) === 'Playful') ? 'selected' : ''}>Playful</option>
                                                    <option value="Friendly" ${((driverPet.behaviour || pet.pet_behaviour) === 'Friendly') ? 'selected' : ''}>Friendly</option>
                                                </select>
                                            </td>
                                            <td><input type="date" class="form-control w-100 driver-pet-birthday" style="min-width:120px;max-width:200px;" data-pet-id="${pet.pet}" value="${driverPet.birthday || ''}" /></td>
                                            <td>
                                                <select class="form-control w-100 driver-pet-package" style="min-width:120px;max-width:200px;" data-pet-id="${pet.pet}">
                                                    <option value="">--</option>
                                                    <option value="Mini Groom" ${driverPet.package === 'Mini Groom' ? 'selected' : ''}>Mini Groom</option>
                                                    <option value="Full Groom" ${driverPet.package === 'Full Groom' ? 'selected' : ''}>Full Groom</option>
                                                    <option value="Mini Groom + Hygiene" ${driverPet.package === 'Mini Groom + Hygiene' ? 'selected' : ''}>Mini Groom + Hygiene</option>
                                                    <option value="Mini Groom + Zero Trim" ${driverPet.package === 'Mini Groom + Zero Trim' ? 'selected' : ''}>Mini Groom + Zero Trim</option>
                                                    <option value="Other" ${driverPet.package === 'Other' ? 'selected' : ''}>Other</option>
                                                </select>
                                            </td>
                                            <td>
                                                <select class="form-control w-100 driver-pet-addon" style="min-width:120px;max-width:200px;" data-pet-id="${pet.pet}">
                                                    <option value="">--</option>
                                                    <option value="Medicated Bath" ${driverPet.addon === 'Medicated Bath' ? 'selected' : ''}>Medicated Bath</option>
                                                    <option value="Nail Cutting" ${driverPet.addon === 'Nail Cutting' ? 'selected' : ''}>Nail Cutting</option>
                                                </select>
                                            </td>
                                            <td><input type="text" class="form-control w-100 driver-pet-amount" style="min-width:100px;max-width:140px;" maxlength="20" data-pet-id="${pet.pet}" value="${driverPet.amount || ''}" /></td>
                                            <td>
                                                <select class="form-control w-100 driver-pet-coat" style="min-width:120px;max-width:200px;" data-pet-id="${pet.pet}">
                                                    <option value="">--</option>
                                                    <option value="Healthy" ${driverPet.coat === 'Healthy' ? 'selected' : ''}>Healthy</option>
                                                    <option value="Dry" ${driverPet.coat === 'Dry' ? 'selected' : ''}>Dry</option>
                                                    <option value="Hair Loss" ${driverPet.coat === 'Hair Loss' ? 'selected' : ''}>Hair Loss</option>
                                                    <option value="Rashes" ${driverPet.coat === 'Rashes' ? 'selected' : ''}>Rashes</option>
                                                    <option value="Infection" ${driverPet.coat === 'Infection' ? 'selected' : ''}>Infection</option>
                                                </select>
                                            </td>
                                            <td>
                                                <select class="form-control w-100 driver-pet-ears" style="min-width:120px;max-width:200px;" data-pet-id="${pet.pet}">
                                                    <option value="">--</option>
                                                    <option value="Healthy" ${driverPet.ears === 'Healthy' ? 'selected' : ''}>Healthy</option>
                                                    <option value="Excessive Wax" ${driverPet.ears === 'Excessive Wax' ? 'selected' : ''}>Excessive Wax</option>
                                                    <option value="Infection" ${driverPet.ears === 'Infection' ? 'selected' : ''}>Infection</option>
                                                </select>
                                            </td>
                                            <td>
                                                <select class="form-control w-100 driver-pet-eyes" style="min-width:120px;max-width:200px;" data-pet-id="${pet.pet}">
                                                    <option value="">--</option>
                                                    <option value="Healthy" ${driverPet.eyes === 'Healthy' ? 'selected' : ''}>Healthy</option>
                                                    <option value="Discolored" ${driverPet.eyes === 'Discolored' ? 'selected' : ''}>Discolored</option>
                                                    <option value="Redness" ${driverPet.eyes === 'Redness' ? 'selected' : ''}>Redness</option>
                                                    <option value="Discharge" ${driverPet.eyes === 'Discharge' ? 'selected' : ''}>Discharge</option>
                                                </select>
                                            </td>
                                            <td>
                                                <select class="form-control w-100 driver-pet-teeth" style="min-width:120px;max-width:200px;" data-pet-id="${pet.pet}">
                                                    <option value="">--</option>
                                                    <option value="Healthy" ${driverPet.teeth === 'Healthy' ? 'selected' : ''}>Healthy</option>
                                                    <option value="Tartar" ${driverPet.teeth === 'Tartar' ? 'selected' : ''}>Tartar</option>
                                                    <option value="Broken" ${driverPet.teeth === 'Broken' ? 'selected' : ''}>Broken</option>
                                                    <option value="Discolored" ${driverPet.teeth === 'Discolored' ? 'selected' : ''}>Discolored</option>
                                                </select>
                                            </td>
                                            <td>
                                                <select class="form-control w-100 driver-pet-ticks" style="min-width:120px;max-width:200px;" data-pet-id="${pet.pet}">
                                                    <option value="">--</option>
                                                    <option value="None" ${driverPet.ticks === 'None' ? 'selected' : ''}>None</option>
                                                    <option value="Few" ${driverPet.ticks === 'Few' ? 'selected' : ''}>Few</option>
                                                    <option value="Infestation" ${driverPet.ticks === 'Infestation' ? 'selected' : ''}>Infestation</option>
                                                </select>
                                            </td>
                                            <td>
                                                <select class="form-control w-100 driver-pet-fleas" style="min-width:120px;max-width:200px;" data-pet-id="${pet.pet}">
                                                    <option value="">--</option>
                                                    <option value="None" ${driverPet.fleas === 'None' ? 'selected' : ''}>None</option>
                                                    <option value="Few" ${driverPet.fleas === 'Few' ? 'selected' : ''}>Few</option>
                                                    <option value="Infestation" ${driverPet.fleas === 'Infestation' ? 'selected' : ''}>Infestation</option>
                                                </select>
                                            </td>
                                            <td>
                                                <select class="form-control w-100 driver-pet-weight" style="min-width:120px;max-width:200px;" data-pet-id="${pet.pet}">
                                                    <option value="">--</option>
                                                    <option value="Ideal" ${driverPet.weight === 'Ideal' ? 'selected' : ''}>Ideal</option>
                                                    <option value="Overweight" ${driverPet.weight === 'Overweight' ? 'selected' : ''}>Overweight</option>
                                                    <option value="Underweight" ${driverPet.weight === 'Underweight' ? 'selected' : ''}>Underweight</option>
                                                </select>
                                            </td>
                                            <td><input type="text" class="form-control w-100 driver-pet-groomer-comments" style="min-width:120px;max-width:200px;" maxlength="100" data-pet-id="${pet.pet}" value="${driverPet.groomer_comments || ''}" /></td>
                                    <td>
                                        <input type="file" accept="image/*" multiple class="pet-photo-input" data-pet-id="${pet.pet}" style="display:block;" />
                                        <button type="button" class="btn btn-primary save-pet-photo-btn mt-2" data-pet-id="${pet.pet}" data-session-id="${req.name}">Save</button>
                                        <div class="pet-photo-links mt-2" data-pet-id="${pet.pet}">
                                            ${renderPetPhotos(req.pet_photos, pet.pet, req.name)}
                                        </div>
                                    </td>
                                </tr>
                            `;
                        }).join('')}
                    </tbody>
                </table>
            </div>
            <div class="d-flex justify-content-end mt-2">
                <button type="button" class="btn btn-primary save-driver-pet-details-btn" aria-label="Save Pet Details">Save</button>
            </div>
        </div>
    `;
};

// Add Payment Details section below all tables in renderCard:
const renderPaymentDetailsSection = (req) => {
    const driverSuggestions = req.driver_suggestions || {};
    return `
        <div class="mb-2" style="border-bottom:1px solid #eee;">
            <div class="mb-2 font-weight-bold text-secondary" style="font-size:1.15rem;">
                <i class="fa fa-money-bill mr-1"></i>Payment Details
            </div>
            <div class="row">
                <div class="col-12 col-md-4 mb-2">
                    <label>Travel Cost</label>
                    <input type="text" class="form-control driver-travel-cost" value="${driverSuggestions.travel_cost || ''}" />
                </div>
                <div class="col-12 col-md-4 mb-2">
                    <label>Total Amount Paid</label>
                    <input type="text" class="form-control driver-total-amount-paid" value="${driverSuggestions.total_amount_paid || ''}" />
                </div>
                <div class="col-12 col-md-4 mb-2">
                    <label>Payment Method</label>
                    <select class="form-control driver-payment-method">
                        <option value="">--</option>
                        <option value="UPI" ${driverSuggestions.payment_method === 'UPI' ? 'selected' : ''}>UPI</option>
                        <option value="Cash" ${driverSuggestions.payment_method === 'Cash' ? 'selected' : ''}>Cash</option>
                        <option value="Payment not made" ${driverSuggestions.payment_method === 'Payment not made' ? 'selected' : ''}>Payment not made</option>
                        <option value="UPI and Cash" ${driverSuggestions.payment_method === 'UPI and Cash' ? 'selected' : ''}>UPI and Cash</option>
                    </select>
                </div>
            </div>
            <div class="d-flex justify-content-end mt-2">
                <button type="button" class="btn btn-primary save-driver-payment-btn" aria-label="Save Payment Details">Save</button>
            </div>
        </div>
    `;
};

// --- Card Header (collapsible) ---
const cardHeader = `
    <div class="d-flex flex-row align-items-center w-100" style="min-height:48px;">
        <span class="expand-icon" style="font-size:1.2em;cursor:pointer;">${expandIcon}</span>
        <span class="font-weight-bold mr-2">${customerName}</span>
        <span class="font-weight-bold text-primary mr-2">${serviceRequestLink}</span>
        <span class="font-weight-bold mr-2 ml-auto">${req.scheduled_date} ${formatTime(req.scheduled_date_start)}</span>
        <span class="font-weight-bold mr-2">${req.status}</span>
        ${isSaved ? '<i class="fa fa-check-circle text-success ml-2" aria-label="Saved"></i>' : ''}
    </div>
`;

// Collapsible card logic
const cardBody = `
    ${renderDriverSummary(req)}
    ${serviceItemsTable}
    ${renderServiceRequestInfoTable(req)}
    ${renderUniquePetsTable(req)}
    ${renderPaymentDetailsSection(req)}
    ${renderVisitVerificationSection(req, tempDriverInputs[req.name])}
`;
const card = `
    <div class="card mb-4 ${cardHighlight}" data-session-id="${req.name}" ${cardContainerBg}>
        <div class="card-header bg-white d-flex align-items-center" style="cursor:pointer; border-bottom:1px solid #eee;" tabindex="0" data-toggle="collapse" data-target="#collapse-${req.name}" aria-expanded="false" aria-controls="collapse-${req.name}">
            ${cardHeader}
        </div>
        <div id="collapse-${req.name}" class="collapse">
            <div class="card-body">
                ${cardBody}
            </div>
        </div>
    </div>
`;
// After rendering, fetch customer type if missing
setTimeout(() => {
    const $card = $(`[data-session-id='${req.name}']`);
    fetchAndSetCustomerType(req, $card);
    fetchAndSetCustomerContacts(req, $card);
}, 0);
return card;
}

// Render all cards
function renderCards() {
    if (filteredRequests.length === 0) {
        return `<div class="alert alert-info mt-4">No grooming sessions found.</div>`;
    }
    return filteredRequests.map(renderCard).join('');
}

// Render progress tracker (sticky)
function renderProgress() {
    const total = groomingRequests.length;
    const done = savedIds.size;
    return `<div class="sticky-top bg-white py-2 mb-3 shadow-sm rounded d-flex align-items-center" style="z-index:20; border-bottom:1px solid #eee;"><span class="font-weight-bold">${done} of ${total} sessions updated</span></div>`;
}

// Main render
async function renderAll() {
    await fetchData();
    $root.html(`
        ${renderDatePicker()}
        <div id="progress-tracker">${renderProgress()}</div>
        <div id="grooming-cards">${renderCards()}</div>
    `);
    bindEvents();
}

// Bind events
function bindEvents() {
    // Collapsible card expand/collapse
    $('.card-header').on('click keydown', function(e) {
        if (e.type === 'click' || e.key === 'Enter' || e.key === ' ') {
            const $header = $(this);
            const $card = $header.closest('.card');
            const $collapse = $card.find('.collapse');
            const expanded = $collapse.hasClass('show');
            // Collapse all others
            $('.collapse').collapse('hide');
            if (!expanded) {
                $collapse.collapse('show');
            }
        }
    });

    // Save verification
    $('.save-verification-btn').off('click').on('click', async function() {
        const $card = $(this).closest('.card');
        const sessionId = $card.data('session-id');
        const $section = $card.find('.bg-white.rounded.shadow');
        const electricity = $section.find('.driver-electricity').val();
        const water = $section.find('.driver-water').val();
        const parking = $section.find('.driver-parking').val();
        const livingSpace = $section.find('.driver-living-space').val();
        const livingSpaceNotes = $section.find('.driver-living-space-notes').val();
        const groomerName = $section.find('.driver-groomer-name').val();
        const driverName = $section.find('.driver-driver-name').val();
        const notes = $section.find('.driver-notes').val();
        if (!parking) {
            frappe.show_alert({message: "Please select Parking.", indicator: "orange"});
            return;
        }
        const $btn = $(this);
        $btn.prop('disabled', true);
        $btn.after('<span class="spinner-border spinner-border-sm ml-2"></span>');
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
            await frappe.call('petcare.petcare.page.grooming_data_entry.grooming_data_entry.save_driver_suggestion', {
                service_request_id: sessionId,
                driver_suggestions: JSON.stringify(suggestion)
            });
            savedIds.add(sessionId);
            delete tempDriverInputs[sessionId];
            frappe.show_alert({message: "Visit verification saved!", indicator: "green"});
            // No re-render
        } catch (err) {
            frappe.show_alert({message: "Failed to save.", indicator: "red"});
        } finally {
            $btn.prop('disabled', false);
            $section.find('.spinner-border').remove();
        }
    });

    // Date picker event
    $('#grooming-date-picker').on('change', function() {
        selectedDate = this.value;
        renderAll();
    });

    // Live change detection for the four fields
    $('.driver-electricity, .driver-water, .driver-parking, .driver-living-space').off('change').on('change', function() {
        const $card = $(this).closest('.card');
        const sessionId = $card.data('session-id');
        // Get all current values from the section
        const $section = $card.find('.bg-white.rounded.shadow');
        tempDriverInputs[sessionId] = {
            electricity: $section.find('.driver-electricity').val(),
            water: $section.find('.driver-water').val(),
            parking: $section.find('.driver-parking').val(),
            living_space: $section.find('.driver-living-space').val(),
            living_space_notes: $section.find('.driver-living-space-notes').val(),
            groomer: $section.find('.driver-groomer-name').val(),
            driver: $section.find('.driver-driver-name').val(),
            notes: $section.find('.driver-notes').val(),
        };
        // Re-render just the Visit Verification section
        $section.replaceWith(renderVisitVerificationSection(groomingRequests.find(r => r.name === sessionId), tempDriverInputs[sessionId]));
        // Re-bind events for the new section
        bindEvents();
    });

    // Add event for driver info save
    $('.save-driver-info-btn').off('click').on('click', async function() {
        const $card = $(this).closest('.card');
        const sessionId = $card.data('session-id');
        const driverName = $card.find('.driver-info-driver').val();
        const groomerName = $card.find('.driver-info-groomer').val();
        const driverNotes = $card.find('.driver-info-notes').val();
        // Update driver_suggestions
        const req = groomingRequests.find(r => r.name === sessionId);
        if (!req.driver_suggestions) req.driver_suggestions = {};
        req.driver_suggestions.driver = driverName;
        req.driver_suggestions.groomer = groomerName;
        req.driver_suggestions.notes = driverNotes;
        try {
            await frappe.call('petcare.petcare.page.grooming_data_entry.grooming_data_entry.save_driver_suggestion', {
                service_request_id: sessionId,
                driver_suggestions: JSON.stringify(req.driver_suggestions)
            });
            frappe.show_alert({message: "Driver info saved!", indicator: "green"});
            // No re-render
        } catch (err) {
            frappe.show_alert({message: "Failed to save driver info.", indicator: "red"});
        }
    });

    // Add event for pet details save
    $('.save-driver-pet-details-btn').off('click').on('click', async function() {
        const $card = $(this).closest('.card');
        const sessionId = $card.data('session-id');
        // Collect all pet input values
        const pets = {};
        $card.find('tbody tr').each(function() {
            const $row = $(this);
            const petId = $row.find('.driver-pet-name').data('pet-id');
            if (!petId) return;
            pets[petId] = {
                name: $row.find('.driver-pet-name').val(),
                breed: $row.find('.driver-pet-breed').val(),
                age: $row.find('.driver-pet-age').val(),
                gender: $row.find('.driver-pet-gender').val(),
                behaviour: $row.find('.driver-pet-behaviour').val(),
                birthday: $row.find('.driver-pet-birthday').val(),
                package: $row.find('.driver-pet-package').val(),
                addon: $row.find('.driver-pet-addon').val(),
                amount: $row.find('.driver-pet-amount').val(),
                coat: $row.find('.driver-pet-coat').val(),
                ears: $row.find('.driver-pet-ears').val(),
                eyes: $row.find('.driver-pet-eyes').val(),
                teeth: $row.find('.driver-pet-teeth').val(),
                ticks: $row.find('.driver-pet-ticks').val(),
                fleas: $row.find('.driver-pet-fleas').val(),
                weight: $row.find('.driver-pet-weight').val(),
                groomer_comments: $row.find('.driver-pet-groomer-comments').val(),
            };
        });
        // Merge into driver_suggestions
        const req = groomingRequests.find(r => r.name === sessionId);
        req.driver_suggestions = req.driver_suggestions || {};
        req.driver_suggestions.pets = pets;
        const $btn = $(this);
        $btn.prop('disabled', true);
        $btn.after('<span class="spinner-border spinner-border-sm ml-2"></span>');
        try {
            await frappe.call('petcare.petcare.page.grooming_data_entry.grooming_data_entry.save_driver_suggestion', {
                service_request_id: sessionId,
                driver_suggestions: JSON.stringify(req.driver_suggestions)
            });
            frappe.show_alert({message: "Pet details saved!", indicator: "green"});
            // No re-render
        } catch (err) {
            frappe.show_alert({message: "Failed to save pet details.", indicator: "red"});
        } finally {
            $btn.prop('disabled', false);
            $card.find('.spinner-border').remove();
        }
    });

    // Add event handler for save-driver-payment-btn
    $('.save-driver-payment-btn').off('click').on('click', async function() {
        const $card = $(this).closest('.card');
        const sessionId = $card.data('session-id');
        const travelCost = $card.find('.driver-travel-cost').val();
        const totalAmountPaid = $card.find('.driver-total-amount-paid').val();
        const paymentMethod = $card.find('.driver-payment-method').val();
        // Merge into driver_suggestions
        const req = groomingRequests.find(r => r.name === sessionId);
        req.driver_suggestions = req.driver_suggestions || {};
        req.driver_suggestions.travel_cost = travelCost;
        req.driver_suggestions.total_amount_paid = totalAmountPaid;
        req.driver_suggestions.payment_method = paymentMethod;
        const $btn = $(this);
        $btn.prop('disabled', true);
        $btn.after('<span class="spinner-border spinner-border-sm ml-2"></span>');
        try {
            await frappe.call('petcare.petcare.page.grooming_data_entry.grooming_data_entry.save_driver_suggestion', {
                service_request_id: sessionId,
                driver_suggestions: JSON.stringify(req.driver_suggestions)
            });
            frappe.show_alert({message: "Payment details saved!", indicator: "green"});
            // No re-render
        } catch (err) {
            frappe.show_alert({message: "Failed to save payment details.", indicator: "red"});
        } finally {
            $btn.prop('disabled', false);
            $card.find('.spinner-border').remove();
        }
    });

    // Pet photo upload handler (multiple)
    $('.pet-photo-input').off('change').on('change', async function() {
        const files = Array.from(this.files);
        const $card = $(this).closest('.card');
        const sessionId = $card.data('session-id');
        const petId = $(this).data('pet-id');
        if (!files.length || !petId) return;
        const $input = $(this);
        $input.prop('disabled', true);
        $input.after('<span class="spinner-border spinner-border-sm ml-2 photo-upload-spinner"></span>');
        let uploadedUrls = [];
        for (const file of files) {
            const formData = new FormData();
            formData.append('file', file);
            formData.append('is_private', 0);
            const res = await fetch('/api/method/upload_file', {
                method: 'POST',
                body: formData,
                headers: { 'X-Frappe-CSRF-Token': frappe.csrf_token }
            });
            const data = await res.json();
            if (data.message && data.message.file_url) {
                uploadedUrls.push(data.message.file_url);
            }
        }
        // Now call backend to add to child table
        await frappe.call('petcare.petcare.page.grooming_data_entry.grooming_data_entry.upload_images_to_pet_photos', {
            service_request_id: sessionId,
            pet_id: petId,
            image_urls: uploadedUrls
        });
        frappe.show_alert({message: 'Photo(s) uploaded!', indicator: 'green'});
        // Fetch updated pet_photos for this session and update only the photo links section
        const updatedReq = await frappe.call('petcare.petcare.page.grooming_data_entry.grooming_data_entry.get_grooming_request', {
            service_request_id: sessionId
        }).then(r => r.message || {});
        const $links = $card.find(`.pet-photo-links[data-pet-id='${petId}']`);
        $links.html(renderPetPhotos(updatedReq.pet_photos, petId, sessionId));
        $input.prop('disabled', false);
        $input.after('<span class="spinner-border spinner-border-sm ml-2 photo-upload-spinner"></span>');
        $input.after('<span class="spinner-border spinner-border-sm ml-2 photo-upload-spinner"></span>');
    });

    // Pet photo delete handler (refactored, by URL)
    function bindPhotoDeleteHandler($context) {
        $context.find('.driver-pet-photo-delete').off('click keydown').on('click keydown', async function(e) {
            if (e.type === 'click' || e.key === 'Enter' || e.key === ' ') {
                const $btn = $(this);
                const $card = $btn.closest('.card');
                const sessionId = $card.data('session-id');
                const petId = $btn.data('pet-id');
                const photoUrl = decodeURIComponent($btn.data('photo-url'));
                $btn.prop('disabled', true);
                $btn.after('<span class="spinner-border spinner-border-sm ml-2 photo-delete-spinner"></span>');
                try {
                    // Fetch latest driver_suggestions from backend
                    const latestReq = await frappe.call('petcare.petcare.page.grooming_data_entry.grooming_data_entry.get_grooming_request', {
                        service_request_id: sessionId
                    }).then(r => r.message || {});
                    let driverSuggestions = latestReq.driver_suggestions || {};
                    if (!driverSuggestions.pets) driverSuggestions.pets = {};
                    if (!driverSuggestions.pets[petId]) driverSuggestions.pets[petId] = {};
                    let photos = Array.isArray(driverSuggestions.pets[petId].photos) ? driverSuggestions.pets[petId].photos : [];
                    photos = photos.filter(url => url !== photoUrl);
                    driverSuggestions.pets[petId].photos = photos;
                    await frappe.call('petcare.petcare.page.grooming_data_entry.grooming_data_entry.save_driver_suggestion', {
                        service_request_id: sessionId,
                        driver_suggestions: JSON.stringify(driverSuggestions)
                    });
                    // Re-fetch latest after save
                    const updatedReq = await frappe.call('petcare.petcare.page.grooming_data_entry.grooming_data_entry.get_grooming_request', {
                        service_request_id: sessionId
                    }).then(r => r.message || {});
                    const updatedPhotos = (updatedReq.driver_suggestions && updatedReq.driver_suggestions.pets && updatedReq.driver_suggestions.pets[petId] && updatedReq.driver_suggestions.pets[petId].photos) || [];
                    frappe.show_alert({message: "Photo deleted!", indicator: "orange"});
                    // Update only the thumbnails section for this pet
                    const $thumbs = $card.find(`.pet-photo-links[data-pet-id='${petId}']`);
                    $thumbs.html(updatedPhotos.map((url, idx) => `
                        <a href="${url}" target="_blank" rel="noopener noreferrer" class="text-xs text-blue-600 underline break-all mt-1 select-all mr-2 mb-2" tabindex="0" aria-label="Pet Image URL">${url.split('/').pop()}</a>`).join(''));
                    // Re-bind delete handler for new thumbnails
                    bindPhotoDeleteHandler($card);
                    // If the Service Request form is open, reload it to reflect the new image in driver suggestions
                    if (window.cur_frm && cur_frm.doctype === 'Service Request' && cur_frm.doc.name === sessionId) {
                        cur_frm.reload_doc();
                    }
                } catch (err) {
                    frappe.show_alert({message: "Failed to delete photo.", indicator: "red"});
                } finally {
                    $btn.prop('disabled', false);
                    $card.find('.photo-delete-spinner').remove();
                }
            }
        });
    }
    // Initial bind for delete handler
    bindPhotoDeleteHandler($(document));
}

// Helper to fetch customer type if missing (client-side only)
async function fetchAndSetCustomerType(req, $card) {
    if (!req.customer_type && req.customer) {
        const count = await frappe.db.count('Service Request', {
            filters: {
                customer: req.customer,
                status: 'Completed'
            }
        });
        req.customer_type = count > 0 ? 'Repeat Customer' : 'First-Time Customer';
        if ($card) {
            $card.replaceWith(renderCard(req));
            bindEvents();
        }
    }
}

// Helper to fetch all customer contacts if missing
async function fetchAndSetCustomerContacts(req, $card) {
    if ((!req.customer_contacts || req.customer_contacts.length === 0) && req.customer) {
        // Get all contacts linked to this customer
        const contacts = await frappe.db.get_list('Contact', {
            filters: [
                ['Dynamic Link', 'link_doctype', '=', 'Customer'],
                ['Dynamic Link', 'link_name', '=', req.customer]
            ],
            fields: ['first_name', 'mobile_no', 'phone']
        });
        // Format as: Name (mobile) or Name (phone)
        req.customer_contacts = contacts
            .filter(c => c.mobile_no || c.phone)
            .map(c => `${c.first_name || 'Customer'} (${c.mobile_no || c.phone})`)
            .join(', ') || '-';
        // Re-render the card with updated contacts
        if ($card) {
            $card.replaceWith(renderCard(req));
            bindEvents();
        }
    }
}

// Helper to render pet photos from child table, with delete button
function renderPetPhotos(petPhotos, petId, sessionId) {
    if (!Array.isArray(petPhotos)) return '';
    return petPhotos
        .filter(photo => photo.pet === petId)
        .map(photo => {
            const url = photo.image;
            const parts = url.split('/');
            const filename = parts[parts.length - 1];
            return `<span class="inline-flex items-center gap-2 mr-2 mb-2">
                <a href="${url}" target="_blank" rel="noopener noreferrer" class="text-xs text-blue-600 underline break-all select-all" tabindex="0" aria-label="Pet Image URL">${filename}</a>
                <button type="button" class="btn btn-danger btn-xs delete-pet-photo-btn" data-photo-row-id="${photo.name}" data-session-id="${sessionId}" title="Delete Photo">🗑️</button>
            </span>`;
        })
        .join('');
}

// Initial render
renderAll();
};

// Helper to format time from datetime string
function formatTime(datetimeStr) {
    if (!datetimeStr) return '-';
    // Accepts formats like '13-05-2025 16:30:00' or '13-05-2025 16:30'
    const match = datetimeStr.match(/\d{2}-\d{2}-\d{4} (\d{2}):(\d{2})/);
    if (match) {
        let hour = parseInt(match[1], 10);
        const minute = match[2];
        const ampm = hour >= 12 ? 'PM' : 'AM';
        const hour12 = hour % 12 === 0 ? 12 : hour % 12;
        return `${hour12}:${minute} ${ampm}`;
    }
    return '-';
}

const renderDriverSummary = (req) => {
    // Show discount and total amount directly from req, with rupee symbol
    const discountSection = req.discount_amount ? `
        <div><b>Discount Applied:</b> ₹${req.discount_amount}</div>
        <div><b>Final Amount:</b> <span class="font-weight-bold">₹${req.amount_after_discount || '-'}</span></div>
    ` : '';
    // Format contacts as click-to-call
    let contactsDisplay = '-';
    if (Array.isArray(req.customer_contacts)) {
        contactsDisplay = req.customer_contacts.map(c => {
            const match = c.match(/\((\d{7,})\)/); // match (number)
            if (match) {
                const number = match[1];
                return c.replace(number, `<a href=\"tel:${number}\" class=\"text-primary\">${number}</a>`);
            }
            return c;
        }).join(', ');
    } else if (typeof req.customer_contacts === 'string') {
        contactsDisplay = req.customer_contacts.replace(/(\d{7,})/g, '<a href=\"tel:$1\" class=\"text-primary\">$1</a>');
    }
    return `
        <div class="card mb-3 p-3" style="background:#f8fafc;">
            <div class="mb-2 font-weight-bold text-lg">
                Customer: ${req.customer_name || '-'} <span class="badge badge-info">${req.customer_type || '-'}</span>
            </div>
            <div><b>Service Notes:</b> ${req.service_notes || '-'}</div>
            <div><b>Date:</b> ${req.scheduled_date || '-'} <b>Time:</b> ${formatTime(req.scheduled_date_start)}</div>
            <div><b>Location:</b> ${req.territory || '-'}</div>
            <div><b>Google Maps:</b> ${req.google_maps_link ? `<a href=\"${req.google_maps_link}\" target=\"_blank\">[Link]</a>` : '-'}</div>
            <div><b>Living Space:</b> ${req.living_space || '-'} </div>
            <div><b>Parking:</b> ${req.parking || '-'} <b>Electricity:</b> ${req.electricity || '-'} <b>Water:</b> ${req.water || '-'}</div>
            <div><b>Total Pets:</b> ${req.total_pets || '-'}</div>
            <div><b>Total Amount:</b> ₹${req.total_amount || '-'}</div>
            ${discountSection}
            <div><b>Customer Contact Numbers:</b> ${contactsDisplay}</div>
        </div>
    `;
}; 