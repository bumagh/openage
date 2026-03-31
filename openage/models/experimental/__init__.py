"""
Experimental models for OpenAge.

These models are research prototypes and are not the primary
production models. Use openage.models.TreeModel for
validated predictions.
"""

from openage.models.experimental.autoencoder_cnn import BloodAgeModel

__all__ = ["BloodAgeModel"]
