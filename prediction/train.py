import pandas as pd
from model import MovingAverageForecaster

df = pd.read_csv("../dataset/processed/workload_timeseries.csv")
series = df["total_cpu_avg"]

split_point = int(len(series) * 0.8)
train, test = series[:split_point], series[split_point:]

model = MovingAverageForecaster(window=5)
model.fit(train)

forecast = model.predict(n_steps=len(test))

print("First 10 actual values:", test.values[:10])
print("First 10 predicted values:", [round(f, 2) for f in forecast[:10]])

pd.DataFrame({"forecast": forecast}).to_csv("../dataset/processed/forecast_output.csv", index=False)