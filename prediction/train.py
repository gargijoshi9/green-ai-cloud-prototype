from pathlib import Path
import sys
import pandas as pd
from sklearn.metrics import mean_absolute_error

# Ensure prediction directory is on sys.path so model imports work from any working directory
CURRENT_DIR = Path(__file__).resolve().parent
if str(CURRENT_DIR) not in sys.path:
    sys.path.insert(0, str(CURRENT_DIR))

from model import MovingAverageForecaster, LagRegressionForecaster, DifferencedRidgeForecaster

BASE_DIR = CURRENT_DIR.parent
PROCESSED_DIR = BASE_DIR / "dataset" / "processed"


def walk_forward_evaluate(cls, series, train_size, horizon=3, **kwargs):
    """
    Evaluates forecasting performance using walk-forward validation:
    At each step `t` starting from `train_size`, fits the model on available historical data
    and predicts `horizon` steps ahead.
    """
    preds, actuals = [], []
    for t in range(train_size, len(series) - horizon + 1):
        model = cls(**kwargs)
        model.fit(series.iloc[:t].reset_index(drop=True))
        forecast = model.predict(n_steps=horizon)
        preds.extend(forecast)
        actuals.extend(series.iloc[t:t + horizon].values)
    return preds, actuals


df = pd.read_csv(PROCESSED_DIR / "workload_timeseries.csv")
series = df["mean_cpu_avg"]

train_size = int(len(series) * 0.8)
horizon = 3   # realistic short-term forecast, not 29 steps

models_to_test = {
    "Moving Average": (MovingAverageForecaster, {"window": 5}),
    "Lag Regression": (LagRegressionForecaster, {"n_lags": 5}),
    "Differenced Ridge": (DifferencedRidgeForecaster, {"n_lags": 5, "alpha": 1.0}),
}

print(f"{'Model':<20} {'MAE':>10}")
print("-" * 32)
for name, (cls, kwargs) in models_to_test.items():
    preds, actuals = walk_forward_evaluate(cls, series, train_size, horizon=horizon, **kwargs)
    mae = mean_absolute_error(actuals, preds)
    print(f"{name:<20} {mae:>10.4f}")

# Train the best model on the training split and generate final forecast
best_model = DifferencedRidgeForecaster(n_lags=5, alpha=1.0)
best_model.fit(series.iloc[:train_size].reset_index(drop=True))
final_forecast = best_model.predict(n_steps=len(series) - train_size)

# Include corresponding timestamps so downstream modules (e.g., scheduler, carbon merge) can align
test_timestamps = df["timestamp"].iloc[train_size:].values
forecast_df = pd.DataFrame({
    "timestamp": test_timestamps,
    "forecast": final_forecast
})

output_path = PROCESSED_DIR / "forecast_output.csv"
forecast_df.to_csv(output_path, index=False)
print(f"\nSaved updated forecast with timestamps to {output_path}")