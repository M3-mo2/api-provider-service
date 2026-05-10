// Settings JavaScript

// Protect page
protectPage();

let currentConfig = {};

// Switch tabs
function switchTab(tabName) {
    // Hide all tabs
    document.querySelectorAll('.tab-content').forEach(tab => {
        tab.classList.add('hidden');
    });
    
    // Remove active class from all tab buttons
    document.querySelectorAll('.tab').forEach(btn => {
        btn.classList.remove('active');
    });
    
    // Show selected tab
    document.getElementById(`tab-${tabName}`).classList.remove('hidden');
    
    // Add active class to clicked button
    event.target.classList.add('active');
}

// Load configuration
async function loadConfig() {
    try {
        const response = await apiRequest('/api/dashboard/config');
        
        if (!response.ok) {
            throw new Error('Failed to load config');
        }
        
        currentConfig = await response.json();
        populateSettings();
        
    } catch (error) {
        console.error('Error loading config:', error);
    }
}

// Populate settings from config
function populateSettings() {
    // General
    document.getElementById('server-port').value = currentConfig.server?.port || 10736;
    document.getElementById('detailed-logging').checked = currentConfig.monitoring?.detailed_logging !== false;
    
    // Rotation
    document.getElementById('rotation-enabled').checked = currentConfig.rotation?.enabled !== false;
    document.getElementById('auto-failover').checked = currentConfig.rotation?.auto_failover !== false;
    document.getElementById('health-check-interval').value = currentConfig.rotation?.health_check_interval || 300;
    
    // Rate Limiting
    document.getElementById('rate-limiting-enabled').checked = currentConfig.rate_limiting?.enabled === true;
    document.getElementById('requests-per-minute').value = currentConfig.rate_limiting?.requests_per_minute || 60;
    document.getElementById('requests-per-hour').value = currentConfig.rate_limiting?.requests_per_hour || 1000;
    
    // Backup
    document.getElementById('auto-backup-enabled').checked = currentConfig.database?.auto_backup !== false;
    document.getElementById('backup-interval').value = currentConfig.database?.backup_interval_hours || 10;
}

// Save general settings
async function saveGeneralSettings() {
    const config = {
        'server.port': parseInt(document.getElementById('server-port').value),
        'monitoring.detailed_logging': document.getElementById('detailed-logging').checked
    };
    
    await saveConfig(config, 'General settings saved. Restart required for port changes.');
}

// Save rotation settings
async function saveRotationSettings() {
    const config = {
        'rotation.enabled': document.getElementById('rotation-enabled').checked,
        'rotation.auto_failover': document.getElementById('auto-failover').checked,
        'rotation.health_check_interval': parseInt(document.getElementById('health-check-interval').value)
    };
    
    await saveConfig(config, 'Rotation settings saved successfully');
}

// Save rate limit settings
async function saveRateLimitSettings() {
    const config = {
        'rate_limiting.enabled': document.getElementById('rate-limiting-enabled').checked,
        'rate_limiting.requests_per_minute': parseInt(document.getElementById('requests-per-minute').value),
        'rate_limiting.requests_per_hour': parseInt(document.getElementById('requests-per-hour').value)
    };
    
    await saveConfig(config, 'Rate limiting settings saved successfully');
}

// Save backup settings
async function saveBackupSettings() {
    const config = {
        'database.auto_backup': document.getElementById('auto-backup-enabled').checked,
        'database.backup_interval_hours': parseInt(document.getElementById('backup-interval').value)
    };
    
    await saveConfig(config, 'Backup settings saved successfully');
}

// Save config helper
async function saveConfig(config, successMessage) {
    try {
        const response = await apiRequest('/api/dashboard/config', {
            method: 'PUT',
            body: JSON.stringify(config)
        });
        
        if (!response.ok) {
            throw new Error('Failed to save config');
        }
        
        alert(successMessage);
        loadConfig();
        
    } catch (error) {
        console.error('Error saving config:', error);
        alert('Failed to save settings');
    }
}

// Create backup
async function createBackup() {
    const includeLogs = document.getElementById('include-logs').checked;
    
    if (!confirm('Create a backup now?')) {
        return;
    }
    
    try {
        const response = await apiRequest('/api/dashboard/backup', {
            method: 'POST',
            body: JSON.stringify({ include_logs: includeLogs })
        });
        
        if (!response.ok) {
            throw new Error('Failed to create backup');
        }
        
        const result = await response.json();
        alert(result.message);
        loadBackups();
        
    } catch (error) {
        console.error('Error creating backup:', error);
        alert('Failed to create backup');
    }
}

// Load backups list
async function loadBackups() {
    try {
        const response = await apiRequest('/api/dashboard/backup/list');
        
        if (!response.ok) {
            throw new Error('Failed to load backups');
        }
        
        const backups = await response.json();
        displayBackups(backups);
        
    } catch (error) {
        console.error('Error loading backups:', error);
        document.getElementById('backups-table').innerHTML = 
            '<tr><td colspan="4" class="text-center text-error">Failed to load backups</td></tr>';
    }
}

// Display backups
function displayBackups(backups) {
    const tbody = document.getElementById('backups-table');
    
    if (!backups || backups.length === 0) {
        tbody.innerHTML = '<tr><td colspan="4" class="text-center text-secondary">No backups available</td></tr>';
        return;
    }
    
    tbody.innerHTML = backups.map(backup => `
        <tr>
            <td><code>${backup.filename}</code></td>
            <td>${formatBytes(backup.size)}</td>
            <td>${new Date(backup.created_at).toLocaleString()}</td>
            <td>
                <div class="flex gap-1">
                    <button class="btn btn-primary btn-sm" onclick="restoreBackup('${backup.filename}')">
                        Restore
                    </button>
                    <button class="btn btn-danger btn-sm" onclick="deleteBackup('${backup.filename}')">
                        Delete
                    </button>
                </div>
            </td>
        </tr>
    `).join('');
}

// Format bytes
function formatBytes(bytes) {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return Math.round(bytes / Math.pow(k, i) * 100) / 100 + ' ' + sizes[i];
}

// Restore backup
async function restoreBackup(filename) {
    if (!confirm(`Are you sure you want to restore from "${filename}"? This will overwrite all current data!`)) {
        return;
    }
    
    try {
        const response = await apiRequest('/api/dashboard/backup/restore', {
            method: 'POST',
            body: JSON.stringify({ filename })
        });
        
        if (!response.ok) {
            throw new Error('Failed to restore backup');
        }
        
        const result = await response.json();
        alert(result.message + '\n\nPage will reload...');
        window.location.reload();
        
    } catch (error) {
        console.error('Error restoring backup:', error);
        alert('Failed to restore backup');
    }
}

// Delete backup
async function deleteBackup(filename) {
    if (!confirm(`Delete backup "${filename}"?`)) {
        return;
    }
    
    try {
        const response = await apiRequest(`/api/dashboard/backup/delete`, {
            method: 'POST',
            body: JSON.stringify({ filename })
        });
        
        if (!response.ok) {
            throw new Error('Failed to delete backup');
        }
        
        loadBackups();
        
    } catch (error) {
        console.error('Error deleting backup:', error);
        alert('Failed to delete backup');
    }
}

// Initial load
loadConfig();
loadBackups();
