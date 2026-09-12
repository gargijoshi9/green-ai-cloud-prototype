from flask import Flask, jsonify
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

@app.route('/api/sustainability-metrics', methods=['GET'])
def get_metrics():
    # Mock data for the dashboard skeleton
    mock_data = {
        "active_instances": 3,
        "energy_consumed_kwh": 4.2,
        "carbon_emission_grams": 115.5,
        "efficiency_score": 92
    }
    return jsonify(mock_data)

@app.route('/api/health', methods=['GET'])
def health_check():
    return jsonify({"status": "Backend skeleton is running seamlessly"})

if __name__ == '__main__':
    app.run(port=5000, debug=True)