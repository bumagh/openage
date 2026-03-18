"""
Experimental models for the Healome Aging Clock.

These models are research prototypes and are not the primary
production models. Use healome_clock.models.TreeModel for
validated predictions.
"""

from healome_clock.models.experimental.autoencoder_cnn import BloodAgeModel

__all__ = ["BloodAgeModel"]
