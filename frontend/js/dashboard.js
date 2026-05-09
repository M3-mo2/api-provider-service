// Dashboard JavaScript

// Protect page
protectPage();

let tokenChart = null;
let endpointChart = null;

// Format number with commas
function formatNumber(num) {
    return num.toString().replace(/\B(?=(\d{3})+(?!\d))/g, ",");
}

// Load dashboard data
async function loadDashboard() {
    try {
        const response = await apiRequest('/api/dashboard/stats');
        
        if (!response.ok) {
            throw new Error('Failed to load dashboard data');
        }
        
        const data = await response.json();
        
        // Update stats
        updateStats(data.stats);
        
        // Update top keys table
        updateTopKeys(data.top_keys);
        
        // Update charts
        updateTokenChart(data.token_timeline);
        updateEndpointChart(data.requests_by_endpoint);
        
    } catch (error) {
        console.error('Error loading dashboard:', error);
    }
}

// Update stats cards
function updateStats(stats) {
    document.getElementById('stat-total-requests').textContent = formatNumber(stats.total_requests);
    document.getElementById('stat-total-tokens').textContent = formatNumber(stats.total_tokens);
    document.getElementById('stat-success-rate').textContent = stats.success_rate + '%';
    document.getElementById('stat-avg-latency').textContent = stats.avg_latency_ms + 'ms';
    document.getElementById('stat-total-cost').textContent = '$' + stats.total_cost.toFixed(4);
    document.getElementById('stat-active-keys').textContent = stats.active_keys;
}

// Update top keys table
function updateTopKeys(keys) {
    const tbody = document.getElementById('top-keys-table');
    
    if (!keys || keys.length === 0) {
        tbody.innerHTML = '<tr><td colspan="4" class="text-center text-secondary">No data available</td></tr>';
        return;
    }
    
    tbody.innerHTML = keys.map(key => `
        <tr>
            <td><strong>${key.name}</strong></td>
            <td>${formatNumber(key.total_requests)}</td>
            <td>${key.success_rate}%</td>
            <td>
                <span class="badge ${key.success_rate >= 95 ? 'badge-success' : 'badge-warning'}">
                    ${key.success_rate >= 95 ? '✓ Healthy' : '⚠ Warning'}
                </span>
            </td>
        </tr>
    `).join('');
}

// Update token usage chart
function updateTokenChart(timeline) {
    const ctx = document.getElementById('token-chart').getContext('2d');
    
    if (tokenChart) {
        tokenChart.destroy();
    }
    
    const labels = timeline.map(t => t.date);
    const inputTokens = timeline.map(t => t.input_tokens);
    const outputTokens = timeline.map(t => t.output_tokens);
    
    tokenChart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: labels,
            datasets: [
                {
                    label: 'Input Tokens',
                    data: inputTokens,
                    borderColor: '#58a6ff',
                    backgroundColor: 'rgba(88, 166, 255, 0.1)',
                    tension: 0.4
                },
                {
                    label: 'Output Tokens',
                    data: outputTokens,
                    borderColor: '#3fb950',
                    backgroundColor: 'rgba(63, 185, 80, 0.1)',
                    tension: 0.4
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    labels: {
                        color: '#c9d1d9'
                    }
                }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    ticks: {
                        color: '#8b949e'
                    },
                    grid: {
                        color: '#21262d'
                    }
                },
                x: {
                    ticks: {
                        color: '#8b949e'
                    },
                    grid: {
                        color: '#21262d'
                    }
                }
            }
        }
    });
}

// Update endpoint chart
function updateEndpointChart(endpoints) {
    const ctx = document.getElementById('endpoint-chart').getContext('2d');
    
    if (endpointChart) {
        endpointChart.destroy();
    }
    
    const labels = Object.keys(endpoints);
    const data = Object.values(endpoints);
    
    endpointChart = new Chart(ctx, {
        type: 'doughnut',
        data: {
            labels: labels,
            datasets: [{
                data: data,
                backgroundColor: [
                    '#58a6ff',
                    '#3fb950',
                    '#d29922',
                    '#bc8cff',
                    '#f85149'
                ]
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    position: 'bottom',
                    labels: {
                        color: '#c9d1d9',
                        padding: 15
                    }
                }
            }
        }
    });
}

// Auto-refresh every 30 seconds
setInterval(loadDashboard, 30000);

// Initial load
loadDashboard();
