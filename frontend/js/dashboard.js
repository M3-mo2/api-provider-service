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
                    ${key.success_rate >= 95 ? 'Healthy' : 'Warning'}
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
                    borderColor: '#00d4ff',
                    backgroundColor: 'rgba(0, 212, 255, 0.08)',
                    tension: 0.4,
                    borderWidth: 2,
                    pointRadius: 3,
                    pointBackgroundColor: '#00d4ff'
                },
                {
                    label: 'Output Tokens',
                    data: outputTokens,
                    borderColor: '#f0b429',
                    backgroundColor: 'rgba(240, 180, 41, 0.08)',
                    tension: 0.4,
                    borderWidth: 2,
                    pointRadius: 3,
                    pointBackgroundColor: '#f0b429'
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    labels: {
                        color: '#7a7a9a',
                        font: { family: "'JetBrains Mono', monospace", size: 11 },
                        padding: 16
                    }
                }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    ticks: {
                        color: '#4e4e6a',
                        font: { family: "'JetBrains Mono', monospace", size: 11 }
                    },
                    grid: {
                        color: '#1e1e32'
                    }
                },
                x: {
                    ticks: {
                        color: '#4e4e6a',
                        font: { family: "'JetBrains Mono', monospace", size: 11 }
                    },
                    grid: {
                        color: '#1e1e32'
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
                    '#f0b429',
                    '#00d4ff',
                    '#a78bfa',
                    '#22c55e',
                    '#ef4444'
                ],
                borderColor: '#0e0e16',
                borderWidth: 2
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    position: 'bottom',
                    labels: {
                        color: '#7a7a9a',
                        font: { family: "'JetBrains Mono', monospace", size: 11 },
                        padding: 16
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
