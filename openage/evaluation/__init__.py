"""
Evaluation framework for biological age models.

Two tracks:
  1. Age prediction: MAE, RMSE, R², Pearson correlation, subgroup analysis
  2. Survival analysis: Kaplan-Meier curves, Cox Proportional Hazards, concordance
"""

from openage.evaluation.metrics import compute_age_metrics, compute_subgroup_metrics
from openage.evaluation.survival import (
    compute_kaplan_meier,
    compute_cox_hazard_ratios,
    classify_aging_rate,
)

__all__ = [
    "compute_age_metrics",
    "compute_subgroup_metrics",
    "compute_kaplan_meier",
    "compute_cox_hazard_ratios",
    "classify_aging_rate",
]
