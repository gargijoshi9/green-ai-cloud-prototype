// Initialize globally so the chart can be updated if needed
let energyChartInstance = null;
let dashboardData = null;

document.addEventListener("DOMContentLoaded", () => {
    setupTabs();
    loadDashboardData();
});

/**
 * Handles switching between sidebar tabs
 */
function setupTabs() {
    const navLinks = document.querySelectorAll('.nav-link');
    const tabPanes = document.querySelectorAll('.tab-pane');

    navLinks.forEach(link => {
        link.addEventListener('click', (e) => {
            e.preventDefault();
            
            // Remove active class from all links and panes
            navLinks.forEach(l => l.classList.remove('active'));
            tabPanes.forEach(p => p.classList.remove('active'));

            // Add active class to clicked link and target pane
            link.classList.add('active');
            const targetId = link.getAttribute('data-target');
            document.getElementById(targetId).classList.add('active');
            
            // If the performance tab is activated, ensure the chart resizes properly
            if (targetId === 'view-performance' && energyChartInstance) {
                energyChartInstance.resize();
            }
        });
    });
}

/**
 * Main function to load data (ready for real backend fetch)
 */
async function loadDashboardData() {
    try {
        // --- BACKEND INTEGRATION POINT ---
        // const response = await fetch('http://localhost:5000/api/dashboard-stats');
        // dashboardData = await response.json();
        
        // --- MOCK DATA ---
        dashboardData = await fetchMockData();

        populateUI(dashboardData);
        renderChart(dashboardData.timeseries);

    } catch (error) {
        console.error("Error loading dashboard data:", error);
    }
}

/**
 * Populates all DOM elements across all tabs with fetched data
 */
function populateUI(data) {
    // Top Headline
    document.getElementById('headline-number').innerText = `${data.headline.carbonReductionPercent}%`;

    // Performance Tab KPIs
    document.getElementById('kpi-energy-opt').innerText = `${data.comparison.optimized.energy_kwh}`;
    document.getElementById('kpi-energy-base').innerText = `${data.comparison.baseline.energy_kwh}`;
    document.getElementById('kpi-carbon-opt').innerText = `${data.comparison.optimized.carbon_kg}`;
    document.getElementById('kpi-carbon-base').innerText = `${data.comparison.baseline.carbon_kg}`;
    document.getElementById('kpi-energy-savings').innerText = `${data.headline.energyReductionPercent}%`;

    // Scheduler Tab Stats
    document.getElementById('sch-total').innerText = data.scheduler.totalJobs;
    document.getElementById('sch-delayed').innerText = data.scheduler.delayedJobs;
    document.getElementById('sch-wait').innerText = `${data.scheduler.avgWaitTimeMins} mins`;

    // Scheduler Progress Bar
    const shiftPercent = Math.round((data.scheduler.delayedJobs / data.scheduler.totalJobs) * 100);
    document.getElementById('shift-percentage').innerText = `${shiftPercent}%`;
    // Add slight timeout for the animation to trigger smoothly
    setTimeout(() => {
        document.getElementById('shift-fill').style.width = `${shiftPercent}%`;
    }, 100);
    
    document.getElementById('shift-summary').innerText = 
        `Out of ${data.scheduler.totalJobs} total jobs, ${data.scheduler.delayedJobs} flexible/non-urgent jobs were delayed to align with periods of low carbon grid intensity.`;

    // Model Optimization Tab
    document.getElementById('inf-size-orig').innerText = `${data.inference.originalSizeMB} MB`;
    document.getElementById('inf-lat-orig').innerText = `${data.inference.originalLatencyMs} ms`;
    document.getElementById('inf-size-opt').innerText = `${data.inference.quantizedSizeMB} MB`;
    document.getElementById('inf-lat-opt').innerText = `${data.inference.optimizedLatencyMs} ms`;
}

/**
 * Renders the Chart.js graph
 */
function renderChart(timeseriesData) {
    const ctx = document.getElementById('energyChart').getContext('2d');
    
    // Destroy existing instance if updating dynamically
    if(energyChartInstance) {
        energyChartInstance.destroy();
    }
    
    energyChartInstance = new Chart(ctx, {
        type: 'line',
        data: {
            labels: timeseriesData.labels,
            datasets: [
                {
                    label: 'Baseline Energy Usage (kWh)',
                    data: timeseriesData.baselineEnergy,
                    borderColor: '#94a3b8',
                    backgroundColor: 'rgba(148, 163, 184, 0.1)',
                    borderDash: [5, 5],
                    fill: true,
                    tension: 0.4
                },
                {
                    label: 'Optimized System Usage (kWh)',
                    data: timeseriesData.optimizedEnergy,
                    borderColor: '#10b981',
                    backgroundColor: 'rgba(16, 185, 129, 0.1)',
                    borderWidth: 3,
                    fill: true,
                    tension: 0.4
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: { position: 'top' },
                tooltip: { mode: 'index', intersect: false }
            },
            scales: {
                y: { beginAtZero: true, title: { display: true, text: 'Energy (kWh)' } },
                x: { title: { display: true, text: 'Time of Day' } }
            }
        }
    });
}

/**
 * Simulates API response
 */
function fetchMockData() {
    return new Promise((resolve) => {
        setTimeout(() => {
            resolve({
                headline: {
                    carbonReductionPercent: 34.5,
                    energyReductionPercent: 28.2
                },
                comparison: {
                    baseline: { energy_kwh: 1450, carbon_kg: 680 },
                    optimized: { energy_kwh: 1041, carbon_kg: 445 }
                },
                scheduler: {
                    totalJobs: 1200,
                    delayedJobs: 420,
                    avgWaitTimeMins: 14.5
                },
                inference: {
                    originalSizeMB: 512,
                    quantizedSizeMB: 128,
                    originalLatencyMs: 120,
                    optimizedLatencyMs: 45
                },
                timeseries: {
                    labels: ["00:00", "04:00", "08:00", "12:00", "16:00", "20:00", "24:00"],
                    baselineEnergy: [120, 90, 180, 250, 220, 190, 140],
                    optimizedEnergy: [135, 110, 150, 180, 170, 155, 141] 
                }
            });
        }, 300); 
    });
}