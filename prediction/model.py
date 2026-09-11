import pandas as pd

class MovingAverageForecaster:
    def __init__(self, window=5):
        self.window = window

    def fit(self, series):
        self.history = series.copy()

    def predict(self, n_steps=6):
        preds = []
        history = self.history.copy()
        for _ in range(n_steps):
            next_val = history[-self.window:].mean()
            preds.append(next_val)
            history = pd.concat([history, pd.Series([next_val])], ignore_index=True)
        return preds