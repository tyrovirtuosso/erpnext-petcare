frappe.pages['customer_location_map'].on_page_load = function(wrapper) {
	var page = frappe.ui.make_app_page({
		parent: wrapper,
		title: 'Customer Location Map',
		single_column: true
	});

	// Add customer list sidebar
	const customerListSidebar = $(`
		<div class="customer-list-sidebar" style="
			position: absolute;
			top: 0;
			right: 0;
			width: 300px;
			height: 100%;
			background: white;
			border-left: 1px solid #d1d8dd;
			z-index: 500;
			transform: translateX(100%);
			transition: transform 0.3s ease;
			display: flex;
			flex-direction: column;
		">
			<div class="sidebar-header" style="
				padding: 15px;
				border-bottom: 1px solid #d1d8dd;
				display: flex;
				justify-content: space-between;
				align-items: center;
				background-color: #f7fafc;
			">
				<div style="display: flex; align-items: center;">
					<h6 class="sidebar-title" style="margin: 0; font-weight: 600;"></h6>
					<span class="customer-count" style="
						background: #e2e8f0;
						color: #4a5568;
						padding: 2px 8px;
						border-radius: 12px;
						font-size: 12px;
						margin-left: 8px;
					"></span>
				</div>
				<button class="btn btn-link btn-sm close-sidebar" style="padding: 0;">
					<i class="fa fa-times"></i>
				</button>
			</div>
			<div class="customer-list" style="
				flex: 1;
				overflow-y: auto;
				padding: 15px;
			"></div>
		</div>
	`).appendTo(page.main);

	// Add close handler
	customerListSidebar.find('.close-sidebar').on('click', () => {
		customerListSidebar.css('transform', 'translateX(100%)');
	});

	// Add lead status filter
	const leadStatusFilter = $(`
		<div class="lead-status-filter" style="margin: 10px 15px;">
			<label class="control-label">Lead Status</label>
			<div class="checkbox-list" style="margin-top: 5px;">
				<label class="checkbox">
					<input type="checkbox" value="New Lead" checked> New Lead
				</label>
				<label class="checkbox">
					<input type="checkbox" value="Interested" checked> Interested
				</label>
				<label class="checkbox">
					<input type="checkbox" value="Converted" checked> Converted
				</label>
				<label class="checkbox">
					<input type="checkbox" value="Lost" checked> Lost
				</label>
			</div>
		</div>
	`).appendTo(page.main);

	// Add refresh button
	page.add_inner_button(__('Refresh Map'), function() {
		loadMap();
	});

	// Add progress bar
	const progressBar = $(`
		<div class="progress" style="height: 6px; margin: -10px -15px 10px;">
			<div class="progress-bar" role="progressbar" style="width: 0%"></div>
		</div>
	`).prependTo(page.main);

	// Add map container
	const mapContainer = $('<div id="map" style="height: calc(100vh - 260px); width: 100%; position: relative;"></div>');
	const loadingOverlay = $(`
		<div id="map-loading-overlay" style="
			position: absolute;
			top: 0;
			left: 0;
			right: 0;
			bottom: 0;
			background: rgba(255,255,255,0.8);
			display: flex;
			justify-content: center;
			align-items: center;
			z-index: 1000;
		">
			<div style="text-align: center;">
				<div class="loading-spinner"></div>
				<div id="loading-status" style="margin-top: 10px; font-weight: 500;"></div>
			</div>
		</div>
	`);
	
	mapContainer.append(loadingOverlay);
	$(page.main).append(mapContainer);

	// Initialize map with Google Maps API
	frappe.customer_location_map = new CustomerLocationMap(page, progressBar, loadingOverlay);
	
	// Add filter change handler
	leadStatusFilter.find('input[type="checkbox"]').on('change', function() {
		frappe.customer_location_map.updateMarkersVisibility();
	});
	
	// First get the API key and load Google Maps
	frappe.call({
		method: 'petcare.petcare.page.customer_location_map.customer_location_map.get_google_maps_api_key',
		callback: function(r) {
			if (r.message) {
				// Create script element and load Google Maps API
				const script = document.createElement('script');
				script.src = `https://maps.googleapis.com/maps/api/js?key=${r.message}`;
				script.onload = function() {
					// Load MarkerClusterer after Google Maps
					const clustererScript = document.createElement('script');
					clustererScript.src = 'https://unpkg.com/@google/markerclustererplus@4.0.1/dist/markerclustererplus.min.js';
					clustererScript.onload = function() {
						// Initialize map after both scripts are loaded
						loadMap();
					};
					document.head.appendChild(clustererScript);
				};
				document.head.appendChild(script);
			} else {
				frappe.msgprint({
					title: __('Error'),
					indicator: 'red',
					message: __('Google Maps API key not found. Please configure it in site_config.json')
				});
			}
		}
	});

	// Store sidebar reference in the global space
	frappe.customer_location_map_sidebar = customerListSidebar;
};

class CustomerLocationMap {
	constructor(page, progressBar, loadingOverlay) {
		this.page = page;
		this.progressBar = progressBar;
		this.loadingOverlay = loadingOverlay;
		this.markers = [];
		this.bounds = null;
		this.hoverInfoWindow = null;
		this.customersData = []; // Store customers data
		this.markerCluster = null;
		
		// Define colors for different lead statuses
		this.statusColors = {
			'New Lead': '#2196F3',     // Blue
			'Interested': '#FF9800',    // Orange
			'Converted': '#4CAF50',     // Green
			'Lost': '#F44336'          // Red
		};
	}

	getSelectedLeadStatuses() {
		return $('.lead-status-filter input[type="checkbox"]:checked')
			.map(function() { return $(this).val(); })
			.get();
	}

	updateProgress(percent, message) {
		this.progressBar.find('.progress-bar').css('width', `${percent}%`);
		if (message) {
			this.loadingOverlay.find('#loading-status').text(message);
		}
	}

	createInfoContent(customer, position, isHover = false) {
		if (isHover) {
			return `
				<div style="min-width: 200px; padding: 10px;">
					<div style="margin-bottom: 10px;">
						<h4 style="margin: 0 0 5px; color: #1F272E; font-size: 14px;">${customer.customer_name}</h4>
						<div style="color: ${this.statusColors[customer.custom_lead_status]}; font-weight: 500; font-size: 12px;">
							${customer.custom_lead_status}
						</div>
						${customer.mobile_no ? `
							<div style="font-size: 12px;">📞 ${customer.mobile_no}</div>
						` : ''}
					</div>
					<div style="font-size: 12px;">
						<div>Days Since Service: <strong>${customer.custom_days_since_last_service || 'N/A'}</strong></div>
						<div>Total Pets: <strong>${customer.custom_total_pets || 'N/A'}</strong></div>
					</div>
				</div>
			`;
		}

		return `
			<div style="min-width: 300px; padding: 15px;">
				<div style="margin-bottom: 15px;">
					<h4 style="margin: 0 0 5px; color: #1F272E;">${customer.customer_name}</h4>
					<div style="color: ${this.statusColors[customer.custom_lead_status]}; font-weight: 500; margin-bottom: 5px;">
						${customer.custom_lead_status} - ID: ${customer.name}
					</div>
					${customer.mobile_no ? `
						<div style="margin-bottom: 5px;">
							<a href="tel:${customer.mobile_no}" style="color: #2196F3; text-decoration: none;">
								📞 ${customer.mobile_no}
							</a>
						</div>
					` : ''}
				</div>
				<div style="display: grid; grid-template-columns: repeat(2, 1fr); gap: 10px; margin-bottom: 15px;">
					<div>Days Since Service: <strong>${customer.custom_days_since_last_service || 'N/A'}</strong></div>
					<div>Total Pets: <strong>${customer.custom_total_pets || 'N/A'}</strong></div>
					<div>Living Space: <strong>${customer.custom_living_space || 'N/A'}</strong></div>
					<div>Territory: <strong>${customer.territory || 'N/A'}</strong></div>
					<div>Parking: ${this.formatYesNo(customer.custom_parking)}</div>
					<div>Electricity: ${this.formatYesNo(customer.custom_electricity)}</div>
					<div>Water: ${this.formatYesNo(customer.custom_water_)}</div>
				</div>
				<div style="display: flex; gap: 10px;">
					<button class="btn btn-sm btn-primary" onclick="frappe.set_route('Form', 'Customer', '${customer.name}')">
						View Customer
					</button>
					<a href="https://www.google.com/maps?q=${position.lat},${position.lng}" target="_blank" class="btn btn-sm btn-default">
						Open in Google Maps
					</a>
				</div>
			</div>
		`;
	}

	updateMarkersVisibility() {
		const selectedStatuses = this.getSelectedLeadStatuses();
		let visibleMarkers = 0;
		const currentZoom = this.map.getZoom();
		const currentCenter = this.map.getCenter();

		this.markers.forEach((marker, index) => {
			const customer = this.customersData[index];
			const isVisible = selectedStatuses.includes(customer.custom_lead_status);
			
			marker.setMap(isVisible ? this.map : null);
			
			if (isVisible) {
				visibleMarkers++;
			}

			// Close any open info windows for hidden markers
			if (!isVisible) {
				if (marker.clickInfoWindow) marker.clickInfoWindow.close();
			}
		});

		// Close hover window if open
		if (this.hoverInfoWindow) {
			this.hoverInfoWindow.close();
			this.hoverInfoWindow = null;
		}

		// Only adjust bounds on initial load or if no markers are visible
		if (visibleMarkers === 0) {
			frappe.msgprint({
				title: __('No Data'),
				indicator: 'yellow',
				message: __('No customers found with the selected lead status(es).')
			});
		} else {
			// Restore previous view
			this.map.setZoom(currentZoom);
			this.map.setCenter(currentCenter);
		}

		// Update clusterer with only visible markers
		if (this.markerCluster) {
			this.markerCluster.clearMarkers();
			const visibleMarkersArr = this.markers.filter((marker, idx) =>
				selectedStatuses.includes(this.customersData[idx].custom_lead_status)
			);
			this.markerCluster.addMarkers(visibleMarkersArr);
		}
	}

	showLocations() {
		this.updateProgress(0, "Initializing...");
		this.loadingOverlay.show();

		// Clear existing markers and hover info window
		this.markers.forEach(marker => marker.setMap(null));
		this.markers = [];
		this.customersData = []; // Clear stored customer data
		if (this.hoverInfoWindow) {
			this.hoverInfoWindow.close();
			this.hoverInfoWindow = null;
		}
		this.bounds = new google.maps.LatLngBounds();
		// Clear previous clusterer
		if (this.markerCluster) {
			this.markerCluster.clearMarkers();
			this.markerCluster = null;
		}

		this.updateProgress(30, "Loading customer locations...");

		frappe.call({
			method: "petcare.petcare.page.customer_location_map.customer_location_map.get_customer_locations",
			callback: (response) => {
				if (response.exc) {
					frappe.msgprint({
						title: __('Error'),
						indicator: 'red',
						message: __('Failed to fetch customer locations: ') + response.exc
					});
					this.loadingOverlay.hide();
					return;
				}

				const { customers, failed } = response.message;
				
				if (!customers || !customers.length) {
					frappe.msgprint({
						title: __('No Data'),
						indicator: 'yellow',
						message: __('No customers found with valid coordinates.')
					});
					this.loadingOverlay.hide();
					return;
				}

				this.updateProgress(60, `Processing ${customers.length} locations...`);

				// Store customers data and create markers
				customers.forEach((customer, index) => {
					const position = {
						lat: parseFloat(customer.latitude),
						lng: parseFloat(customer.longitude)
					};

					// Skip if invalid coordinates
					if (isNaN(position.lat) || isNaN(position.lng)) {
						console.error(`Invalid coordinates for customer ${customer.name}`);
						return;
					}

					// Store customer data
					this.customersData.push(customer);

					const marker = new google.maps.Marker({
						position: position,
						map: this.map,
						title: customer.customer_name,
						icon: {
							path: google.maps.SymbolPath.CIRCLE,
							scale: 10,
							fillColor: this.statusColors[customer.custom_lead_status] || '#757575',
							fillOpacity: 1,
							strokeWeight: 2,
							strokeColor: "#FFFFFF"
						}
					});

					// Create info windows
					const clickInfoWindow = new google.maps.InfoWindow({
						content: this.createInfoContent(customer, position, false)
					});

					// Add hover event listeners
					marker.addListener('mouseover', () => {
						// Close any existing hover info window
						if (this.hoverInfoWindow) {
							this.hoverInfoWindow.close();
						}

						// Create and show new hover info window
						this.hoverInfoWindow = new google.maps.InfoWindow({
							content: this.createInfoContent(customer, position, true),
							disableAutoPan: true // Prevent map from panning to the info window
						});
						
						this.hoverInfoWindow.open(this.map, marker);
					});

					marker.addListener('mouseout', () => {
						if (this.hoverInfoWindow) {
							this.hoverInfoWindow.close();
							this.hoverInfoWindow = null;
						}
					});

					marker.addListener('click', () => {
						// Close any open info windows including hover
						this.markers.forEach(m => {
							if (m.clickInfoWindow) m.clickInfoWindow.close();
						});
						if (this.hoverInfoWindow) {
							this.hoverInfoWindow.close();
							this.hoverInfoWindow = null;
						}
						clickInfoWindow.open(this.map, marker);
					});

					marker.clickInfoWindow = clickInfoWindow;
					this.markers.push(marker);
					this.bounds.extend(position);

					// Update progress
					const progress = 60 + (40 * (index + 1) / customers.length);
					this.updateProgress(progress, `Processed ${index + 1} of ${customers.length} locations...`);
				});

				// Cluster all markers with enhanced options
				this.markerCluster = new MarkerClusterer(this.map, this.markers, {
					imagePath: 'https://developers.google.com/maps/documentation/javascript/examples/markerclusterer/m',
					maxZoom: 15,
					gridSize: 50,
					zoomOnClick: false,
					averageCenter: true,
					minimumClusterSize: 2,
					styles: [
						{
							textColor: 'white',
							url: 'https://developers.google.com/maps/documentation/javascript/examples/markerclusterer/m1.png',
							height: 53,
							width: 53
						},
						{
							textColor: 'white',
							url: 'https://developers.google.com/maps/documentation/javascript/examples/markerclusterer/m2.png',
							height: 56,
							width: 56
						},
						{
							textColor: 'white',
							url: 'https://developers.google.com/maps/documentation/javascript/examples/markerclusterer/m3.png',
							height: 66,
							width: 66
						}
					]
				});

				// Add click handler for clusters
				google.maps.event.addListener(this.markerCluster, 'clusterclick', (cluster) => {
					const markers = cluster.getMarkers();
					const bounds = new google.maps.LatLngBounds();
					markers.forEach(marker => bounds.extend(marker.getPosition()));

					// Calculate the zoom level that would fit these bounds
					const maxZoom = 15; // Your max zoom level
					this.map.fitBounds(bounds);
					const zoom = this.map.getZoom();
					
					// Check if markers are too close (would still be clustered at max zoom)
					let wouldSeparate = true;
					if (markers.length > 1) {
						const positions = markers.map(m => m.getPosition());
						for (let i = 0; i < positions.length; i++) {
							for (let j = i + 1; j < positions.length; j++) {
								// Calculate distance in pixels at max zoom
								const projection = this.map.getProjection();
								if (projection) {
									const p1 = projection.fromLatLngToPoint(positions[i]);
									const p2 = projection.fromLatLngToPoint(positions[j]);
									const pixelDistance = Math.sqrt(
										Math.pow(p1.x - p2.x, 2) + 
										Math.pow(p1.y - p2.y, 2)
									) * Math.pow(2, maxZoom);
									
									if (pixelDistance < 50) { // If markers would be closer than 50 pixels
										wouldSeparate = false;
										break;
									}
								}
							}
							if (!wouldSeparate) break;
						}
					}

					// If markers wouldn't separate at max zoom or we're already at max zoom
					if (!wouldSeparate || zoom >= maxZoom) {
						const customers = markers.map(marker => 
							this.customersData[this.markers.indexOf(marker)]
						);
						this.showCustomerList(customers, `Customers at this location (${markers.length})`);
					} else {
						// If markers would separate, zoom in
						this.map.fitBounds(bounds);
						
						// If we're very close to max zoom, just go to max zoom
						if (zoom > maxZoom - 2) {
							this.map.setZoom(maxZoom);
						}
					}
				});

				// Update visibility based on selected filters
				this.updateMarkersVisibility();

				this.updateProgress(100, "");
				this.loadingOverlay.hide();

				// Show any failures
				if (failed && failed.length > 0) {
					frappe.msgprint({
						title: __('Some Customers Failed'),
						indicator: 'orange',
						message: __(`${failed.length} customer(s) could not be displayed on the map. Check the error log for details.`)
					});
				}
			}
		});
	}

	formatYesNo(value) {
		if (!value) return '<span class="badge" style="background-color: #ff5252;">No</span>';
		return '<span class="badge" style="background-color: #4CAF50;">Yes</span>';
	}

	showCustomerList(customers, title) {
		const sidebar = frappe.customer_location_map_sidebar;
		const customerList = sidebar.find('.customer-list');
		
		// Update title and count separately
		sidebar.find('.sidebar-title').text('Customers at this location');
		sidebar.find('.customer-count').text(customers.length);

		let content = '';
		customers.forEach(customer => {
			// Format phone number to ensure it starts with +
			const formattedPhone = customer.mobile_no ? 
				(customer.mobile_no.startsWith('+') ? customer.mobile_no : '+' + customer.mobile_no) : '';

			content += `
				<div class="customer-card" style="
					border: 1px solid #d1d8dd;
					border-radius: 4px;
					padding: 15px;
					margin-bottom: 10px;
					background: white;
					transition: all 0.2s;
					cursor: pointer;
				">
					<div style="display: flex; justify-content: space-between; align-items: start;">
						<div style="flex: 1;">
							<div style="font-weight: 600; color: ${this.statusColors[customer.custom_lead_status]};">
								${customer.customer_name}
							</div>
							<div style="font-size: 12px; color: #666; margin: 5px 0;">
								${customer.custom_lead_status} · ID: ${customer.name}
							</div>
							${formattedPhone ? `
								<div style="
									font-size: 14px;
									color: #2196F3;
									margin-top: 8px;
									display: flex;
									align-items: center;
									gap: 6px;
								">
									<i class="fa fa-phone" style="font-size: 12px;"></i>
									<a href="tel:${formattedPhone}" 
										style="color: #2196F3; text-decoration: none;"
										target="_blank" rel="noopener noreferrer">
										${formattedPhone}
									</a>
								</div>
							` : ''}
						</div>
						<div class="action-buttons" style="opacity: 0.7; transition: opacity 0.2s;">
							<a class="btn btn-xs btn-default view-customer" 
								href="/app/customer/${encodeURIComponent(customer.name)}"
								target="_blank" rel="noopener noreferrer"
								title="View Details">
								<i class="fa fa-external-link"></i>
							</a>
						</div>
					</div>
					<div style="
						display: grid;
						grid-template-columns: repeat(2, 1fr);
						gap: 10px;
						margin-top: 10px;
						font-size: 12px;
					">
						<div>
							<i class="fa fa-clock-o" style="color: #8D99A6;"></i>
							Days Since Service: <strong>${customer.custom_days_since_last_service || 'N/A'}</strong>
						</div>
						<div>
							<i class="fa fa-paw" style="color: #8D99A6;"></i>
							Total Pets: <strong>${customer.custom_total_pets || 'N/A'}</strong>
						</div>
						${customer.territory ? `
							<div>
								<i class="fa fa-map-marker" style="color: #8D99A6;"></i>
								${customer.territory}
							</div>
						` : ''}
						${customer.custom_living_space ? `
							<div>
								<i class="fa fa-home" style="color: #8D99A6;"></i>
								${customer.custom_living_space}
							</div>
						` : ''}
					</div>
					<div style="
						display: flex;
						gap: 10px;
						margin-top: 10px;
						font-size: 12px;
					">
						<span title="Parking">
							<i class="fa fa-car" style="color: ${customer.custom_parking ? '#4CAF50' : '#ff5252'};"></i>
						</span>
						<span title="Electricity">
							<i class="fa fa-bolt" style="color: ${customer.custom_electricity ? '#4CAF50' : '#ff5252'};"></i>
						</span>
						<span title="Water">
							<i class="fa fa-tint" style="color: ${customer.custom_water_ ? '#4CAF50' : '#ff5252'};"></i>
						</span>
					</div>
				</div>
			`;
		});

		customerList.html(content);

		// Add hover effect
		customerList.find('.customer-card').hover(
			function() {
				$(this).css({
					'box-shadow': '0 2px 8px rgba(0,0,0,0.1)',
					'border-color': '#b8c2cc'
				});
				$(this).find('.action-buttons').css('opacity', '1');
			},
			function() {
				$(this).css({
					'box-shadow': 'none',
					'border-color': '#d1d8dd'
				});
				$(this).find('.action-buttons').css('opacity', '0.7');
			}
		);

		// Show sidebar
		sidebar.css('transform', 'translateX(0)');
	}
}

function loadMap() {
	if (typeof google === 'undefined' || !frappe.customer_location_map) {
		frappe.msgprint({
			title: __('Error'),
			indicator: 'red',
			message: __('Google Maps failed to load. Please refresh the page.')
		});
		return;
	}

	const mapOptions = {
		center: { lat: 20.5937, lng: 78.9629 }, // Center of India
		zoom: 5,
		mapTypeControl: true,
		streetViewControl: false,
		mapTypeId: google.maps.MapTypeId.ROADMAP
	};

	frappe.customer_location_map.map = new google.maps.Map(
		document.getElementById('map'),
		mapOptions
	);

	frappe.customer_location_map.showLocations();
} 