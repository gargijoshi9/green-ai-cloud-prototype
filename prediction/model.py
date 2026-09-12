import pandas as pd
import numpy as np
from sklearn.linear_model import LinearRegression


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


class LagRegressionForecaster:
    """
    Predicts the next value using the previous `n_lags` values as input features.
    E.g. with n_lags=3: predicts t using [t-1, t-2, t-3].
    """

    def __init__(self, n_lags=5):
        self.n_lags = n_lags
        self.model = LinearRegression()

    def _make_lag_features(self, series):
        df = pd.DataFrame({"y": series.values})
        for lag in range(1, self.n_lags + 1):
            df[f"lag_{lag}"] = df["y"].shift(lag)
        df = df.dropna().reset_index(drop=True)
        X = df[[f"lag_{lag}" for lag in range(1, self.n_lags + 1)]]
        y = df["y"]
        return X, y

    def fit(self, series):
        self.history = series.copy()
        X, y = self._make_lag_features(series)
        self.model.fit(X, y)

    def predict(self, n_steps=6):
        preds = []
        history = list(self.history.values[-self.n_lags:])
        for _ in range(n_steps):
            X_input = pd.DataFrame([history[-self.n_lags:][::-1]],
                                    columns=[f"lag_{lag}" for lag in range(1, self.n_lags + 1)])
            next_val = self.model.predict(X_input)[0]
            preds.append(next_val)
            history.append(next_val)
        return preds