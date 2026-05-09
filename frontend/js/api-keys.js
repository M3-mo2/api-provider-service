// API Keys Management JavaScript

// Protect page
protectPage();

let currentEditId = null;

// Load API keys
async function loadKeys() {
    try {
        const response = await apiRequest('/api/dashboard/keys');
        
        if (!response.ok) {
            throw new Error('Failed to load keys');
        }
        
        const keys = await response.json();
        displayKeys(keys);
        
    } catch (error) {
        console.error('Error loading keys:', error);
        document.getElementById('keys-table').innerHTML = 
            '<tr><td colspan="8" class="text-center text-error">Failed to load keys</td></tr>';
    }
}

// Display keys in table
function displayKeys(keys) {
    const tbody = document.getElementById('keys-table');
    
    if (!keys || keys.length === 0) {
        tbody.innerHTML = '<tr><td colspan="8" class="text-center text-secondary">No API keys configured. Add one to get started.</td></tr>';
        return;
    }
    
    tbody.innerHTML = keys.map(key => `
        <tr>
            <td><strong>${key.name}</strong></td>
            <td><code>${key.api_key}</code></td>
            <td>
                <span class="badge ${key.is_active ? 'badge-success' : 'badge-error'}">
                    ${key.is_active ? '✓ Active' : '✕ Inactive'}
                </span>
            </td>
            <td>${key.priority}</td>
            <td>${key.total_requests.toLocaleString()}</td>
            <td>
                <span class="${key.success_rate >= 95 ? 'text-success' : 'text-warning'}">
                    ${key.success_rate}%
                </span>
            </td>
            <td>${key.last_used_at ? new Date(key.last_used_at).toLocaleString() : 'Never'}</td>
            <td>
                <div class="flex gap-1">
                    <button class="btn btn-secondary btn-sm" onclick="editKey(${key.id})">Edit</button>
                    <button class="btn btn-secondary btn-sm" onclick="toggleKey(${key.id}, ${!key.is_active})">
                        ${key.is_active ? 'Disable' : 'Enable'}
                    </button>
                    <button class="btn btn-danger btn-sm" onclick="deleteKey(${key.id}, '${key.name}')">Delete</button>
                </div>
            </td>
        </tr>
    `).join('');
}

// Show add key modal
function showAddKeyModal() {
    currentEditId = null;
    document.getElementById('modal-title').textContent = 'Add API Key';
    document.getElementById('key-form').reset();
    document.getElementById('key-id').value = '';
    document.getElementById('key-active').checked = true;
    document.getElementById('key-modal').classList.remove('hidden');
}

// Hide key modal
function hideKeyModal() {
    document.getElementById('key-modal').classList.add('hidden');
    currentEditId = null;
}

// Edit key
async function editKey(id) {
    try {
        const response = await apiRequest('/api/dashboard/keys');
        const keys = await response.json();
        const key = keys.find(k => k.id === id);
        
        if (!key) {
            alert('Key not found');
            return;
        }
        
        currentEditId = id;
        document.getElementById('modal-title').textContent = 'Edit API Key';
        document.getElementById('key-id').value = id;
        document.getElementById('key-name').value = key.name;
        document.getElementById('key-value').value = key.api_key.replace('...', ''); // Show masked, user can update
        document.getElementById('key-priority').value = key.priority;
        document.getElementById('key-active').checked = key.is_active;
        document.getElementById('key-modal').classList.remove('hidden');
        
    } catch (error) {
        console.error('Error loading key:', error);
        alert('Failed to load key details');
    }
}

// Save key (add or update)
async function saveKey() {
    const id = document.getElementById('key-id').value;
    const name = document.getElementById('key-name').value.trim();
    const apiKey = document.getElementById('key-value').value.trim();
    const priority = parseInt(document.getElementById('key-priority').value);
    const isActive = document.getElementById('key-active').checked;
    
    if (!name || !apiKey) {
        alert('Please fill in all required fields');
        return;
    }
    
    const data = {
        name,
        api_key: apiKey,
        priority,
        is_active: isActive
    };
    
    try {
        let response;
        
        if (id) {
            // Update existing key
            response = await apiRequest(`/api/dashboard/keys/${id}`, {
                method: 'PUT',
                body: JSON.stringify(data)
            });
        } else {
            // Create new key
            response = await apiRequest('/api/dashboard/keys', {
                method: 'POST',
                body: JSON.stringify(data)
            });
        }
        
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.error || 'Failed to save key');
        }
        
        hideKeyModal();
        loadKeys();
        
    } catch (error) {
        console.error('Error saving key:', error);
        alert('Failed to save key: ' + error.message);
    }
}

// Toggle key active status
async function toggleKey(id, newStatus) {
    try {
        const response = await apiRequest(`/api/dashboard/keys/${id}`, {
            method: 'PUT',
            body: JSON.stringify({ is_active: newStatus })
        });
        
        if (!response.ok) {
            throw new Error('Failed to toggle key');
        }
        
        loadKeys();
        
    } catch (error) {
        console.error('Error toggling key:', error);
        alert('Failed to toggle key status');
    }
}

// Delete key
async function deleteKey(id, name) {
    if (!confirm(`Are you sure you want to delete the key "${name}"? This action cannot be undone.`)) {
        return;
    }
    
    try {
        const response = await apiRequest(`/api/dashboard/keys/${id}`, {
            method: 'DELETE'
        });
        
        if (!response.ok) {
            throw new Error('Failed to delete key');
        }
        
        loadKeys();
        
    } catch (error) {
        console.error('Error deleting key:', error);
        alert('Failed to delete key');
    }
}

// Close modal on overlay click
document.getElementById('key-modal').addEventListener('click', (e) => {
    if (e.target.id === 'key-modal') {
        hideKeyModal();
    }
});

// Initial load
loadKeys();

// Auto-refresh every 30 seconds
setInterval(loadKeys, 30000);
