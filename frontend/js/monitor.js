// Monitor JavaScript

// Protect page
protectPage();

let currentOffset = 0;
let currentLimit = 100;
let autoRefreshInterval = null;

// Load logs
async function loadLogs() {
    try {
        const limit = parseInt(document.getElementById('filter-limit').value);
        currentLimit = limit;
        
        const response = await apiRequest(`/api/dashboard/logs?limit=${limit}&offset=${currentOffset}`);
        
        if (!response.ok) {
            throw new Error('Failed to load logs');
        }
        
        const logs = await response.json();
        displayLogs(logs);
        
        // Update count
        document.getElementById('logs-count').textContent = logs.length;
        
        // Update pagination buttons
        document.getElementById('prev-btn').disabled = currentOffset === 0;
        document.getElementById('next-btn').disabled = logs.length < limit;
        
    } catch (error) {
        console.error('Error loading logs:', error);
        document.getElementById('logs-table').innerHTML = 
            '<tr><td colspan="8" class="text-center text-error">Failed to load logs</td></tr>';
    }
}

// Display logs in table
function displayLogs(logs) {
    const tbody = document.getElementById('logs-table');
    
    if (!logs || logs.length === 0) {
        tbody.innerHTML = '<tr><td colspan="8" class="text-center text-secondary">No logs available</td></tr>';
        return;
    }
    
    // Apply filters
    const statusFilter = document.getElementById('filter-status').value;
    const endpointFilter = document.getElementById('filter-endpoint').value;
    
    let filteredLogs = logs;
    
    if (statusFilter === 'success') {
        filteredLogs = filteredLogs.filter(log => log.status_code >= 200 && log.status_code < 300);
    } else if (statusFilter === 'error') {
        filteredLogs = filteredLogs.filter(log => log.status_code >= 400);
    }
    
    if (endpointFilter) {
        filteredLogs = filteredLogs.filter(log => log.endpoint === endpointFilter);
    }
    
    tbody.innerHTML = filteredLogs.map(log => {
        const statusClass = log.status_code >= 200 && log.status_code < 300 ? 'badge-success' : 
                           log.status_code >= 400 ? 'badge-error' : 'badge-warning';
        
        const time = new Date(log.created_at).toLocaleTimeString();
        
        return `
            <tr>
                <td>${time}</td>
                <td><span class="badge badge-info">${log.method}</span></td>
                <td><code style="font-size: 11px;">${log.endpoint || 'N/A'}</code></td>
                <td>${log.model || 'N/A'}</td>
                <td>
                    <span class="badge ${statusClass}">
                        ${log.status_code}
                    </span>
                </td>
                <td>
                    ${log.total_tokens ? `
                        <span class="text-secondary" style="font-size: 12px;">
                            ${log.total_tokens.toLocaleString()}
                            <br>
                            <span style="color: var(--accent-cyan);">in:${log.input_tokens}</span>
                            <span style="color: var(--accent-amber);">out:${log.output_tokens}</span>
                        </span>
                    ` : 'N/A'}
                </td>
                <td>${log.latency_ms ? log.latency_ms + 'ms' : 'N/A'}</td>
                <td><span class="text-secondary" style="font-size: 11px;">${log.client_ip || 'N/A'}</span></td>
            </tr>
        `;
    }).join('');
}

// Next page
function nextPage() {
    currentOffset += currentLimit;
    loadLogs();
}

// Previous page
function previousPage() {
    currentOffset = Math.max(0, currentOffset - currentLimit);
    loadLogs();
}

// Export logs
async function exportLogs() {
    try {
        const response = await apiRequest('/api/dashboard/logs?limit=1000');
        
        if (!response.ok) {
            throw new Error('Failed to export logs');
        }
        
        const logs = await response.json();
        
        // Convert to CSV
        const csv = convertToCSV(logs);
        
        // Download
        const blob = new Blob([csv], { type: 'text/csv' });
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `logs_${new Date().toISOString()}.csv`;
        a.click();
        window.URL.revokeObjectURL(url);
        
    } catch (error) {
        console.error('Error exporting logs:', error);
        alert('Failed to export logs');
    }
}

// Convert logs to CSV
function convertToCSV(logs) {
    const headers = ['Time', 'Method', 'Endpoint', 'Model', 'Status', 'Input Tokens', 'Output Tokens', 'Total Tokens', 'Latency (ms)', 'IP'];
    
    const rows = logs.map(log => [
        log.created_at,
        log.method,
        log.endpoint,
        log.model,
        log.status_code,
        log.input_tokens,
        log.output_tokens,
        log.total_tokens,
        log.latency_ms,
        log.client_ip
    ]);
    
    const csvContent = [
        headers.join(','),
        ...rows.map(row => row.map(cell => `"${cell || ''}"`).join(','))
    ].join('\n');
    
    return csvContent;
}

// Setup auto-refresh
function setupAutoRefresh() {
    const checkbox = document.getElementById('auto-refresh');
    
    checkbox.addEventListener('change', () => {
        if (checkbox.checked) {
            autoRefreshInterval = setInterval(loadLogs, 5000); // Refresh every 5 seconds
        } else {
            if (autoRefreshInterval) {
                clearInterval(autoRefreshInterval);
                autoRefreshInterval = null;
            }
        }
    });
    
    // Start auto-refresh if checked
    if (checkbox.checked) {
        autoRefreshInterval = setInterval(loadLogs, 5000);
    }
}

// Initial load
loadLogs();
setupAutoRefresh();

// Cleanup on page unload
window.addEventListener('beforeunload', () => {
    if (autoRefreshInterval) {
        clearInterval(autoRefreshInterval);
    }
});
