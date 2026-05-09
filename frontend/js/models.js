// Models Management JavaScript

// Protect page
protectPage();

let currentEditId = null;

// Load models
async function loadModels() {
    try {
        const response = await apiRequest('/api/dashboard/models');
        
        if (!response.ok) {
            throw new Error('Failed to load models');
        }
        
        const models = await response.json();
        displayModels(models);
        
    } catch (error) {
        console.error('Error loading models:', error);
        document.getElementById('models-table').innerHTML = 
            '<tr><td colspan="6" class="text-center text-error">Failed to load models</td></tr>';
    }
}

// Display models in table
function displayModels(models) {
    const tbody = document.getElementById('models-table');
    
    if (!models || models.length === 0) {
        tbody.innerHTML = '<tr><td colspan="6" class="text-center text-secondary">No models configured. Add one to get started.</td></tr>';
        return;
    }
    
    tbody.innerHTML = models.map(model => `
        <tr>
            <td>
                <strong>${model.display_name || model.name}</strong>
                ${model.description ? `<br><small class="text-secondary">${model.description}</small>` : ''}
            </td>
            <td><code style="font-size: 11px;">${model.fireworks_model_id}</code></td>
            <td>
                <span class="badge badge-info">${model.model_type || 'N/A'}</span>
            </td>
            <td>${model.context_length ? model.context_length.toLocaleString() : 'N/A'}</td>
            <td>
                <span class="badge ${model.is_active ? 'badge-success' : 'badge-error'}">
                    ${model.is_active ? '✓ Active' : '✕ Inactive'}
                </span>
            </td>
            <td>
                <div class="flex gap-1">
                    <button class="btn btn-secondary btn-sm" onclick="editModel(${model.id})">Edit</button>
                    <button class="btn btn-secondary btn-sm" onclick="toggleModel(${model.id}, ${!model.is_active})">
                        ${model.is_active ? 'Disable' : 'Enable'}
                    </button>
                    <button class="btn btn-danger btn-sm" onclick="deleteModel(${model.id}, '${model.name}')">Delete</button>
                </div>
            </td>
        </tr>
    `).join('');
}

// Show add model modal
function showAddModelModal() {
    currentEditId = null;
    document.getElementById('modal-title').textContent = 'Add Model';
    document.getElementById('model-form').reset();
    document.getElementById('model-id').value = '';
    document.getElementById('model-active').checked = true;
    document.getElementById('model-modal').classList.remove('hidden');
}

// Hide model modal
function hideModelModal() {
    document.getElementById('model-modal').classList.add('hidden');
    currentEditId = null;
}

// Edit model
async function editModel(id) {
    try {
        const response = await apiRequest('/api/dashboard/models');
        const models = await response.json();
        const model = models.find(m => m.id === id);
        
        if (!model) {
            alert('Model not found');
            return;
        }
        
        currentEditId = id;
        document.getElementById('modal-title').textContent = 'Edit Model';
        document.getElementById('model-id').value = id;
        document.getElementById('model-name').value = model.name;
        document.getElementById('model-fireworks-id').value = model.fireworks_model_id;
        document.getElementById('model-display-name').value = model.display_name || '';
        document.getElementById('model-description').value = model.description || '';
        document.getElementById('model-type').value = model.model_type || 'chat';
        document.getElementById('model-context-length').value = model.context_length || '';
        document.getElementById('model-input-price').value = model.input_price || '';
        document.getElementById('model-output-price').value = model.output_price || '';
        document.getElementById('model-active').checked = model.is_active;
        document.getElementById('model-modal').classList.remove('hidden');
        
    } catch (error) {
        console.error('Error loading model:', error);
        alert('Failed to load model details');
    }
}

// Save model (add or update)
async function saveModel() {
    const id = document.getElementById('model-id').value;
    const name = document.getElementById('model-name').value.trim();
    const fireworksModelId = document.getElementById('model-fireworks-id').value.trim();
    const displayName = document.getElementById('model-display-name').value.trim();
    const description = document.getElementById('model-description').value.trim();
    const modelType = document.getElementById('model-type').value;
    const contextLength = document.getElementById('model-context-length').value;
    const inputPrice = document.getElementById('model-input-price').value;
    const outputPrice = document.getElementById('model-output-price').value;
    const isActive = document.getElementById('model-active').checked;
    
    if (!name || !fireworksModelId) {
        alert('Please fill in all required fields');
        return;
    }
    
    const data = {
        name,
        fireworks_model_id: fireworksModelId,
        display_name: displayName || null,
        description: description || null,
        model_type: modelType,
        context_length: contextLength ? parseInt(contextLength) : null,
        input_price: inputPrice ? parseFloat(inputPrice) : null,
        output_price: outputPrice ? parseFloat(outputPrice) : null,
        is_active: isActive
    };
    
    try {
        let response;
        
        if (id) {
            // Update existing model
            response = await apiRequest(`/api/dashboard/models/${id}`, {
                method: 'PUT',
                body: JSON.stringify(data)
            });
        } else {
            // Create new model
            response = await apiRequest('/api/dashboard/models', {
                method: 'POST',
                body: JSON.stringify(data)
            });
        }
        
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.error || 'Failed to save model');
        }
        
        hideModelModal();
        loadModels();
        
    } catch (error) {
        console.error('Error saving model:', error);
        alert('Failed to save model: ' + error.message);
    }
}

// Toggle model active status
async function toggleModel(id, newStatus) {
    try {
        const response = await apiRequest(`/api/dashboard/models/${id}`, {
            method: 'PUT',
            body: JSON.stringify({ is_active: newStatus })
        });
        
        if (!response.ok) {
            throw new Error('Failed to toggle model');
        }
        
        loadModels();
        
    } catch (error) {
        console.error('Error toggling model:', error);
        alert('Failed to toggle model status');
    }
}

// Delete model
async function deleteModel(id, name) {
    if (!confirm(`Are you sure you want to delete the model "${name}"? This action cannot be undone.`)) {
        return;
    }
    
    try {
        const response = await apiRequest(`/api/dashboard/models/${id}`, {
            method: 'DELETE'
        });
        
        if (!response.ok) {
            throw new Error('Failed to delete model');
        }
        
        loadModels();
        
    } catch (error) {
        console.error('Error deleting model:', error);
        alert('Failed to delete model');
    }
}

// Close modal on overlay click
document.getElementById('model-modal').addEventListener('click', (e) => {
    if (e.target.id === 'model-modal') {
        hideModelModal();
    }
});

// Initial load
loadModels();

// Auto-refresh every 30 seconds
setInterval(loadModels, 30000);
