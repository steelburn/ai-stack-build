// AI Stack Status Monitor Frontend
document.addEventListener('DOMContentLoaded', function() {
    loadDashboard();
});

function toggleServicesPanel() {
    const panel = document.getElementById('services-panel');
    const button = document.querySelector('.services-toggle');

    if (panel.style.display === 'none' || panel.style.display === '') {
        panel.style.display = 'block';
        button.textContent = '🔽 Access Services';
    } else {
        panel.style.display = 'none';
        button.textContent = '🔗 Access Services';
    }
}

async function loadDashboard() {
    try {
        const response = await fetch('/api/status');
        const data = await response.json();

        renderServices(data.services);
        renderCharts(data.services);
    } catch (error) {
        console.error('Error loading dashboard:', error);
        showError('Failed to load dashboard data');
    }
}

function renderServices(services) {
    const tbody = document.getElementById('services-tbody');
    const servicesGrid = document.getElementById('services-grid');
    tbody.innerHTML = '';
    servicesGrid.innerHTML = '';

    // Service URL mapping with display names
    const serviceUrls = {
        'n8n': { url: '/n8n/', name: 'N8N Workflow', description: 'Workflow Automation' },
        'adminer': { url: '/adminer/', name: 'Adminer', description: 'Database Admin' },
        'dify-web': { url: '/dify/', name: 'Dify', description: 'AI App Platform' },
        'flowise': { url: '/flowise/', name: 'Flowise', description: 'AI Workflow Builder' },
        'openwebui': { url: '/openwebui/', name: 'OpenWebUI', description: 'LLM Web Interface' },
        'ollama-webui': { url: '/ollama-webui/', name: 'Ollama WebUI', description: 'Model Management' },
        'litellm': { url: '/litellm/', name: 'LiteLLM', description: 'LLM Router' },
        'openmemory': { url: '/openmemory/', name: 'OpenMemory', description: 'AI Memory System' },
        'ollama': { url: '/ollama/', name: 'Ollama API', description: 'LLM Server' },
        'qdrant': { url: '/qdrant/', name: 'Qdrant', description: 'Vector Database' },
        'dify-api': { url: '/dify/', name: 'Dify API', description: 'AI API' },
        'dify-worker': { url: '/dify/', name: 'Dify Worker', description: 'Background Tasks' }
    };

    Object.entries(services).forEach(([serviceKey, service]) => {
        // Table row
        const row = document.createElement('tr');
        const statusClass = service.status === 'up' ? 'up' : service.status === 'down' ? 'down' : 'disabled';
        const statusIndicatorClass = service.status === 'up' ? 'status-up' : service.status === 'down' ? 'status-down' : 'status-disabled';

        const serviceUrl = serviceUrls[serviceKey];
        const accessLink = serviceUrl ? `<a href="${serviceUrl.url}" target="_blank" class="logs-link">Access Service</a> | ` : '';

        row.innerHTML = `
            <td>${service.name}</td>
            <td>
                <span class="status-indicator ${statusIndicatorClass}"></span>
                <span class="${statusClass}">${service.status.toUpperCase()}</span>
            </td>
            <td class="response-time">${service.response_time || 'N/A'}</td>
            <td>
                ${service.status === 'disabled'
                    ? '<span style="color: #95a5a6;">Service disabled</span>'
                    : `${accessLink}<a href="/logs/${serviceKey}" class="logs-link">View Logs</a> | <a href="/resources" class="logs-link">View Resources</a>`
                }
            </td>
        `;
        tbody.appendChild(row);

        // Service card for grid
        if (serviceUrl) {
            const card = document.createElement('div');
            card.className = 'service-card';

            const statusClassForCard = service.status === 'up' ? 'up' : service.status === 'down' ? 'down' : 'disabled';

            card.innerHTML = `
                <h4>${serviceUrl.name}</h4>
                <p style="margin: 5px 0; color: #666; font-size: 0.9em;">${serviceUrl.description}</p>
                <a href="${serviceUrl.url}" target="_blank">Access Service</a>
                <span class="status ${statusClassForCard}">${service.status.toUpperCase()}</span>
            `;
            servicesGrid.appendChild(card);
        }
    });
}

function renderCharts(services) {
    const serviceNames = Object.keys(services);
    const serviceStatuses = Object.values(services).map(s => s.status);
    const responseTimes = Object.values(services).map(s => s.response_time || 0);

    // Health Chart
    const healthCtx = document.getElementById('healthChart').getContext('2d');
    const healthData = {
        labels: serviceNames,
        datasets: [{
            label: 'Service Status',
            data: serviceStatuses.map(status => status === 'up' ? 1 : status === 'down' ? 0 : 0.5),
            backgroundColor: serviceStatuses.map(status =>
                status === 'up' ? '#27ae60' : status === 'down' ? '#e74c3c' : '#95a5a6'
            ),
            borderColor: serviceStatuses.map(status =>
                status === 'up' ? '#229954' : status === 'down' ? '#c0392b' : '#7f8c8d'
            ),
            borderWidth: 1
        }]
    };
    new Chart(healthCtx, {
        type: 'bar',
        data: healthData,
        options: {
            responsive: true,
            maintainAspectRatio: false,
            scales: {
                y: {
                    beginAtZero: true,
                    max: 1,
                    ticks: {
                        callback: function(value) {
                            return value === 1 ? 'Up' : value === 0 ? 'Down' : 'Disabled';
                        }
                    }
                }
            },
            plugins: {
                legend: { display: false }
            }
        }
    });

    // Response Time Chart
    const responseCtx = document.getElementById('responseTimeChart').getContext('2d');
    const responseData = {
        labels: serviceNames,
        datasets: [{
            label: 'Response Time (ms)',
            data: responseTimes,
            backgroundColor: '#3498db',
            borderColor: '#2980b9',
            borderWidth: 1
        }]
    };
    new Chart(responseCtx, {
        type: 'bar',
        data: responseData,
        options: {
            responsive: true,
            maintainAspectRatio: false,
            scales: {
                y: {
                    beginAtZero: true
                }
            }
        }
    });
}

function showError(message) {
    const container = document.querySelector('.container');
    container.innerHTML = `<div style="text-align: center; color: #e74c3c; padding: 50px;"><h2>Error</h2><p>${message}</p></div>`;
}