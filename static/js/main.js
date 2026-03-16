document.addEventListener("DOMContentLoaded", function() {

    // --- Search Engine Auto-Suggest Logic ---
    const searchInput = document.getElementById('searchInput');
    const searchSuggestions = document.getElementById('searchSuggestions');

    if (searchInput) {
        searchInput.addEventListener('input', function() {
            const query = this.value.trim();
            if (query.length > 0) {
                // Fetch data from our new API
                fetch(`/api/search?q=${encodeURIComponent(query)}`)
                    .then(res => res.json())
                    .then(data => {
                        searchSuggestions.innerHTML = '';
                        if (data.length > 0) {
                            data.forEach(item => {
                                const div = document.createElement('div');
                                div.className = 'p-3 border-bottom search-item';
                                div.style.cursor = 'pointer';
                                // Color coding based on type
                                const badgeColor = item.type === 'Patient' ? 'bg-primary' : 'bg-success';
                                div.innerHTML = `<span class="badge ${badgeColor} me-2">${item.type}</span> <span class="fw-bold text-dark">${item.text}</span>`;
                                div.onclick = () => window.location.href = item.url;
                                searchSuggestions.appendChild(div);
                            });
                            searchSuggestions.style.display = 'block';
                        } else {
                            searchSuggestions.innerHTML = '<div class="p-3 text-muted">No results found.</div>';
                            searchSuggestions.style.display = 'block';
                        }
                    });
            } else {
                searchSuggestions.style.display = 'none';
            }
        });

        // Hide suggestions when clicking outside
        document.addEventListener('click', function(e) {
            if (!searchInput.contains(e.target) && !searchSuggestions.contains(e.target)) {
                searchSuggestions.style.display = 'none';
            }
        });
    }

    // 1. Line Chart (Patient Statistics)
    const ctxLine = document.getElementById('patientChart');
    if (ctxLine) {
        new Chart(ctxLine, {
            type: 'line',
            data: {
                labels: ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul'],
                datasets: [{
                    label: 'Total Patients',
                    data: [1200, 1900, 1500, 2200, 1800, 2500, 1856],
                    borderColor: '#114B43', // Dark Green
                    backgroundColor: 'rgba(17, 75, 67, 0.1)',
                    borderWidth: 3,
                    tension: 0.4, // Smooth curves
                    fill: true
                },
                {
                    label: 'Inpatients',
                    data: [800, 1100, 900, 1400, 1200, 1600, 1200],
                    borderColor: '#158765', // Light Green
                    borderWidth: 3,
                    tension: 0.4
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: { position: 'bottom' }
                },
                scales: {
                    y: { beginAtZero: true, grid: { borderDash: [5, 5] } },
                    x: { grid: { display: false } }
                }
            }
        });
    }

    // 2. Doughnut Chart (Balance)
    const ctxDoughnut = document.getElementById('balanceChart');
    if (ctxDoughnut) {
        new Chart(ctxDoughnut, {
            type: 'doughnut',
            data: {
                labels: ['Income', 'Expense'],
                datasets: [{
                    data: [87, 13], // Representing 87% as in the image
                    backgroundColor: ['#158765', '#E0E0E0'],
                    borderWidth: 0,
                    cutout: '80%' // Makes the doughnut thin
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: { display: false },
                    tooltip: { enabled: false }
                }
            }
        });
    }
});