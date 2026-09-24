import os
import sys
from functools import lru_cache
from pathlib import Path

import pandas as pd

from flask import Flask, jsonify, send_from_directory
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


def _load_scheduler_results():
    category_df = pd.read_csv(DATA_DIR / "workload_by_category.csv")
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
    )
    return scheduled, carbon_start


def _build_timeseries(scheduled, carbon_start):
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
    return {
        "labels": [f"{hour:02d}:00" for hour in hours],
        "baselineEnergy": [
            round(float(baseline.get(hour, 0.0) * ENERGY_PER_WORKLOAD_UNIT), 4)
            for hour in hours
        ],
        "optimizedEnergy": [
            round(float(optimized.get(hour, 0.0) * ENERGY_PER_WORKLOAD_UNIT), 4)
            for hour in hours
        ],
    }


@lru_cache(maxsize=1)
def build_dashboard_data():
    inference = run_benchmark(retrain=False)
    scheduled, carbon_start = _load_scheduler_results()
    baseline_score = float(scheduled["carbon_score_now"].sum())
    optimized_score = float(scheduled["carbon_score_scheduled"].sum())
    carbon_reduction = (
        (baseline_score - optimized_score) / baseline_score * 100
        if baseline_score
        else 0.0
    )
    baseline_energy = float(
        scheduled["workload"].sum() * ENERGY_PER_WORKLOAD_UNIT
    )
    delayed = scheduled[scheduled["decision"] == "SHIFTED"]

    return {
        "headline": {
            "carbonReductionPercent": round(carbon_reduction, 2),
            "energyReductionPercent": 0.0,
        },
        "comparison": {
            "baseline": {
                "energy_kwh": round(baseline_energy, 2),
                "carbon_kg": round(baseline_score / 1_000_000, 2),
            },
            "optimized": {
                "energy_kwh": round(baseline_energy, 2),
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
        "timeseries": _build_timeseries(scheduled, carbon_start),
        "metadata": {
            "carbon_source": str(CARBON_DATA_PATH.relative_to(PROJECT_ROOT)),
            "workload_source": "dataset/processed/workload_by_category.csv",
            "energy_basis": "CPU workload proxy; no power-meter data is available",
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
        return jsonify(build_dashboard_data())
    except Exception as error:
        app.logger.exception("Dashboard data error")
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

    app.run(
        host="0.0.0.0",
        port=5000,
        debug=True
    )