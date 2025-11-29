async function loadServices() {
    const response = await fetch('/api/services');
    const services = await response.json();
    const container = document.getElementById('services');
    
    services.forEach(service => {
        const div = document.createElement('div');
        div.className = 'service';
        div.innerHTML = `
            <h3>${service.name}</h3>
            <p>Status: ${service.status}</p>
            <p>Image: ${service.image}</p>
            <button onclick="restartService('${service.name}')">Restart</button>
        `;
        container.appendChild(div);
    });
}

async function restartService(name) {
    const response = await fetch(`/api/restart/${name}`, { method: 'POST' });
    const result = await response.json();
    alert(result.status);
}

loadServices();