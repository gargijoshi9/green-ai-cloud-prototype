import os
import sys

from flask import Flask, jsonify
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


# ============================================================
# FLASK
# ============================================================

app = Flask(__name__)

CORS(app)


# ============================================================
# SUSTAINABILITY METRICS
# ============================================================

@app.route(
    "/api/sustainability-metrics",
    methods=["GET"]
)
def get_metrics():

    data = {

        "active_instances": 3,

        "energy_consumed_kwh": 4.2,

        "carbon_emission_grams": 115.5,

        "efficiency_score": 92
    }

    return jsonify(data)


# ============================================================
# REAL INFERENCE METRICS
# ============================================================

@app.route(
    "/api/inference-metrics",
    methods=["GET"]
)
def get_inference_metrics():

    try:

        results = run_benchmark(
            retrain=False
        )

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