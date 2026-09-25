import os
import numpy as np
import torch
import pandas as pd


_THIS_DIR = os.path.dirname(os.path.abspath(__file__))
PROCESSED_CSV = os.path.join(_THIS_DIR, "..", "dataset", "processed", "workload_timeseries.csv")

WINDOW_SIZE = 5  # must match input_size in WorkloadModel


def load_workload_series(column: str = "mean_cpu_avg") -> pd.Series:
    """
    Loads the processed workload time series and returns one column
    as a sorted-by-timestamp pandas Series.

    column options: "total_cpu_avg", "mean_cpu_avg", "vm_count"
    """
    df = pd.read_csv(PROCESSED_CSV)
    df = df.sort_values("timestamp").reset_index(drop=True)

    if column not in df.columns:
        raise ValueError(f"Column '{column}' not found. Available: {list(df.columns)}")

    return df[column]


def build_windows(series: pd.Series, window_size: int = WINDOW_SIZE):
    """
    Converts a 1D workload series into (X, y) sliding windows:
    X[i] = [t_i, t_i+1, ..., t_i+window_size-1]
    y[i] = t_i+window_size   (the next value to predict)

    Returns two torch.FloatTensors: X of shape (N, window_size), y of shape (N, 1)
    """
    values = series.values.astype("float32")

    X, y = [], []
    for i in range(len(values) - window_size):
        X.append(values[i : i + window_size])
        y.append(values[i + window_size])

    X = torch.tensor(np.array(X), dtype=torch.float32)
    y = torch.tensor(np.array(y), dtype=torch.float32).unsqueeze(1)
    return X, y


def get_sample_input(column: str = "mean_cpu_avg") -> torch.Tensor:
    """
    Returns a single real input window of shape (1, WINDOW_SIZE) —
    a drop-in replacement for `torch.randn(1, 5)` in benchmark.py.
    Uses the most recent WINDOW_SIZE readings.
    """
    series = load_workload_series(column)
    if len(series) < WINDOW_SIZE:
        raise ValueError(
            f"Not enough data: need at least {WINDOW_SIZE} rows, got {len(series)}"
        )
    last_window = series.values[-WINDOW_SIZE:].astype("float32")
    return torch.tensor(last_window, dtype=torch.float32).unsqueeze(0)  # shape (1, 5)


def get_full_dataset(column: str = "mean_cpu_avg"):
    """
    Returns the full (X, y) dataset built from real workload data,
    for benchmarking accuracy across many samples rather than just one input.
    """
    series = load_workload_series(column)
    return build_windows(series, WINDOW_SIZE)


if __name__ == "__main__":
    # Quick sanity check when run directly: python inference/data_utils.py
    sample = get_sample_input()
    print("Sample input shape:", sample.shape)
    print("Sample input values:", sample)

    X, y = get_full_dataset()
    print(f"Full dataset: X={X.shape}, y={y.shape}")
