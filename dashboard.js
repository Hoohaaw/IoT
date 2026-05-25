async function fetchData() {
    try {
        const response = await fetch('/data');
        const data = await response.json();
        document.getElementById('temperature').textContent = data.temperature.toFixed(1) + ' °C';
    } catch (error) {
        console.error('Failed to fetch data:', error);
    }
}

fetchData();
setInterval(fetchData, 2000);
