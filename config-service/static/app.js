async function loadServices() {
    try {
        const response = await fetch('/api/services');
        const services = await response.json();
        
        if (response.ok) {
            displayServices(services);
        } else {
            showAlert('Error loading services: ' + services.error, 'danger');
        }
    } catch (error) {
        showAlert('Failed to load services: ' + error.message, 'danger');
    }
}

function displayServices(services) {
    const container = document.getElementById('services');
    container.innerHTML = '';
    
    services.forEach(service => {
        const col = document.createElement('div');
        col.className = 'col-md-6 col-lg-4';
        
        const statusClass = service.status.toLowerCase().includes('up') ? 'status-running' : 'status-stopped';
        
        col.innerHTML = `
            <div class="card service-card">
                <div class="card-body">
                    <h6 class="card-title">${service.name}</h6>
                    <p class="card-text">
                        <small class="text-muted">ID: ${service.id.substring(0, 12)}</small><br>
                        <span class="${statusClass}">● ${service.status}</span><br>
                        <small>Image: ${service.image}</small>
                    </p>
                    <button class="btn btn-sm btn-warning btn-restart" onclick="restartService('${service.name}')">
                        Restart
                    </button>
                </div>
            </div>
        `;
        container.appendChild(col);
    });
}

async function restartService(name) {
    try {
        const response = await fetch(`/api/restart/${name}`, { method: 'POST' });
        const result = await response.json();
        
        if (result.status === 'success') {
            showAlert(`Service ${name} restarted successfully`, 'success');
            loadServices(); // Refresh the list
        } else {
            showAlert(`Failed to restart ${name}: ${result.message}`, 'danger');
        }
    } catch (error) {
        showAlert('Error restarting service: ' + error.message, 'danger');
    }
}

function showAlert(message, type) {
    const alertDiv = document.createElement('div');
    alertDiv.className = `alert alert-${type} alert-dismissible fade show`;
    alertDiv.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `;
    
    const container = document.querySelector('.container');
    container.insertBefore(alertDiv, container.firstChild);
    
    // Auto-dismiss after 5 seconds
    setTimeout(() => {
        if (alertDiv.parentNode) {
            alertDiv.remove();
        }
    }, 5000);
}

async function loadConfigFiles() {
    try {
        const response = await fetch('/api/config/files');
        const files = await response.json();
        
        const container = document.getElementById('config-files');
        container.innerHTML = '';
        
        files.forEach(file => {
            const div = document.createElement('div');
            div.className = 'mb-2';
            div.innerHTML = `
                <button class="btn btn-sm btn-outline-primary me-2" onclick="loadConfigFile('${file.path}')">
                    ${file.path}
                </button>
                <small class="text-muted">${file.description}</small>
            `;
            container.appendChild(div);
        });
    } catch (error) {
        showAlert('Failed to load config files: ' + error.message, 'danger');
    }
}

async function loadConfigFile(filePath) {
    try {
        const response = await fetch(`/api/config/file/${filePath}`);
        const data = await response.json();
        
        if (data.error) {
            showAlert(data.error, 'danger');
            return;
        }
        
        // Determine syntax highlighting mode based on file extension
        const fileExtension = filePath.split('.').pop().toLowerCase();
        let mode = 'text/plain';
        
        switch (fileExtension) {
            case 'js':
            case 'json':
                mode = 'javascript';
                break;
            case 'py':
                mode = 'python';
                break;
            case 'yml':
            case 'yaml':
                mode = 'yaml';
                break;
            case 'conf':
                if (filePath.includes('nginx')) {
                    mode = 'nginx';
                } else {
                    mode = 'properties';
                }
                break;
            case 'sql':
                mode = 'sql';
                break;
            case 'env':
                mode = 'properties';
                break;
        }
        
        // Create modal for editing
        const modal = document.createElement('div');
        modal.className = 'modal fade';
        modal.innerHTML = `
            <div class="modal-dialog modal-xl">
                <div class="modal-content">
                    <div class="modal-header">
                        <h5 class="modal-title">Edit ${filePath}</h5>
                        <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                    </div>
                    <div class="modal-body">
                        <textarea id="code-editor" is="highlighted-code" class="form-control" style="height: 500px; font-family: 'Courier New', monospace; resize: vertical;" language="${mode}">${data.content}</textarea>
                    </div>
                    <div class="modal-footer">
                        <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Close</button>
                        <button type="button" class="btn btn-primary" onclick="saveConfigFile('${filePath}')">Save Changes</button>
                    </div>
                </div>
            </div>
        `;
        document.body.appendChild(modal);
        
        const bsModal = new bootstrap.Modal(modal);
        bsModal.show();
        
        // highlighted-code library automatically handles textareas with is="highlighted-code" attribute
        
        modal.addEventListener('hidden.bs.modal', () => {
            // Clean up highlighted-code instance
            document.body.removeChild(modal);
        });
    } catch (error) {
        showAlert('Failed to load config file: ' + error.message, 'danger');
    }
}

async function saveConfigFile(filePath) {
    const content = document.getElementById('code-editor').value;
    
    try {
        const response = await fetch(`/api/config/file/${filePath}`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ content })
        });
        const result = await response.json();
        
        if (result.status === 'success') {
            showAlert('Configuration saved successfully', 'success');
            bootstrap.Modal.getInstance(document.querySelector('.modal')).hide();
        } else {
            showAlert('Failed to save: ' + result.message, 'danger');
        }
    } catch (error) {
        showAlert('Error saving config: ' + error.message, 'danger');
    }
}

async function executeQuery() {
    const query = document.getElementById('db-query').value.trim();
    if (!query) {
        showAlert('Please enter a query', 'warning');
        return;
    }
    
    try {
        const response = await fetch('/api/database/query', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ query })
        });
        const result = await response.json();
        
        const resultsDiv = document.getElementById('query-results');
        
        if (result.status === 'error') {
            resultsDiv.innerHTML = `<div class="alert alert-danger">${result.message}</div>`;
        } else if (result.results) {
            // SELECT query results
            let html = '<table class="table table-sm"><thead><tr>';
            result.columns.forEach(col => {
                html += `<th>${col}</th>`;
            });
            html += '</tr></thead><tbody>';
            
            result.results.forEach(row => {
                html += '<tr>';
                row.forEach(cell => {
                    html += `<td>${cell}</td>`;
                });
                html += '</tr>';
            });
            html += '</tbody></table>';
            resultsDiv.innerHTML = html;
        } else {
            resultsDiv.innerHTML = `<div class="alert alert-success">Query executed successfully. Affected rows: ${result.affected_rows}</div>`;
        }
    } catch (error) {
        showAlert('Error executing query: ' + error.message, 'danger');
    }
}

// Load services and config files on page load
document.addEventListener('DOMContentLoaded', function() {
    loadServices();
    loadConfigFiles();
});