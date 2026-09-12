import torch
import torch.nn as nn

from baseline_model import WorkloadModel


def create_quantized_model(input_size=5):

    model = WorkloadModel(input_size)

    # Dynamic INT8 quantization
    quantized_model = torch.quantization.quantize_dynamic(
        model,
        {nn.Linear},
        dtype=torch.qint8
    )

    quantized_model.eval()

    return quantized_model


if __name__ == "__main__":

    model = create_quantized_model()

    sample_input = torch.randn(1, 5)

    with torch.no_grad():
        output = model(sample_input)

    print("Quantized INT8 Model")
    print("Input:", sample_input)
    print("Prediction:", output)