import os
import sys
from functools import lru_cache
from pathlib import Path

import pandas as pd

from flask import Flask, jsonify, send_from_directory, request
from flask_cors import CORS


# ============================================================
# PROJECT ROOT
# ============================================================

PROJECT_ROOT = os.path.abspath(
    os.path.join(
        os.path.dirname(__file__),
        ".."
    )
)

if PROJECT_ROOT not in sys.path:

    sys.path.insert(
        0,
        PROJECT_ROOT
    )


# ============================================================
# REAL INFERENCE BENCHMARK
# ============================================================

from inference.benchmark import run_benchmark
from scheduler.scheduler import carbon_aware_schedule


# ============================================================
# FLASK
# ============================================================

app = Flask(__name__)

CORS(app)


@app.route("/")
def dashboard_index():
    return send_from_directory(os.path.dirname(__file__), "index.html")


@app.route("/<path:filename>")
def dashboard_asset(filename):
    return send_from_directory(os.path.dirname(__file__), filename)

DATA_DIR = Path(PROJECT_ROOT) / "dataset" / "processed"
CARBON_DATA_PATH = (
    Path(PROJECT_ROOT) / "carbon_data" / "india_carbon_intensity_all_states.csv"
)
ENERGY_PER_WORKLOAD_UNIT = 1e-6

# Canonical configuration defaults
DEFAULT_CAPACITY_FACTOR = 1.5
DEFAULT_MAX_DELAY_MINUTES = 720  # 12 hours


def _load_scheduler_results(
    capacity_factor=DEFAULT_CAPACITY_FACTOR,
    max_delay_minutes=DEFAULT_MAX_DELAY_MINUTES,
):
    category_df = pd.read_csv(DATA_DIR / "workload_by_category.csv")
    forecast_path = DATA_DIR / "forecast_output.csv"

    # Merge/append forecasted future demand from the prediction model
    if forecast_path.exists():
        forecast_df = pd.read_csv(forecast_path)
        ts_path = DATA_DIR / "workload_timeseries.csv"
        avg_vm_count = (
            pd.read_csv(ts_path)["vm_count"].mean()
            if ts_path.exists()
            else 1.0
        )
        # Scale if forecast is mean CPU per VM (~7-10) to match total category cpu_avg (~500k)
        if forecast_df["forecast"].mean() < 1000:
            scaled_forecast = forecast_df["forecast"] * avg_vm_count
        else:
            scaled_forecast = forecast_df["forecast"]

        max_hist_time = category_df["timestamp"].max()
        future_timestamps = max_hist_time + 300 + (forecast_df.index * 300)

        # Allocate future forecast across flexible (Delay-insensitive: ~53%) and interactive (~47%)
        forecast_flexible = pd.DataFrame({
            "timestamp": future_timestamps,
            "cpu_avg": scaled_forecast * 0.53,
            "vm_category": "Delay-insensitive",
        })
        forecast_interactive = pd.DataFrame({
            "timestamp": future_timestamps,
            "cpu_avg": scaled_forecast * 0.47,
            "vm_category": "Interactive",
        })
        category_df = pd.concat(
            [category_df, forecast_flexible, forecast_interactive],
            ignore_index=True,
        )

    carbon_df = pd.read_csv(CARBON_DATA_PATH)
    carbon_df["timestamp"] = pd.to_datetime(carbon_df["timestamp"], utc=True)
    carbon_df = carbon_df.groupby(
        "timestamp", as_index=False
    )["carbon_intensity_gco2_kwh"].mean()

    carbon_start = carbon_df["timestamp"].min()
    category_df["timestamp"] = carbon_start + pd.to_timedelta(
        category_df["timestamp"], unit="s"
    )
    category_df = category_df.rename(
        columns={"cpu_avg": "workload", "vm_category": "workload_type"}
    )
    scheduled = carbon_aware_schedule(
        category_df[["timestamp", "workload", "workload_type"]],
        carbon_df,
        capacity_factor=capacity_factor,
        max_delay_minutes=max_delay_minutes,
    )
    return scheduled, carbon_start


def _build_timeseries(scheduled, carbon_start, energy_reduction=0.0):
    scheduled = scheduled.copy()
    scheduled["original_hour"] = (
        (scheduled["timestamp"] - carbon_start).dt.total_seconds() // 3600
    ).astype(int)
    scheduled["scheduled_hour"] = (
        (scheduled["scheduled_timestamp"] - carbon_start).dt.total_seconds() // 3600
    ).astype(int)
    baseline = scheduled.groupby("original_hour")["workload"].sum()
    optimized = scheduled.groupby("scheduled_hour")["workload"].sum()
    hours = range(int(max(baseline.index.max(), optimized.index.max())) + 1)
    energy_factor = max(0.0, 1.0 - (energy_reduction / 100.0))
    return {
        "labels": [f"{hour:02d}:00" for hour in hours],
        "baselineEnergy": [
            round(float(baseline.get(hour, 0.0) * ENERGY_PER_WORKLOAD_UNIT), 4)
            for hour in hours
        ],
        "optimizedEnergy": [
            round(float(optimized.get(hour, 0.0) * ENERGY_PER_WORKLOAD_UNIT * energy_factor), 4)
            for hour in hours
        ],
    }


@lru_cache(maxsize=16)
def build_dashboard_data(
    capacity_factor=DEFAULT_CAPACITY_FACTOR,
    max_delay_minutes=DEFAULT_MAX_DELAY_MINUTES,
):
    inference = run_benchmark(retrain=False)
    scheduled, carbon_start = _load_scheduler_results(
        capacity_factor=capacity_factor,
        max_delay_minutes=max_delay_minutes,
    )
    baseline_score = float(scheduled["carbon_score_now"].sum())
    optimized_score = float(scheduled["carbon_score_scheduled"].sum())
    carbon_reduction = (
        (baseline_score - optimized_score) / baseline_score * 100
        if baseline_score
        else 0.0
    )
    improvement = inference.get("improvement", {})
    latency_red = float(improvement.get("latency_reduction_percent", 0.0))
    size_red = float(improvement.get("size_reduction_percent", 0.0))
    energy_reduction = latency_red if latency_red > 0 else max(0.0, size_red)
    baseline_energy = float(
        scheduled["workload"].sum() * ENERGY_PER_WORKLOAD_UNIT
    )
    optimized_energy = baseline_energy * max(0.0, 1.0 - (energy_reduction / 100.0))
    delayed = scheduled[scheduled["decision"] == "SHIFTED"]

    return {
        "headline": {
            "carbonReductionPercent": round(carbon_reduction, 2),
            "energyReductionPercent": round(energy_reduction, 2),
        },
        "comparison": {
            "baseline": {
                "energy_kwh": round(baseline_energy, 2),
                "carbon_kg": round(baseline_score / 1_000_000, 2),
            },
            "optimized": {
                "energy_kwh": round(optimized_energy, 2),
                "carbon_kg": round(optimized_score / 1_000_000, 2),
            },
        },
        "scheduler": {
            "totalJobs": int(len(scheduled)),
            "delayedJobs": int(len(delayed)),
            "avgWaitTimeMins": round(float(delayed["delay_minutes"].mean()), 2)
            if not delayed.empty
            else 0.0,
        },
        "inference": inference,
        "timeseries": _build_timeseries(scheduled, carbon_start, energy_reduction=energy_reduction),
        "metadata": {
            "carbon_source": str(CARBON_DATA_PATH.relative_to(PROJECT_ROOT)),
            "workload_source": "dataset/processed/workload_by_category.csv",
            "energy_basis": "Quantization latency reduction proxy applied to scheduled workload",
        },
    }


# ============================================================
# SUSTAINABILITY METRICS
# ============================================================

@app.route(
    "/api/sustainability-metrics",
    methods=["GET"]
)
def get_metrics():
    dashboard = build_dashboard_data()
    return jsonify({
        "active_instances": dashboard["scheduler"]["totalJobs"],
        "energy_consumed_kwh": dashboard["comparison"]["optimized"]["energy_kwh"],
        "carbon_emission_grams": dashboard["comparison"]["optimized"]["carbon_kg"] * 1000,
        "efficiency_score": dashboard["headline"]["carbonReductionPercent"],
    })


@app.route("/api/dashboard", methods=["GET"])
def get_dashboard():
    try:
        capacity = float(request.args.get("capacity", DEFAULT_CAPACITY_FACTOR))
        delay = int(request.args.get("delay", DEFAULT_MAX_DELAY_MINUTES))
        return jsonify(build_dashboard_data(capacity_factor=capacity, max_delay_minutes=delay))
    except Exception as error:
        app.logger.exception("Dashboard data error")
        return jsonify({"success": False, "error": str(error)}), 500


@app.route("/api/run-simulation", methods=["POST", "GET"])
def run_simulation():
    try:
        capacity = float(request.args.get("capacity", DEFAULT_CAPACITY_FACTOR))
        delay = int(request.args.get("delay", DEFAULT_MAX_DELAY_MINUTES))
        if request.args.get("refresh", "false").lower() == "true":
            build_dashboard_data.cache_clear()
        data = build_dashboard_data(capacity_factor=capacity, max_delay_minutes=delay)
        return jsonify({"success": True, "data": data})
    except Exception as error:
        app.logger.exception("Simulation execution error")
        return jsonify({"success": False, "error": str(error)}), 500


# ============================================================
# REAL INFERENCE METRICS
# ============================================================

@app.route(
    "/api/inference-metrics",
    methods=["GET"]
)
def get_inference_metrics():

    try:

        results = build_dashboard_data()["inference"]

        return jsonify({

            "success": True,

            "data": results

        })

    except Exception as e:

        print(
            "Inference benchmark error:",
            str(e)
        )

        return jsonify({

            "success": False,

            "error": str(e)

        }), 500


# ============================================================
# HEALTH
# ============================================================

@app.route(
    "/api/health",
    methods=["GET"]
)
def health_check():

    return jsonify({

        "status":
            "Backend is running successfully"

    })


# ============================================================
# START
# ============================================================

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5001))
    print(f"\n * Green AI Dashboard available at: http://localhost:{port}\n")
    app.run(
        host="0.0.0.0",
        port=port,
        debug=True
    )