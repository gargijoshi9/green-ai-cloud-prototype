// ============================================================
// GREEN AI DASHBOARD - SCRIPT & INTERACTIVE SIMULATION ENGINE
// ============================================================

let energyChartInstance = null;
let dashboardData = null;
let toastTimeout = null;


// ============================================================
// PAGE INITIALIZATION
// ============================================================

document.addEventListener("DOMContentLoaded", () => {
    setupTabs();
    setupSimulationControls();
    loadDashboardData();
});


// ============================================================
// TAB NAVIGATION SETUP
// ============================================================

function setupTabs() {
    const navLinks = document.querySelectorAll(".nav-link");
    const tabPanes = document.querySelectorAll(".tab-pane");

    navLinks.forEach(link => {
        link.addEventListener("click", (event) => {
            event.preventDefault();

            navLinks.forEach(item => item.classList.remove("active"));
            tabPanes.forEach(item => item.classList.remove("active"));

            link.classList.add("active");

            const targetId = link.getAttribute("data-target");
            const target = document.getElementById(targetId);

            if (target) {
                target.classList.add("active");
            }

            if (targetId === "view-performance" && energyChartInstance) {
                energyChartInstance.resize();
            }
        });
    });
}


// ============================================================
// SIMULATION CONTROLS & EVENT LISTENERS
// ============================================================

function setupSimulationControls() {
    const runBtn = document.getElementById("run-sim-btn");
    const delaySelect = document.getElementById("param-delay");
    const capacitySelect = document.getElementById("param-capacity");

    if (runBtn) {
        runBtn.addEventListener("click", () => {
            triggerSimulation(true);
        });
    }

    if (delaySelect) {
        delaySelect.addEventListener("change", () => {
            triggerSimulation(false);
        });
    }

    if (capacitySelect) {
        capacitySelect.addEventListener("change", () => {
            triggerSimulation(false);
        });
    }
}


// ============================================================
// INITIAL DATA LOAD
// ============================================================

async function loadDashboardData() {
    try {
        const delay = document.getElementById("param-delay")?.value || 360;
        const capacity = document.getElementById("param-capacity")?.value || 1.25;

        const response = await fetch(`/api/dashboard?delay=${delay}&capacity=${capacity}`);

        if (!response.ok) {
            throw new Error(`Dashboard API error: ${response.status}`);
        }

        const result = await response.json();

        if (result.success === false) {
            throw new Error(result.error || "Dashboard data generation failed");
        }

        dashboardData = result;

        populateUI(dashboardData, true);
        renderChart(dashboardData.timeseries, true);
        updateLastEvaluatedTime();

    } catch (error) {
        console.error("Dashboard initialization error:", error);
        showToast("Error loading dashboard data: " + error.message, true);
    }
}


// ============================================================
// TRIGGER LIVE SIMULATION
// ============================================================

async function triggerSimulation(forceRefresh = false) {
    const runBtn = document.getElementById("run-sim-btn");
    const btnIcon = document.getElementById("sim-btn-icon");
    const btnText = document.getElementById("sim-btn-text");
    const statusDot = document.getElementById("status-dot");
    const statusText = document.getElementById("status-text");

    const delay = document.getElementById("param-delay")?.value || 360;
    const capacity = document.getElementById("param-capacity")?.value || 1.25;

    // Enter Loading State
    if (runBtn) {
        runBtn.disabled = true;
        if (btnIcon) btnIcon.className = "fa-solid fa-spinner fa-spin";
        if (btnText) btnText.innerText = "Simulating Pipeline...";
    }
    if (statusDot) {
        statusDot.style.backgroundColor = "#f59e0b"; // Warning amber
    }
    if (statusText) {
        statusText.innerText = "Recalculating Carbon Schedule...";
    }

    try {
        const response = await fetch(
            `/api/run-simulation?delay=${delay}&capacity=${capacity}&refresh=${forceRefresh}`
        );

        if (!response.ok) {
            throw new Error(`Simulation API failed: ${response.status}`);
        }

        const result = await response.json();

        if (result.success === false) {
            throw new Error(result.error || "Simulation failed to compute");
        }

        dashboardData = result.data;

        // Transition UI with smooth animations
        populateUI(dashboardData, true);
        renderChart(dashboardData.timeseries, true);
        updateLastEvaluatedTime();

        const delayedCount = dashboardData.scheduler.delayedJobs;
        const carbonSaved = dashboardData.headline.carbonReductionPercent;
        showToast(`Simulation complete: ${delayedCount} jobs deferred to clean energy slots (${carbonSaved}% carbon avoided).`);

    } catch (error) {
        console.error("Simulation error:", error);
        showToast("Simulation error: " + error.message, true);
    } finally {
        // Restore Ready State
        if (runBtn) {
            runBtn.disabled = false;
            if (btnIcon) btnIcon.className = "fa-solid fa-play";
            if (btnText) btnText.innerText = "Run Live Simulation";
        }
        if (statusDot) {
            statusDot.style.backgroundColor = "#10b981"; // Success green
        }
        if (statusText) {
            statusText.innerText = "Live System Active";
        }
    }
}


// ============================================================
// ============================================================
// NUMBER FORMATTING WITH COMMAS (e.g. 98,013.76)
// ============================================================

function formatNumberWithCommas(val, decimals = 2) {
    const num = Number(val);
    if (isNaN(num)) return val;
    return num.toLocaleString("en-US", {
        minimumFractionDigits: decimals,
        maximumFractionDigits: decimals
    });
}


// ============================================================
// ANIMATED NUMBER COUNTER (Cubic Easing with Commas)
// ============================================================

function animateNumber(element, target, duration = 900, decimals = 2, prefix = "", suffix = "") {
    if (!element) return;

    const currentRaw = element.getAttribute("data-val");
    const startVal = currentRaw !== null ? parseFloat(currentRaw) : 0;
    const endVal = parseFloat(target) || 0;

    element.setAttribute("data-val", endVal);

    if (isNaN(startVal) || isNaN(endVal)) {
        element.innerText = `${prefix}${formatNumberWithCommas(target, decimals)}${suffix}`;
        return;
    }

    const startTime = performance.now();

    function frame(now) {
        const elapsed = now - startTime;
        const progress = Math.min(elapsed / duration, 1.0);
        // Ease out cubic: 1 - (1 - t)^3
        const easeOut = 1 - Math.pow(1 - progress, 3);
        const current = startVal + (endVal - startVal) * easeOut;

        element.innerText = `${prefix}${formatNumberWithCommas(current, decimals)}${suffix}`;

        if (progress < 1.0) {
            requestAnimationFrame(frame);
        } else {
            element.innerText = `${prefix}${formatNumberWithCommas(endVal, decimals)}${suffix}`;
        }
    }

    requestAnimationFrame(frame);
}


// ============================================================
// POPULATE DASHBOARD UI
// ============================================================

function populateUI(data, animate = true) {
    if (!data) return;

    const animDuration = animate ? 850 : 0;

    // 1. Headline Metric
    const headlineNumber = document.getElementById("headline-number");
    if (headlineNumber) {
        if (animate) {
            animateNumber(headlineNumber, data.headline.carbonReductionPercent, animDuration, 2, "", "%");
        } else {
            headlineNumber.innerText = `${formatNumberWithCommas(data.headline.carbonReductionPercent, 2)}%`;
        }
    }

    // 2. Energy KPI
    const energyOpt = document.getElementById("kpi-energy-opt");
    if (energyOpt) {
        if (animate) {
            animateNumber(energyOpt, data.comparison.optimized.energy_kwh, animDuration, 2, "", " kWh");
        } else {
            energyOpt.innerText = `${formatNumberWithCommas(data.comparison.optimized.energy_kwh, 2)} kWh`;
        }
    }

    const energyBase = document.getElementById("kpi-energy-base");
    if (energyBase) {
        if (animate) {
            animateNumber(energyBase, data.comparison.baseline.energy_kwh, animDuration, 2, "", "");
        } else {
            energyBase.innerText = `${formatNumberWithCommas(data.comparison.baseline.energy_kwh, 2)}`;
        }
    }

    // 3. Carbon KPI
    const carbonOpt = document.getElementById("kpi-carbon-opt");
    if (carbonOpt) {
        if (animate) {
            animateNumber(carbonOpt, data.comparison.optimized.carbon_kg, animDuration, 2, "", " kg CO₂");
        } else {
            carbonOpt.innerText = `${formatNumberWithCommas(data.comparison.optimized.carbon_kg, 2)} kg CO₂`;
        }
    }

    const carbonBase = document.getElementById("kpi-carbon-base");
    if (carbonBase) {
        if (animate) {
            animateNumber(carbonBase, data.comparison.baseline.carbon_kg, animDuration, 2, "", "");
        } else {
            carbonBase.innerText = `${formatNumberWithCommas(data.comparison.baseline.carbon_kg, 2)}`;
        }
    }

    // 4. Overall Energy Savings %
    const energySavings = document.getElementById("kpi-energy-savings");
    if (energySavings) {
        if (animate) {
            animateNumber(energySavings, data.headline.energyReductionPercent, animDuration, 2, "", "%");
        } else {
            energySavings.innerText = `${formatNumberWithCommas(data.headline.energyReductionPercent, 2)}%`;
        }
    }

    // 5. Scheduler Statistics
    const totalJobs = document.getElementById("sch-total");
    if (totalJobs) {
        if (animate) {
            animateNumber(totalJobs, data.scheduler.totalJobs, animDuration, 0, "", "");
        } else {
            totalJobs.innerText = formatNumberWithCommas(data.scheduler.totalJobs, 0);
        }
    }

    const delayedJobs = document.getElementById("sch-delayed");
    if (delayedJobs) {
        if (animate) {
            animateNumber(delayedJobs, data.scheduler.delayedJobs, animDuration, 0, "", "");
        } else {
            delayedJobs.innerText = formatNumberWithCommas(data.scheduler.delayedJobs, 0);
        }
    }

    const waitTime = document.getElementById("sch-wait");
    if (waitTime) {
        if (animate) {
            animateNumber(waitTime, data.scheduler.avgWaitTimeMins, animDuration, 2, "", " mins");
        } else {
            waitTime.innerText = `${formatNumberWithCommas(data.scheduler.avgWaitTimeMins, 2)} mins`;
        }
    }

    // Shift Progress Bar & Summary
    const total = data.scheduler.totalJobs || 1;
    const delayed = data.scheduler.delayedJobs || 0;
    const shiftPercent = Math.round((delayed / total) * 100);

    const shiftPercentage = document.getElementById("shift-percentage");
    if (shiftPercentage) {
        if (animate) {
            animateNumber(shiftPercentage, shiftPercent, animDuration, 0, "", "%");
        } else {
            shiftPercentage.innerText = `${shiftPercent}%`;
        }
    }

    const shiftFill = document.getElementById("shift-fill");
    if (shiftFill) {
        shiftFill.style.width = "0%";
        setTimeout(() => {
            shiftFill.style.width = `${Math.min(100, Math.max(0, shiftPercent))}%`;
        }, 80);
    }

    const shiftSummary = document.getElementById("shift-summary");
    if (shiftSummary) {
        shiftSummary.innerText =
            `Out of ${formatNumberWithCommas(data.scheduler.totalJobs, 0)} total evaluated compute jobs, ` +
            `${formatNumberWithCommas(data.scheduler.delayedJobs, 0)} flexible/non-urgent jobs were deferred ` +
            `to future cleaner energy windows.`;
    }

    // 6. Model Optimization Metrics (FP32 vs INT8)
    if (data.inference) {
        const baseline = data.inference.baseline;
        const quantized = data.inference.quantized;

        const origSize = document.getElementById("inf-size-orig");
        if (origSize) origSize.innerText = `${Number(baseline.size_kb).toFixed(2)} KB`;

        const origLat = document.getElementById("inf-lat-orig");
        if (origLat) origLat.innerText = `${Number(baseline.latency_ms).toFixed(4)} ms`;

        const optSize = document.getElementById("inf-size-opt");
        if (optSize) optSize.innerText = `${Number(quantized.size_kb).toFixed(2)} KB`;

        const optLat = document.getElementById("inf-lat-opt");
        if (optLat) optLat.innerText = `${Number(quantized.latency_ms).toFixed(4)} ms`;
    }
}


// ============================================================
// CHART RENDERING & SMOOTH TRANSITION
// ============================================================

function renderChart(timeseriesData, animate = true) {
    const canvas = document.getElementById("energyChart");
    if (!canvas || !timeseriesData) return;

    const ctx = canvas.getContext("2d");

    // If chart already exists, update data smoothly
    if (energyChartInstance) {
        energyChartInstance.data.labels = timeseriesData.labels;
        energyChartInstance.data.datasets[0].data = timeseriesData.baselineEnergy;
        energyChartInstance.data.datasets[1].data = timeseriesData.optimizedEnergy;

        energyChartInstance.update({
            duration: animate ? 950 : 0,
            easing: "easeOutQuart"
        });
        return;
    }

    // Initialize new Chart instance
    energyChartInstance = new Chart(ctx, {
        type: "line",
        data: {
            labels: timeseriesData.labels,
            datasets: [
                {
                    label: "Baseline Energy Usage (kWh)",
                    data: timeseriesData.baselineEnergy,
                    borderColor: "#94a3b8",
                    backgroundColor: "rgba(148, 163, 184, 0.12)",
                    borderDash: [5, 5],
                    borderWidth: 2,
                    fill: true,
                    tension: 0.35,
                    pointRadius: 2,
                    pointHoverRadius: 5,
                },
                {
                    label: "Green AI Scheduled System (kWh)",
                    data: timeseriesData.optimizedEnergy,
                    borderColor: "#10b981",
                    backgroundColor: "rgba(16, 185, 129, 0.12)",
                    borderWidth: 3,
                    fill: true,
                    tension: 0.35,
                    pointRadius: 3,
                    pointHoverRadius: 6,
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            animation: {
                duration: animate ? 1100 : 0,
                easing: "easeOutQuart"
            },
            plugins: {
                legend: {
                    position: "top",
                    labels: {
                        font: { family: "'Inter', sans-serif", size: 12, weight: 600 },
                        color: "#334155",
                        usePointStyle: true,
                        padding: 20
                    }
                },
                tooltip: {
                    mode: "index",
                    intersect: false,
                    backgroundColor: "rgba(15, 23, 42, 0.9)",
                    titleFont: { size: 13, weight: 700 },
                    bodyFont: { size: 12 },
                    padding: 12,
                    cornerRadius: 8,
                    callbacks: {
                        label: function(context) {
                            const label = context.dataset.label || "";
                            const val = context.parsed.y;
                            return ` ${label}: ${formatNumberWithCommas(val, 2)} kWh`;
                        }
                    }
                }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    ticks: {
                        callback: function(value) {
                            return formatNumberWithCommas(value, 0);
                        }
                    },
                    title: {
                        display: true,
                        text: "Energy Consumption (kWh)",
                        color: "#64748b",
                        font: { size: 12, weight: 600 }
                    },
                    grid: { color: "rgba(226, 232, 240, 0.6)" }
                },
                x: {
                    title: {
                        display: true,
                        text: "Simulation Timeline (Hours)",
                        color: "#64748b",
                        font: { size: 12, weight: 600 }
                    },
                    grid: { display: false }
                }
            }
        }
    });
}


// ============================================================
// TOAST NOTIFICATIONS & METADATA
// ============================================================

function showToast(message, isError = false) {
    const toast = document.getElementById("sim-toast");
    const toastMsg = document.getElementById("sim-toast-msg");

    if (!toast || !toastMsg) return;

    if (toastTimeout) clearTimeout(toastTimeout);

    toastMsg.innerText = message;
    toast.style.borderColor = isError ? "#ef4444" : "#10b981";

    const icon = toast.querySelector("i");
    if (icon) {
        icon.className = isError ? "fa-solid fa-circle-exclamation" : "fa-solid fa-circle-check";
        icon.style.color = isError ? "#ef4444" : "#10b981";
    }

    toast.classList.add("show");

    toastTimeout = setTimeout(() => {
        toast.classList.remove("show");
    }, 3800);
}

function updateLastEvaluatedTime() {
    const timeSpan = document.getElementById("last-run-time");
    if (timeSpan) {
        const now = new Date();
        timeSpan.innerText = now.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit", second: "2-digit" });
    }
}
