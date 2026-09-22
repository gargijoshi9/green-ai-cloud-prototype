import torch
import torch.nn as nn


class WorkloadModel(nn.Module):
    """
    Neural network for workload prediction.

    Input:
        5 consecutive real workload values

    Output:
        next workload value
    """

    def __init__(self, input_size=5):
        super().__init__()

        self.model = nn.Sequential(
            nn.Linear(input_size, 32),
            nn.ReLU(),

            nn.Linear(32, 16),
            nn.ReLU(),

            nn.Linear(16, 1)
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