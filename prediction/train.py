import pandas as pd
from model import MovingAverageForecaster, LagRegressionForecaster, DifferencedRidgeForecaster
from sklearn.metrics import mean_absolute_error


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


df = pd.read_csv("../dataset/processed/workload_timeseries.csv")
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

# Keep the SAME output format — column name and structure unchanged
# so the scheduler/dashboard code doesn't need to change at all
best_model = DifferencedRidgeForecaster(n_lags=5, alpha=1.0)
best_model.fit(series.iloc[:train_size].reset_index(drop=True))
final_forecast = best_model.predict(n_steps=len(series) - train_size)

pd.DataFrame({"forecast": final_forecast}).to_csv("../dataset/processed/forecast_output.csv", index=False)
print("\nSaved updated forecast to dataset/processed/forecast_output.csv")