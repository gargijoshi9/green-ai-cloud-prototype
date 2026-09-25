import copy
import os

import torch
import torch.nn as nn

from inference.baseline_model import WorkloadModel


def _ensure_quantized_engine():
    """Ensure a supported quantized engine is active (e.g. qnnpack on ARM/macOS, fbgemm on x86)."""
    supported = torch.backends.quantized.supported_engines
    if "qnnpack" in supported:
        torch.backends.quantized.engine = "qnnpack"
    elif "fbgemm" in supported:
        torch.backends.quantized.engine = "fbgemm"


def create_quantized_model(
    input_size=5,
    trained_model=None
):
    """
    Creates an INT8 model from an already trained FP32 model.
    """

    if trained_model is None:
        raise ValueError(
            "A trained FP32 model must be provided "
            "for INT8 quantization."
        )

    _ensure_quantized_engine()

    # Copy trained FP32 model
    model = copy.deepcopy(trained_model)

    model.eval()

    # Dynamic INT8 quantization
    quantized_model = torch.quantization.quantize_dynamic(
        model,
        {nn.Linear},
        dtype=torch.qint8
    )

    quantized_model.eval()

    return quantized_model


if __name__ == "__main__":

    checkpoint_path = os.path.join(
        os.path.dirname(__file__),
        "artifacts",
        "workload_model_fp32.pth"
    )

    if not os.path.exists(checkpoint_path):

        print("Trained FP32 model not found.")
        print("Run benchmark.py first.")

    else:

        model = WorkloadModel(
            input_size=5
        )

        model.load_state_dict(
            torch.load(
                checkpoint_path,
                map_location="cpu"
            )
        )

        model.eval()

        quantized_model = create_quantized_model(
            trained_model=model
        )

        print(
            "INT8 quantized model created successfully."
        )