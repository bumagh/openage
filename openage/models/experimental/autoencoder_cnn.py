"""
Experimental: Autoencoder + CNN architecture for biological age estimation.

This is a research prototype. The primary production model is the
tree-based GradientBoosting model in openage.models.tree.

Architecture:
  Encoder (42 → 75 → 55 → 30) → latent space
    ├── Decoder (30 → 55 → 75 → 42) → reconstruction loss
    └── CNN (Conv1d 1→32→16→5) → FC (150→300→400→1) → age prediction

The autoencoder regularizes the latent space while the CNN branch
predicts age from the compressed biomarker representation.
"""

import torch
import torch.nn as nn
import torch.nn.functional as F


class BloodAgeModel(nn.Module):

    def __init__(self, input_dim: int, output_dim: int = 1):
        super().__init__()
        self.hidden_dim = 30

        self.enc1 = nn.Linear(input_dim, 75)
        self.enc2 = nn.Linear(75, 55)
        self.enc3 = nn.Linear(55, self.hidden_dim)

        self.dec1 = nn.Linear(self.hidden_dim, 55)
        self.dec2 = nn.Linear(55, 75)
        self.dec3 = nn.Linear(75, input_dim)

        self.conv1 = nn.Conv1d(1, 32, kernel_size=4, padding="same")
        self.conv2 = nn.Conv1d(32, 16, kernel_size=4, padding="same")
        self.conv3 = nn.Conv1d(16, 5, kernel_size=4, padding="same")
        self.fc1 = nn.Linear(5 * self.hidden_dim, 300)
        self.fc2 = nn.Linear(300, 400)
        self.fc3 = nn.Linear(400, output_dim)

    def forward(self, x):
        h = F.relu(self.enc1(x))
        h = F.relu(self.enc2(h))
        z = F.relu(self.enc3(h))

        d = F.relu(self.dec1(z))
        d = F.relu(self.dec2(d))
        reconstruction = self.dec3(d)

        c = F.relu(self.conv1(z.unsqueeze(1)))
        c = F.relu(self.conv2(c))
        c = F.relu(self.conv3(c))
        c = torch.flatten(c, 1)
        c = F.relu(self.fc1(c))
        c = F.relu(self.fc2(c))
        age_pred = self.fc3(c)

        return z, reconstruction, age_pred

    def predict_age(self, x: torch.Tensor) -> torch.Tensor:
        _, _, age = self.forward(x)
        return age
