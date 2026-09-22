import time
import torch

from baseline_model import create_baseline_model
from quantized_model import create_quantized_model
from data_utils import get_sample_input, get_full_dataset


def benchmark_model(model, sample_input, iterations=1000):

    model.eval()

    # Warm-up
    with torch.no_grad():
        for _ in range(100):
            model(sample_input)

    start_time = time.perf_counter()

    with torch.no_grad():
        for _ in range(iterations):
            model(sample_input)

    end_time = time.perf_counter()

    total_time = end_time - start_time

    avg_latency = (total_time / iterations) * 1000

    return total_time, avg_latency


def get_model_size(model):

    import tempfile
    import os

    with tempfile.NamedTemporaryFile(delete=False) as f:

        torch.save(model.state_dict(), f.name)
        size = os.path.getsize(f.name)

    os.remove(f.name)

    return size / 1024


def evaluate_accuracy(model, X, y):
    """Mean absolute error of the model's predictions against real workload targets."""
    model.eval()
    with torch.no_grad():
        predictions = model(X)
        mae = torch.mean(torch.abs(predictions - y)).item()
    return mae


if __name__ == "__main__":

    input_size = 5

    # ---- Real workload data instead of torch.randn(1, input_size) ----
    sample_input = get_sample_input()          # most recent 5 readings -> shape (1, 5)
    X_all, y_all = get_full_dataset()          # full sliding-window dataset for accuracy eval

    print(f"Loaded real workload data: {X_all.shape[0]} windows")
    print(f"Sample input (last {input_size} readings): {sample_input.tolist()}")

    # -----------------------------
    # Baseline Model
    # -----------------------------

    baseline_model = create_baseline_model(input_size)

    baseline_time, baseline_latency = benchmark_model(
        baseline_model,
        sample_input
    )

    baseline_size = get_model_size(baseline_model)
    baseline_mae = evaluate_accuracy(baseline_model, X_all, y_all)

    # -----------------------------
    # Quantized Model
    # -----------------------------

    quantized_model = create_quantized_model(input_size)

    quantized_time, quantized_latency = benchmark_model(
        quantized_model,
        sample_input
    )

    quantized_size = get_model_size(quantized_model)
    quantized_mae = evaluate_accuracy(quantized_model, X_all, y_all)

    # -----------------------------
    # Calculate improvements
    # -----------------------------

    latency_reduction = (
        (baseline_latency - quantized_latency)
        / baseline_latency
    ) * 100

    size_reduction = (
        (baseline_size - quantized_size)
        / baseline_size
    ) * 100

    # -----------------------------
    # Results
    # -----------------------------

    print("\n================================")
    print(" GREEN AI INFERENCE BENCHMARK")
    print("================================")

    print("\nBaseline FP32 Model")
    print("--------------------")
    print(f"Model Size     : {baseline_size:.2f} KB")
    print(f"Total Time     : {baseline_time:.4f} sec")
    print(f"Avg Latency    : {baseline_latency:.4f} ms")
    print(f"MAE (real data): {baseline_mae:.4f}")

    print("\nQuantized INT8 Model")
    print("--------------------")
    print(f"Model Size     : {quantized_size:.2f} KB")
    print(f"Total Time     : {quantized_time:.4f} sec")
    print(f"Avg Latency    : {quantized_latency:.4f} ms")
    print(f"MAE (real data): {quantized_mae:.4f}")

    print("\nImprovement")
    print("--------------------")
    print(f"Latency Reduction : {latency_reduction:.2f}%")
    print(f"Model Size Reduction : {size_reduction:.2f}%")
