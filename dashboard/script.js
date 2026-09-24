// ============================================================
// GREEN AI DASHBOARD - SCRIPT
// ============================================================

let energyChartInstance = null;
let dashboardData = null;


// ============================================================
// PAGE LOAD
// ============================================================

document.addEventListener("DOMContentLoaded", () => {
    setupTabs();
    loadDashboardData();
});


// ============================================================
// TAB SETUP
// ============================================================

function setupTabs() {

    const navLinks =
        document.querySelectorAll(".nav-link");

    const tabPanes =
        document.querySelectorAll(".tab-pane");

    navLinks.forEach(link => {

        link.addEventListener("click", (event) => {

            event.preventDefault();

            navLinks.forEach(item => {
                item.classList.remove("active");
            });

            tabPanes.forEach(item => {
                item.classList.remove("active");
            });

            link.classList.add("active");

            const targetId =
                link.getAttribute("data-target");

            const target =
                document.getElementById(targetId);

            if (target) {
                target.classList.add("active");
            }

            if (
                targetId === "view-performance" &&
                energyChartInstance
            ) {
                energyChartInstance.resize();
            }

        });

    });
}


// ============================================================
// LOAD DASHBOARD DATA
// ============================================================

async function loadDashboardData() {

    try {

        const response = await fetch(
            "/api/dashboard"
        );

        if (!response.ok) {

            throw new Error(
                `Inference API error: ${response.status}`
            );

        }

        const result = await response.json();

        if (result.success === false) {
            throw new Error(result.error || "Dashboard API failed");
        }

        dashboardData = result;


        console.log(
            "================================"
        );

        console.log(
            "REAL INFERENCE RESULTS"
        );

        console.log(
            "================================"
        );

        console.log(
            "Data source:",
            dashboardData.inference.data.source
        );

        console.log(
            "Workload column:",
            dashboardData.inference.data.column
        );

        console.log(
            "Training samples:",
            dashboardData.inference.data.train_samples
        );

        console.log(
            "Test samples:",
            dashboardData.inference.data.test_samples
        );

        console.log(
            "FP32:",
            dashboardData.inference.baseline
        );

        console.log(
            "INT8:",
            dashboardData.inference.quantized
        );

        console.log(
            "Comparison:",
            dashboardData.inference.improvement
        );


        // Populate dashboard

        populateUI(dashboardData);

        renderChart(
            dashboardData.timeseries
        );


    } catch (error) {

        console.error(
            "Dashboard loading error:",
            error
        );

    }
}


// ============================================================
// POPULATE DASHBOARD
// ============================================================

function populateUI(data) {


    // ========================================================
    // HEADLINE
    // ========================================================

    const headlineNumber =
        document.getElementById(
            "headline-number"
        );

    if (headlineNumber) {

        headlineNumber.innerText =
            `${data.headline.carbonReductionPercent}%`;

    }


    // ========================================================
    // ENERGY KPI
    // ========================================================

    const energyOpt =
        document.getElementById(
            "kpi-energy-opt"
        );

    if (energyOpt) {

        energyOpt.innerText =
            `${data.comparison.optimized.energy_kwh}`;

    }


    const energyBase =
        document.getElementById(
            "kpi-energy-base"
        );

    if (energyBase) {

        energyBase.innerText =
            `${data.comparison.baseline.energy_kwh}`;

    }


    // ========================================================
    // CARBON KPI
    // ========================================================

    const carbonOpt =
        document.getElementById(
            "kpi-carbon-opt"
        );

    if (carbonOpt) {

        carbonOpt.innerText =
            `${data.comparison.optimized.carbon_kg}`;

    }


    const carbonBase =
        document.getElementById(
            "kpi-carbon-base"
        );

    if (carbonBase) {

        carbonBase.innerText =
            `${data.comparison.baseline.carbon_kg}`;

    }


    // ========================================================
    // ENERGY SAVINGS
    // ========================================================

    const energySavings =
        document.getElementById(
            "kpi-energy-savings"
        );

    if (energySavings) {

        energySavings.innerText =
            `${data.headline.energyReductionPercent}%`;

    }


    // ========================================================
    // SCHEDULER
    // ========================================================

    const totalJobs =
        document.getElementById(
            "sch-total"
        );

    if (totalJobs) {

        totalJobs.innerText =
            data.scheduler.totalJobs;

    }


    const delayedJobs =
        document.getElementById(
            "sch-delayed"
        );

    if (delayedJobs) {

        delayedJobs.innerText =
            data.scheduler.delayedJobs;

    }


    const waitTime =
        document.getElementById(
            "sch-wait"
        );

    if (waitTime) {

        waitTime.innerText =
            `${data.scheduler.avgWaitTimeMins} mins`;

    }


    const shiftPercent =
        Math.round(
            (
                data.scheduler.delayedJobs /
                data.scheduler.totalJobs
            ) * 100
        );


    const shiftPercentage =
        document.getElementById(
            "shift-percentage"
        );

    if (shiftPercentage) {

        shiftPercentage.innerText =
            `${shiftPercent}%`;

    }


    const shiftFill =
        document.getElementById(
            "shift-fill"
        );

    if (shiftFill) {

        setTimeout(() => {

            shiftFill.style.width =
                `${shiftPercent}%`;

        }, 100);

    }


    const shiftSummary =
        document.getElementById(
            "shift-summary"
        );

    if (shiftSummary) {

        shiftSummary.innerText =
            `Out of ${data.scheduler.totalJobs} total jobs, ` +
            `${data.scheduler.delayedJobs} flexible/non-urgent jobs ` +
            `were delayed to align with periods of low carbon grid intensity.`;

    }


    // ========================================================
    // REAL FP32 VS INT8 INFERENCE RESULTS
    // ========================================================

    const baseline =
        data.inference.baseline;

    const quantized =
        data.inference.quantized;


    // --------------------------------------------------------
    // FP32 MODEL SIZE
    // --------------------------------------------------------

    const originalSize =
        document.getElementById(
            "inf-size-orig"
        );

    if (originalSize) {

        originalSize.innerText =
            `${Number(baseline.size_kb).toFixed(2)} KB`;

    }


    // --------------------------------------------------------
    // FP32 LATENCY
    // --------------------------------------------------------

    const originalLatency =
        document.getElementById(
            "inf-lat-orig"
        );

    if (originalLatency) {

        originalLatency.innerText =
            `${Number(baseline.latency_ms).toFixed(4)} ms`;

    }


    // --------------------------------------------------------
    // INT8 MODEL SIZE
    // --------------------------------------------------------

    const optimizedSize =
        document.getElementById(
            "inf-size-opt"
        );

    if (optimizedSize) {

        optimizedSize.innerText =
            `${Number(quantized.size_kb).toFixed(2)} KB`;

    }


    // --------------------------------------------------------
    // INT8 LATENCY
    // --------------------------------------------------------

    const optimizedLatency =
        document.getElementById(
            "inf-lat-opt"
        );

    if (optimizedLatency) {

        optimizedLatency.innerText =
            `${Number(quantized.latency_ms).toFixed(4)} ms`;

    }


    // ========================================================
    // OPTIONAL MODEL NAME ELEMENTS
    // ========================================================

    const originalModel =
        document.getElementById(
            "inf-model-orig"
        );

    if (originalModel) {

        originalModel.innerText =
            baseline.model;

    }


    const optimizedModel =
        document.getElementById(
            "inf-model-opt"
        );

    if (optimizedModel) {

        optimizedModel.innerText =
            quantized.model;

    }


    // ========================================================
    // OPTIONAL MAE ELEMENTS
    // ========================================================

    const originalMae =
        document.getElementById(
            "inf-mae-orig"
        );

    if (originalMae) {

        originalMae.innerText =
            Number(baseline.mae).toFixed(4);

    }


    const optimizedMae =
        document.getElementById(
            "inf-mae-opt"
        );

    if (optimizedMae) {

        optimizedMae.innerText =
            Number(quantized.mae).toFixed(4);

    }


    // ========================================================
    // OPTIONAL REDUCTION ELEMENTS
    // ========================================================

    const sizeReduction =
        document.getElementById(
            "inf-size-reduction"
        );

    if (sizeReduction) {

        sizeReduction.innerText =
            `${data.inference.improvement.size_reduction_percent}%`;

    }


    const latencyReduction =
        document.getElementById(
            "inf-latency-reduction"
        );

    if (latencyReduction) {

        latencyReduction.innerText =
            `${data.inference.improvement.latency_reduction_percent}%`;

    }


    const maeChange =
        document.getElementById(
            "inf-mae-change"
        );

    if (maeChange) {

        maeChange.innerText =
            `${data.inference.improvement.mae_change_percent}%`;

    }

}


// ============================================================
// ENERGY CHART
// ============================================================

function renderChart(timeseriesData) {

    const canvas =
        document.getElementById(
            "energyChart"
        );

    if (!canvas) {
        return;
    }


    const ctx =
        canvas.getContext("2d");


    if (energyChartInstance) {

        energyChartInstance.destroy();

    }


    energyChartInstance =
        new Chart(ctx, {

            type: "line",

            data: {

                labels:
                    timeseriesData.labels,

                datasets: [

                    {

                        label:
                            "Baseline Energy Usage (kWh)",

                        data:
                            timeseriesData.baselineEnergy,

                        borderColor:
                            "#94a3b8",

                        backgroundColor:
                            "rgba(148, 163, 184, 0.1)",

                        borderDash:
                            [5, 5],

                        fill:
                            true,

                        tension:
                            0.4

                    },

                    {

                        label:
                            "Optimized System Usage (kWh)",

                        data:
                            timeseriesData.optimizedEnergy,

                        borderColor:
                            "#10b981",

                        backgroundColor:
                            "rgba(16, 185, 129, 0.1)",

                        borderWidth:
                            3,

                        fill:
                            true,

                        tension:
                            0.4

                    }

                ]

            },

            options: {

                responsive:
                    true,

                maintainAspectRatio:
                    false,

                plugins: {

                    legend: {

                        position:
                            "top"

                    },

                    tooltip: {

                        mode:
                            "index",

                        intersect:
                            false

                    }

                },

                scales: {

                    y: {

                        beginAtZero:
                            true,

                        title: {

                            display:
                                true,

                            text:
                                "Energy (kWh)"

                        }

                    },

                    x: {

                        title: {

                            display:
                                true,

                            text:
                                "Time of Day"

                        }

                    }

                }

            }

        });

}


