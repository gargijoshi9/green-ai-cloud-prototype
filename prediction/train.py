import pandas as pd
from model import MovingAverageForecaster, LagRegressionForecaster
from sklearn.metrics import mean_absolute_error

df = pd.read_csv("../dataset/processed/workload_timeseries.csv")
series = df["mean_cpu_avg"]

split_point = int(len(series) * 0.8)
train, test = series[:split_point], series[split_point:]

# --- Baseline (for comparison in your Results section) ---
baseline = MovingAverageForecaster(window=5)
baseline.fit(train)
baseline_forecast = baseline.predict(n_steps=len(test))
baseline_mae = mean_absolute_error(test.values, baseline_forecast)

# --- Upgraded model ---
model = LagRegressionForecaster(n_lags=10)
model.fit(train)
forecast = model.predict(n_steps=len(test))
model_mae = mean_absolute_error(test.values, forecast)

print(f"Baseline (Moving Average) MAE: {baseline_mae:.3f}")
print(f"Lag Regression MAE:          {model_mae:.3f}")
print(f"Improvement: {((baseline_mae - model_mae) / baseline_mae * 100):.1f}%")

# Keep the SAME output format — column name and structure unchanged
# so the scheduler/dashboard code doesn't need to change at all
pd.DataFrame({"forecast": forecast}).to_csv("../dataset/processed/forecast_output.csv", index=False)

print("Saved updated forecast to dataset/processed/forecast_output.csv")