/**
 * Global TimeSync API Dashboard JavaScript
 * Handles time conversion, timezone display, and API interaction.
 */

// Configuration object
const config = {
    apiBase: "/api/timesync",
    updateInterval: 10000, // 10 seconds
    defaultTimezone: Intl.DateTimeFormat().resolvedOptions().timeZone || "UTC"
};

// State management
let state = {
    token: null,
    selectedTimezone: config.defaultTimezone,
    popularTimezones: [],
    conversionHistory: [],
    worldClock: {}
};

// DOM elements
const elements = {
    // Conversion form
    conversionForm: document.getElementById('conversion-form'),
    utcTimestampInput: document.getElementById('utc-timestamp'),
    timezoneSelect: document.getElementById('timezone-select'),
    convertButton: document.getElementById('convert-button'),
    conversionResult: document.getElementById('conversion-result'),
    
    // World clock
    worldClockContainer: document.getElementById('world-clock'),
    
    // Popular timezones
    popularTimezonesContainer: document.getElementById('popular-timezones'),
    
    // Timezone search
    timezoneSearchInput: document.getElementById('timezone-search'),
    searchResults: document.getElementById('search-results'),
    
    // History section
    conversionHistoryContainer: document.getElementById('conversion-history')
};

/**
 * Initialize the dashboard functionality
 */
async function initDashboard() {
    console.log("Initializing TimeSync Dashboard...");
    
    // Set current UTC time as default in the input
    setCurrentUTCTime();
    
    // Load available timezones
    await loadTimezones();
    
    // Load popular timezones
    await loadPopularTimezones();
    
    // Setup event listeners
    setupEventListeners();
    
    // Start regular updates for world clocks
    startClockUpdates();
    
    console.log("Dashboard initialization complete");
}

/**
 * Set the current UTC time in the input field
 */
function setCurrentUTCTime() {
    const now = new Date();
    const isoString = now.toISOString();
    if (elements.utcTimestampInput) {
        elements.utcTimestampInput.value = isoString;
    }
}

/**
 * Load available timezones from the API
 */
async function loadTimezones() {
    try {
        const response = await fetch(`${config.apiBase}/timezones`);
        if (!response.ok) {
            throw new Error(`Failed to load timezones: ${response.statusText}`);
        }
        
        const timezones = await response.json();
        populateTimezoneSelect(timezones);
        
        console.log(`Loaded ${timezones.length} timezones`);
    } catch (error) {
        console.error("Error loading timezones:", error);
        showError("Failed to load timezone data. Please try refreshing the page.");
    }
}

/**
 * Load popular timezones for the world clock display
 */
async function loadPopularTimezones() {
    try {
        const response = await fetch(`${config.apiBase}/popular-timezones`);
        if (!response.ok) {
            throw new Error(`Failed to load popular timezones: ${response.statusText}`);
        }
        
        state.popularTimezones = await response.json();
        renderPopularTimezones();
        
        console.log(`Loaded ${state.popularTimezones.length} popular timezones`);
    } catch (error) {
        console.error("Error loading popular timezones:", error);
        showError("Failed to load world clock data. Please try refreshing the page.");
    }
}

/**
 * Populate the timezone select dropdown
 */
function populateTimezoneSelect(timezones) {
    if (!elements.timezoneSelect) return;
    
    // Clear existing options
    elements.timezoneSelect.innerHTML = '';
    
    // Add option for browser's local timezone
    const localOption = document.createElement('option');
    localOption.value = config.defaultTimezone;
    localOption.textContent = `${config.defaultTimezone} (Local)`;
    localOption.selected = true;
    elements.timezoneSelect.appendChild(localOption);
    
    // Add all timezones
    timezones.forEach(timezone => {
        if (timezone !== config.defaultTimezone) {
            const option = document.createElement('option');
            option.value = timezone;
            option.textContent = timezone;
            elements.timezoneSelect.appendChild(option);
        }
    });
}

/**
 * Render popular timezones as a world clock
 */
function renderPopularTimezones() {
    if (!elements.popularTimezonesContainer) return;
    
    // Clear existing content
    elements.popularTimezonesContainer.innerHTML = '';
    
    // Create a row for the cards
    const row = document.createElement('div');
    row.className = 'row g-3';
    
    // Add each timezone as a card
    state.popularTimezones.forEach(timezone => {
        const col = document.createElement('div');
        col.className = 'col-md-4 col-lg-3 mb-3';
        
        // Parse the current time
        const time = new Date(timezone.current_time);
        
        col.innerHTML = `
            <div class="card h-100">
                <div class="card-body">
                    <h5 class="card-title">${formatTimezoneName(timezone.name)}</h5>
                    <h6 class="card-subtitle mb-2 text-muted">
                        ${timezone.country_code ? `(${timezone.country_code})` : ''}
                        ${timezone.offset}
                    </h6>
                    <p class="card-text timezone-time" data-timezone="${timezone.name}">
                        ${formatTime(time)}
                    </p>
                    <div class="text-muted small">
                        ${timezone.is_dst ? '<span class="badge bg-info">DST Active</span>' : ''}
                    </div>
                </div>
                <div class="card-footer">
                    <button class="btn btn-sm btn-outline-primary convert-to-btn" 
                            data-timezone="${timezone.name}">
                        Convert to this timezone
                    </button>
                </div>
            </div>
        `;
        
        row.appendChild(col);
    });
    
    elements.popularTimezonesContainer.appendChild(row);
    
    // Add event listeners to the convert buttons
    document.querySelectorAll('.convert-to-btn').forEach(button => {
        button.addEventListener('click', (e) => {
            const timezone = e.target.getAttribute('data-timezone');
            if (elements.timezoneSelect) {
                elements.timezoneSelect.value = timezone;
                
                // If form exists, submit it
                if (elements.conversionForm) {
                    elements.conversionForm.dispatchEvent(new Event('submit'));
                }
            }
        });
    });
}

/**
 * Format a timezone name for display
 */
function formatTimezoneName(name) {
    // Replace underscores with spaces and split on slashes
    const parts = name.replace(/_/g, ' ').split('/');
    // Return just the city part (last part)
    return parts[parts.length - 1];
}

/**
 * Format a date object as a readable time string
 */
function formatTime(date) {
    return date.toLocaleString(undefined, {
        weekday: 'short',
        month: 'short',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit',
        second: '2-digit'
    });
}

/**
 * Start regular updates for the world clocks
 */
function startClockUpdates() {
    // Update immediately
    updateAllClocks();
    
    // Then update at regular intervals
    setInterval(updateAllClocks, config.updateInterval);
}

/**
 * Update all clock displays
 */
function updateAllClocks() {
    document.querySelectorAll('.timezone-time').forEach(clockElement => {
        const timezone = clockElement.getAttribute('data-timezone');
        
        // Get current time
        const now = new Date();
        
        // Format time string for this timezone
        try {
            const options = {
                timeZone: timezone,
                weekday: 'short',
                month: 'short',
                day: 'numeric',
                hour: '2-digit',
                minute: '2-digit',
                second: '2-digit'
            };
            
            clockElement.textContent = now.toLocaleString(undefined, options);
        } catch (error) {
            console.error(`Error formatting time for ${timezone}:`, error);
            clockElement.textContent = "Time unavailable";
        }
    });
}

/**
 * Convert UTC timestamp to target timezone
 */
async function convertTime(e) {
    if (e) e.preventDefault();
    
    if (!elements.utcTimestampInput || !elements.timezoneSelect || !elements.conversionResult) {
        console.error("Required form elements not found");
        return;
    }
    
    const utcTimestamp = elements.utcTimestampInput.value.trim();
    const targetTimezone = elements.timezoneSelect.value;
    
    if (!utcTimestamp || !targetTimezone) {
        showError("Please provide both a UTC timestamp and target timezone");
        return;
    }
    
    try {
        // Show loading state
        elements.conversionResult.innerHTML = `
            <div class="alert alert-info">
                <span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span>
                Converting time...
            </div>
        `;
        
        // Make API request
        const response = await fetch(`${config.apiBase}/convert?utc_timestamp=${encodeURIComponent(utcTimestamp)}&target_timezone=${encodeURIComponent(targetTimezone)}`);
        
        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.detail || "Error converting time");
        }
        
        const result = await response.json();
        
        // Format the result
        const localTime = new Date(result.local_timestamp);
        const utcTime = new Date(result.utc_timestamp);
        
        // Display the result
        elements.conversionResult.innerHTML = `
            <div class="alert alert-success">
                <h5>Conversion Result</h5>
                <div class="row">
                    <div class="col-md-6">
                        <strong>UTC Time:</strong><br>
                        ${utcTime.toLocaleString(undefined, {
                            weekday: 'long',
                            year: 'numeric',
                            month: 'long',
                            day: 'numeric',
                            hour: '2-digit',
                            minute: '2-digit',
                            second: '2-digit',
                            timeZoneName: 'short'
                        })}
                    </div>
                    <div class="col-md-6">
                        <strong>${result.timezone} Time:</strong><br>
                        ${localTime.toLocaleString(undefined, {
                            weekday: 'long',
                            year: 'numeric',
                            month: 'long',
                            day: 'numeric',
                            hour: '2-digit',
                            minute: '2-digit',
                            second: '2-digit',
                            timeZoneName: 'short'
                        })}
                    </div>
                </div>
                <div class="mt-2">
                    <strong>Time Difference:</strong> UTC ${result.offset}
                    ${result.is_dst ? '<span class="badge bg-info ms-2">DST Active</span>' : ''}
                </div>
            </div>
        `;
        
        // Add to conversion history
        addToHistory(result);
        
    } catch (error) {
        console.error("Error converting time:", error);
        showError(error.message || "Failed to convert time. Please check your input and try again.");
    }
}

/**
 * Add a conversion result to the history
 */
function addToHistory(result) {
    // Add to the beginning of the history array
    state.conversionHistory.unshift(result);
    
    // Keep only the last 5 items
    if (state.conversionHistory.length > 5) {
        state.conversionHistory.pop();
    }
    
    // Update the history display
    renderConversionHistory();
}

/**
 * Render the conversion history
 */
function renderConversionHistory() {
    if (!elements.conversionHistoryContainer) return;
    
    // Clear existing content
    elements.conversionHistoryContainer.innerHTML = '';
    
    // If no history, show a message
    if (state.conversionHistory.length === 0) {
        elements.conversionHistoryContainer.innerHTML = `
            <div class="alert alert-info">
                No conversion history yet. Convert a time to see it here.
            </div>
        `;
        return;
    }
    
    // Create a table for the history
    const table = document.createElement('table');
    table.className = 'table table-sm table-striped';
    
    // Add table header
    table.innerHTML = `
        <thead>
            <tr>
                <th>UTC Time</th>
                <th>Local Time</th>
                <th>Timezone</th>
                <th>Offset</th>
                <th>DST</th>
            </tr>
        </thead>
        <tbody>
        </tbody>
    `;
    
    // Add rows for each history item
    const tbody = table.querySelector('tbody');
    
    state.conversionHistory.forEach(item => {
        const row = document.createElement('tr');
        
        // Parse times
        const utcTime = new Date(item.utc_timestamp);
        const localTime = new Date(item.local_timestamp);
        
        row.innerHTML = `
            <td>${utcTime.toLocaleString()}</td>
            <td>${localTime.toLocaleString()}</td>
            <td>${item.timezone}</td>
            <td>${item.offset}</td>
            <td>${item.is_dst ? 'Yes' : 'No'}</td>
        `;
        
        tbody.appendChild(row);
    });
    
    elements.conversionHistoryContainer.appendChild(table);
}

/**
 * Display an error message
 */
function showError(message) {
    if (!elements.conversionResult) return;
    
    elements.conversionResult.innerHTML = `
        <div class="alert alert-danger">
            <strong>Error:</strong> ${message}
        </div>
    `;
}

/**
 * Setup event listeners for the dashboard
 */
function setupEventListeners() {
    // Conversion form submission
    if (elements.conversionForm) {
        elements.conversionForm.addEventListener('submit', convertTime);
    }
    
    // Current UTC time button
    const nowButton = document.getElementById('now-button');
    if (nowButton) {
        nowButton.addEventListener('click', setCurrentUTCTime);
    }
    
    // Timezone search input
    if (elements.timezoneSearchInput) {
        elements.timezoneSearchInput.addEventListener('input', handleTimezoneSearch);
    }
}

/**
 * Handle timezone search input
 */
function handleTimezoneSearch(e) {
    const searchTerm = e.target.value.trim().toLowerCase();
    
    if (!elements.searchResults || !elements.timezoneSelect) return;
    
    // Clear results if search term is empty
    if (searchTerm.length === 0) {
        elements.searchResults.innerHTML = '';
        return;
    }
    
    // Get all timezone options
    const options = Array.from(elements.timezoneSelect.options);
    
    // Filter options based on search term
    const filteredOptions = options.filter(option => 
        option.textContent.toLowerCase().includes(searchTerm)
    );
    
    // Show up to 5 results
    const limitedResults = filteredOptions.slice(0, 5);
    
    // Display results
    elements.searchResults.innerHTML = '';
    
    if (limitedResults.length === 0) {
        elements.searchResults.innerHTML = `
            <div class="list-group-item">No matching timezones found</div>
        `;
    } else {
        const resultsList = document.createElement('div');
        resultsList.className = 'list-group';
        
        limitedResults.forEach(option => {
            const item = document.createElement('button');
            item.className = 'list-group-item list-group-item-action';
            item.textContent = option.textContent;
            item.addEventListener('click', () => {
                elements.timezoneSelect.value = option.value;
                elements.searchResults.innerHTML = '';
                elements.timezoneSearchInput.value = '';
            });
            
            resultsList.appendChild(item);
        });
        
        elements.searchResults.appendChild(resultsList);
    }
}

// Initialize the dashboard when the DOM is fully loaded
document.addEventListener('DOMContentLoaded', initDashboard);
