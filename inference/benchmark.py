import os
import time

import torch
import torch.nn as nn

from torch.utils.data import DataLoader
from torch.utils.data import TensorDataset

from inference.baseline_model import WorkloadModel
from inference.quantized_model import create_quantized_model

from inference.data_utils import (
    load_workload_series,
    build_windows,
    WINDOW_SIZE
)


# ============================================================
# CONFIGURATION
# ============================================================

WORKLOAD_COLUMN = "mean_cpu_avg"

TRAIN_RATIO = 0.80

EPOCHS = 100

LEARNING_RATE = 0.001

BATCH_SIZE = 64

BENCHMARK_REPEATS = 10

BENCHMARK_BATCH_SIZE = 256


# ============================================================
# CHECKPOINT
# ============================================================

CHECKPOINT_DIR = os.path.join(
    os.path.dirname(__file__),
    "artifacts"
)

CHECKPOINT_PATH = os.path.join(
    CHECKPOINT_DIR,
    "workload_model_fp32.pth"
)


# ============================================================
# REAL WORKLOAD DATA
# ============================================================

def prepare_real_workload():

    series = load_workload_series(
        WORKLOAD_COLUMN
    )

    if len(series) <= WINDOW_SIZE + 2:

        raise ValueError(
            "Not enough workload data."
        )

    # Time-based split
    split_index = int(
        len(series) * TRAIN_RATIO
    )

    train_series = series.iloc[
        :split_index
    ]

    # Keep previous WINDOW_SIZE values
    # as context for the first test window.

    test_series = series.iloc[
        split_index - WINDOW_SIZE:
    ]

    X_train, y_train = build_windows(
        train_series,
        WINDOW_SIZE
    )

    X_test, y_test = build_windows(
        test_series,
        WINDOW_SIZE
    )

    print()
    print("==========================================")
    print(" REAL WORKLOAD DATA")
    print("==========================================")

    print(
        "Source       : "
        "dataset/processed/workload_timeseries.csv"
    )

    print(
        "Column       :",
        WORKLOAD_COLUMN
    )

    print(
        "Total rows   :",
        len(series)
    )

    print(
        "Training     :",
        len(X_train)
    )

    print(
        "Testing      :",
        len(X_test)
    )

    print(
        "Input shape  :",
        X_train.shape
    )

    print(
        "Target shape :",
        y_train.shape
    )

    return (
        X_train,
        y_train,
        X_test,
        y_test
    )


# ============================================================
# TRAIN FP32 MODEL
# ============================================================

def train_fp32_model(
    X_train,
    y_train
):

    print()
    print("==========================================")
    print(" TRAINING FP32 MODEL")
    print("==========================================")

    torch.manual_seed(42)

    model = WorkloadModel(
        input_size=X_train.shape[1]
    )

    criterion = nn.MSELoss()

    optimizer = torch.optim.Adam(
        model.parameters(),
        lr=LEARNING_RATE
    )

    dataset = TensorDataset(
        X_train,
        y_train
    )

    loader = DataLoader(
        dataset,
        batch_size=BATCH_SIZE,
        shuffle=True
    )

    model.train()

    for epoch in range(EPOCHS):

        total_loss = 0.0

        for X_batch, y_batch in loader:

            optimizer.zero_grad()

            predictions = model(
                X_batch
            )

            loss = criterion(
                predictions,
                y_batch
            )

            loss.backward()

            optimizer.step()

            total_loss += loss.item()

        if (epoch + 1) % 20 == 0:

            average_loss = (
                total_loss / len(loader)
            )

            print(
                f"Epoch {epoch + 1:3d}/{EPOCHS} "
                f"- Loss: {average_loss:.6f}"
            )

    model.eval()

    os.makedirs(
        CHECKPOINT_DIR,
        exist_ok=True
    )

    torch.save(
        model.state_dict(),
        CHECKPOINT_PATH
    )

    print()
    print("FP32 model saved:")
    print(CHECKPOINT_PATH)

    return model


# ============================================================
# LOAD OR TRAIN MODEL
# ============================================================

def get_trained_model(
    X_train,
    y_train,
    retrain=False
):

    model = WorkloadModel(
        input_size=X_train.shape[1]
    )

    if (
        os.path.exists(CHECKPOINT_PATH)
        and not retrain
    ):

        model.load_state_dict(
            torch.load(
                CHECKPOINT_PATH,
                map_location="cpu"
            )
        )

        model.eval()

        print()
        print(
            "Existing trained FP32 model loaded."
        )

        return model

    return train_fp32_model(
        X_train,
        y_train
    )


# ============================================================
# MODEL SIZE
# ============================================================

def get_model_size(model):

    import tempfile

    with tempfile.NamedTemporaryFile(
        delete=False
    ) as f:

        torch.save(
            model.state_dict(),
            f.name
        )

        size = os.path.getsize(
            f.name
        )

    os.remove(f.name)

    return size / 1024


# ============================================================
# MAE
# ============================================================

def evaluate_mae(
    model,
    X,
    y
):

    model.eval()

    with torch.no_grad():

        predictions = model(X)

        mae = torch.mean(
            torch.abs(
                predictions - y
            )
        ).item()

    return mae


# ============================================================
# BENCHMARK
# ============================================================

def benchmark_model(
    model,
    X,
    repeats=BENCHMARK_REPEATS,
    batch_size=BENCHMARK_BATCH_SIZE
):

    model.eval()

    batches = []

    for start in range(
        0,
        len(X),
        batch_size
    ):

        batches.append(
            X[start:start + batch_size]
        )

    # Warm-up
    with torch.no_grad():

        for _ in range(2):

            for batch in batches:
                model(batch)

    # Timed inference
    start_time = time.perf_counter()

    with torch.no_grad():

        for _ in range(repeats):

            for batch in batches:
                model(batch)

    end_time = time.perf_counter()

    total_time = (
        end_time - start_time
    )

    one_pass_time = (
        total_time / repeats
    )

    average_latency = (
        total_time
        /
        (repeats * len(X))
        * 1000
    )

    return (
        one_pass_time,
        average_latency
    )


# ============================================================
# COMPLETE BENCHMARK
# ============================================================

def run_benchmark(
    retrain=False
):

    (
        X_train,
        y_train,
        X_test,
        y_test
    ) = prepare_real_workload()

    # FP32
    fp32_model = get_trained_model(
        X_train,
        y_train,
        retrain=retrain
    )

    fp32_mae = evaluate_mae(
        fp32_model,
        X_test,
        y_test
    )

    (
        fp32_time,
        fp32_latency
    ) = benchmark_model(
        fp32_model,
        X_test
    )

    fp32_size = get_model_size(
        fp32_model
    )

    # INT8
    print()
    print("==========================================")
    print(" CREATING INT8 MODEL")
    print("==========================================")

    int8_model = create_quantized_model(
        trained_model=fp32_model
    )

    int8_mae = evaluate_mae(
        int8_model,
        X_test,
        y_test
    )

    (
        int8_time,
        int8_latency
    ) = benchmark_model(
        int8_model,
        X_test
    )

    int8_size = get_model_size(
        int8_model
    )

    # Comparison
    latency_reduction = (
        (
            fp32_latency
            -
            int8_latency
        )
        /
        fp32_latency
    ) * 100

    size_reduction = (
        (
            fp32_size
            -
            int8_size
        )
        /
        fp32_size
    ) * 100

    mae_change = (
        (
            int8_mae
            -
            fp32_mae
        )
        /
        fp32_mae
    ) * 100

    return {

        "data": {

            "source":
                "dataset/processed/"
                "workload_timeseries.csv",

            "column":
                WORKLOAD_COLUMN,

            "train_samples":
                len(X_train),

            "test_samples":
                len(X_test),

            "window_size":
                WINDOW_SIZE
        },

        "baseline": {

            "model":
                "Baseline FP32 Model",

            "size_kb":
                round(fp32_size, 4),

            "total_time_sec":
                round(fp32_time, 6),

            "latency_ms":
                round(fp32_latency, 4),

            "mae":
                round(fp32_mae, 4)
        },

        "quantized": {

            "model":
                "Quantized INT8 Model",

            "size_kb":
                round(int8_size, 4),

            "total_time_sec":
                round(int8_time, 6),

            "latency_ms":
                round(int8_latency, 4),

            "mae":
                round(int8_mae, 4)
        },

        "improvement": {

            "latency_reduction_percent":
                round(
                    latency_reduction,
                    2
                ),

            "size_reduction_percent":
                round(
                    size_reduction,
                    2
                ),

            "mae_change_percent":
                round(
                    mae_change,
                    2
                )
        }
    }


# ============================================================
# TERMINAL
# ============================================================

if __name__ == "__main__":

    results = run_benchmark(
        retrain=True
    )

    print()
    print("==========================================")
    print(" GREEN AI INFERENCE BENCHMARK")
    print("==========================================")

    print()
    print("REAL WORKLOAD")
    print("------------------------------------------")

    print(
        "Source       :",
        results["data"]["source"]
    )

    print(
        "Column       :",
        results["data"]["column"]
    )

    print(
        "Train samples:",
        results["data"]["train_samples"]
    )

    print(
        "Test samples :",
        results["data"]["test_samples"]
    )

    print()
    print("Baseline FP32 Model")
    print("------------------------------------------")

    print(
        f"Model Size : "
        f"{results['baseline']['size_kb']:.2f} KB"
    )

    print(
        f"Total Time : "
        f"{results['baseline']['total_time_sec']:.4f} sec"
    )

    print(
        f"Latency    : "
        f"{results['baseline']['latency_ms']:.4f} ms/window"
    )

    print(
        f"MAE        : "
        f"{results['baseline']['mae']:.4f}"
    )

    print()
    print("Quantized INT8 Model")
    print("------------------------------------------")

    print(
        f"Model Size : "
        f"{results['quantized']['size_kb']:.2f} KB"
    )

    print(
        f"Total Time : "
        f"{results['quantized']['total_time_sec']:.4f} sec"
    )

    print(
        f"Latency    : "
        f"{results['quantized']['latency_ms']:.4f} ms/window"
    )

    print(
        f"MAE        : "
        f"{results['quantized']['mae']:.4f}"
    )

    print()
    print("COMPARISON")
    print("------------------------------------------")

    print(
        f"Latency Reduction : "
        f"{results['improvement']['latency_reduction_percent']:.2f}%"
    )

    print(
        f"Size Reduction    : "
        f"{results['improvement']['size_reduction_percent']:.2f}%"
    )

    print(
        f"MAE Change        : "
        f"{results['improvement']['mae_change_percent']:.2f}%"
    )

    print()
    print("==========================================")
    print(" Benchmark completed successfully.")
    print("==========================================")