import torch
import torch.nn as nn


class WorkloadModel(nn.Module):
    """
    Deep neural network for cloud workload prediction.

    Input:
        5 consecutive real workload values (e.g. historical CPU readings).

    Architecture:
        Deep Multi-Layer Perceptron (MLP):
        Input(5) -> 128 -> 256 -> 128 -> 64 -> Output(1)
        with ReLU activations (~75,000 parameters).
        This scale represents a realistic operational inference service where
        quantization compute and memory benefits become tangible.

    Output:
        Predicted next workload value
    """

    def __init__(self, input_size=5):
        super().__init__()

        self.model = nn.Sequential(
            nn.Linear(input_size, 128),
            nn.ReLU(),

            nn.Linear(128, 256),
            nn.ReLU(),

            nn.Linear(256, 128),
            nn.ReLU(),

            nn.Linear(128, 64),
            nn.ReLU(),

            nn.Linear(64, 1)
        )

    def forward(self, x):
        return self.model(x)


def create_baseline_model(input_size=5):

    model = WorkloadModel(input_size)

    model.eval()

    return model


if __name__ == "__main__":

    from inference.data_utils import get_sample_input

    model = create_baseline_model()

    sample_input = get_sample_input()

    with torch.no_grad():
        output = model(sample_input)

    print("Baseline FP32 Model")
    print("-------------------")
    print("Input:", sample_input)
    print("Prediction:", output)