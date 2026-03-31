"""
Model implementations for OpenAge.

Primary models are tree-based (GradientBoosting). The neural network
autoencoder+CNN is available under models.experimental.
"""

from openage.models.tree import TreeModel, STANDARD_21_FEATURES, EXTENDED_35_FEATURES

__all__ = ["TreeModel", "STANDARD_21_FEATURES", "EXTENDED_35_FEATURES"]
