frappe.ui.form.on('Service Request', {
    refresh(frm) {
        let suggestions = {};
        try {
            suggestions = frm.doc.driver_suggestions ? JSON.parse(frm.doc.driver_suggestions) : {};
        } catch (e) {
            suggestions = {};
        }

        // Define all fields to show
        const fields = [
            { key: 'electricity', label: 'Electricity', erp: frm.doc.electricity },
            { key: 'water', label: 'Water', erp: frm.doc.water },
            { key: 'parking', label: 'Parking', erp: frm.doc.current_parking },
            { key: 'living_space', label: 'Living Space', erp: frm.doc.living_space },
            { key: 'living_space_notes', label: 'Living Space Notes', erp: frm.doc.living_space_notes },
            { key: 'groomer', label: 'Groomer Name', erp: frm.doc.groomer },
            { key: 'driver', label: 'Driver Name', erp: frm.doc.driver },
            { key: 'notes', label: 'Driver Notes', erp: frm.doc.driver_notes },
            { key: 'travel_cost', label: 'Travel Cost', erp: frm.doc.travel_cost },
            { key: 'total_amount_paid', label: 'Total Amount Paid', erp: frm.doc.total_amount_paid },
            { key: 'payment_method', label: 'Payment Method', erp: frm.doc.payment_method }
        ];

        // Helper to show warning if suggestion differs from ERP
        const getWarn = (val, erp) => (val && erp && val !== erp) ? 
            ' <span aria-label="Changed" class="text-amber-600">⚠️</span>' : '';

        // Build HTML for all fields (always show all)
        let html = `<div class="grid grid-cols-1 md:grid-cols-2 gap-x-8 gap-y-4">`;
        fields.forEach(f => {
            const suggestionVal = suggestions[f.key];
            const erpVal = f.erp;
            const value = suggestionVal !== undefined && suggestionVal !== null && suggestionVal !== '' 
                ? suggestionVal 
                : (erpVal !== undefined && erpVal !== null && erpVal !== '' ? erpVal : '-');
            const warn = getWarn(suggestionVal, erpVal);

            // For notes fields, span both columns
            const colSpan = (f.key === 'living_space_notes' || f.key === 'notes') ? 'md:col-span-2' : '';
            html += `
                <div class="flex flex-col ${colSpan}">
                    <span class="font-semibold text-gray-700">${f.label}:</span>
                    <span class="mt-1 px-2 py-1 rounded bg-gray-100 text-gray-800 inline-block" tabindex="0" aria-label="${f.label}">
                        ${frappe.utils.escape_html(value)}${warn}
                    </span>
                </div>
            `;
        });
        html += `</div>`;

        // Pet details (always show if suggestions.pets exists, else skip)
        if (suggestions.pets && typeof suggestions.pets === 'object') {
            Object.values(suggestions.pets).forEach((pet, idx) => {
                let photoArr = [];
                if (Array.isArray(pet.photos)) {
                    photoArr = pet.photos;
                } else if (typeof pet.photos === 'string' && pet.photos.trim().length > 0) {
                    try {
                        const parsed = JSON.parse(pet.photos);
                        if (Array.isArray(parsed)) {
                            photoArr = parsed;
                        } else {
                            photoArr = [pet.photos];
                        }
                    } catch {
                        photoArr = [pet.photos];
                    }
                }

                html += `
                    <div class="mt-6 p-4 rounded-lg bg-gray-50 border border-gray-200" tabindex="0" aria-label="Pet Details">
                        <div class="font-semibold text-lg mb-2 text-gray-800">Pet ${pet.name ? frappe.utils.escape_html(pet.name) : idx + 1}</div>
                        <div class="flex flex-wrap gap-3">
                            <span class="text-gray-700">Breed: ${frappe.utils.escape_html(pet.breed || '-')}</span>
                            <span class="text-gray-700">Age: ${frappe.utils.escape_html(pet.age || '-')}</span>
                            <span class="text-gray-700">Gender: ${frappe.utils.escape_html(pet.gender || '-')}</span>
                            <span class="text-gray-700">Behaviour: ${frappe.utils.escape_html(pet.behaviour || '-')}</span>
                            <span class="text-gray-700">Birthday: ${frappe.utils.escape_html(pet.birthday || '-')}</span>
                            <span class="text-gray-700">Package: ${frappe.utils.escape_html(pet.package || '-')}</span>
                            <span class="text-gray-700">Add On: ${frappe.utils.escape_html(pet.addon || '-')}</span>
                            <span class="text-gray-700">Amount: ${frappe.utils.escape_html(pet.amount || '-')}</span>
                            <span class="text-gray-700">Coat/Skin: ${frappe.utils.escape_html(pet.coat || '-')}</span>
                            <span class="text-gray-700">Ears: ${frappe.utils.escape_html(pet.ears || '-')}</span>
                            <span class="text-gray-700">Eyes: ${frappe.utils.escape_html(pet.eyes || '-')}</span>
                            <span class="text-gray-700">Teeth: ${frappe.utils.escape_html(pet.teeth || '-')}</span>
                            <span class="text-gray-700">Ticks: ${frappe.utils.escape_html(pet.ticks || '-')}</span>
                            <span class="text-gray-700">Fleas: ${frappe.utils.escape_html(pet.fleas || '-')}</span>
                            <span class="text-gray-700">Weight: ${frappe.utils.escape_html(pet.weight || '-')}</span>
                            <span class="text-gray-700">Groomer Comments: ${frappe.utils.escape_html(pet.groomer_comments || '-')}</span>
                            ${
                                photoArr.length
                                ? photoArr.map(url => {
                                    const parts = url.split('/');
                                    const filename = parts[parts.length - 1];
                                    return `<a href="${frappe.utils.escape_html(url)}" target="_blank" rel="noopener noreferrer" class="text-xs text-blue-600 underline break-all mt-1 select-all mr-2 mb-2" tabindex="0" aria-label="Pet Image URL">${frappe.utils.escape_html(filename)}</a>`;
                                }).join('')
                                : ''
                            }
                        </div>
                    </div>
                `;
            });
        }

        // If no suggestions and no ERP data, show a message
        if (!frm.doc.driver_suggestions && !Object.values(frm.doc).some(val => val)) {
            html = '<span class="text-gray-400">No driver suggestions or data available.</span>';
        }

        // Render in the wrapper
        frm.fields_dict.driver_suggestions_display.$wrapper.html(`
            <div class="p-4">${html}</div>
        `);

        // Pet Photos Section (for each pet row)
        if (frm.doc.pet_details && Array.isArray(frm.doc.pet_details)) {
            frm.doc.pet_details.forEach((pet, idx) => {
                const petRowId = `pet-photo-row-${idx}`;
                const $row = $(`tr[data-idx='${idx + 1}']`);
                if ($row.length) {
                    $row.find('.pet-photo-upload-cell').remove();
                    $row.append(`
                        <td class="pet-photo-upload-cell">
                            <input type="file" accept="image/*" multiple class="pet-photo-input" data-pet-id="${pet.pet}" style="display:block;" />
                            <button type="button" class="btn btn-primary save-pet-photo-btn mt-2" data-pet-id="${pet.pet}" data-session-id="${frm.doc.name}">Save</button>
                            <div class="pet-photo-links mt-2" data-pet-id="${pet.pet}">
                                ${renderPetPhotos(frm.doc.pet_photos, pet.pet, frm.doc.name)}
                            </div>
                        </td>
                    `);
                }
            });
        }

        // Save photo button
        $(document).off('click', '.save-pet-photo-btn').on('click', '.save-pet-photo-btn', async function() {
            const $btn = $(this);
            const petId = $btn.data('pet-id');
            const sessionId = $btn.data('session-id');
            const $row = $btn.closest('tr');
            const files = $row.find('.pet-photo-input')[0].files;
            if (!files.length) {
                frappe.show_alert({message: 'Please select a photo to upload.', indicator: 'orange'});
                return;
            }
            $btn.prop('disabled', true);
            $btn.after('<span class="spinner-border spinner-border-sm ml-2 photo-upload-spinner"></span>');
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
            const $links = $row.find('.pet-photo-links');
            $links.html(renderPetPhotos(updatedReq.pet_photos, petId, sessionId));
            $btn.prop('disabled', false);
            $row.find('.photo-upload-spinner').remove();
        });

        // Delete photo button
        $(document).off('click', '.delete-pet-photo-btn').on('click', '.delete-pet-photo-btn', async function() {
            const $btn = $(this);
            const photoRowId = $btn.data('photo-row-id');
            const sessionId = $btn.data('session-id');
            const $row = $btn.closest('tr');
            const petId = $row.find('.pet-photo-input').data('pet-id');
            
            if (!photoRowId || !sessionId) {
                frappe.show_alert({message: 'Missing required data for deletion.', indicator: 'red'});
                return;
            }

            try {
                $btn.prop('disabled', true);
                $btn.after('<span class="spinner-border spinner-border-sm ml-2 photo-delete-spinner"></span>');
                
                const result = await frappe.call('petcare.petcare.page.grooming_data_entry.grooming_data_entry.delete_pet_photo', {
                    service_request_id: sessionId,
                    photo_row_id: photoRowId
                });

                if (result.message && result.message.status === 'success') {
                    frappe.show_alert({message: 'Photo deleted!', indicator: 'green'});
                    
                    // Fetch updated pet_photos for this session and update only the photo links section
                    const updatedReq = await frappe.call('petcare.petcare.page.grooming_data_entry.grooming_data_entry.get_grooming_request', {
                        service_request_id: sessionId
                    }).then(r => r.message || {});
                    
                    const $links = $row.find('.pet-photo-links');
                    $links.html(renderPetPhotos(updatedReq.pet_photos, petId, sessionId));
                } else {
                    throw new Error(result.message?.message || 'Failed to delete photo');
                }
            } catch (error) {
                console.error('Error deleting photo:', error);
                frappe.show_alert({message: error.message || 'Failed to delete photo', indicator: 'red'});
            } finally {
                $btn.prop('disabled', false);
                $row.find('.photo-delete-spinner').remove();
            }
        });

        // Helper to render pet photos from child table, with delete button
        function renderPetPhotos(petPhotos, petId, sessionId) {
            if (!Array.isArray(petPhotos)) return '';
            return petPhotos
                .filter(photo => photo.pet === petId)
                .map(photo => {
                    const url = photo.image;
                    // Ensure URL is absolute
                    const fullUrl = url.startsWith('http') ? url : frappe.urllib.get_full_url(url);
                    const parts = url.split('/');
                    const filename = parts[parts.length - 1];
                    return `<span class="inline-flex items-center gap-2 mr-2 mb-2">
                        <a href="${fullUrl}" target="_blank" rel="noopener noreferrer" class="text-xs text-blue-600 underline break-all select-all" tabindex="0" aria-label="Pet Image URL">${filename}</a>
                        <button type="button" class="btn btn-danger btn-xs delete-pet-photo-btn" data-photo-row-id="${photo.name}" data-session-id="${sessionId}" title="Delete Photo">🗑️</button>
                    </span>`;
                })
                .join('');
        }
    }
});