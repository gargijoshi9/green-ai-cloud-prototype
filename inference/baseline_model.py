import torch
import torch.nn as nn


class WorkloadModel(nn.Module):
    """
    Simple neural network for workload prediction.
    Input: recent workload values
    Output: predicted workload
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

    from data_utils import get_sample_input

    model = create_baseline_model()

    sample_input = get_sample_input()  # real last-5 workload readings

    with torch.no_grad():
        output = model(sample_input)

    print("Baseline FP32 Model")
    print("Input:", sample_input)
    print("Prediction:", output)
