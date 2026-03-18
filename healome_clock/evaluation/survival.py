"""
Survival analysis evaluation for biological age models.

Track 2 of the Healome benchmarking framework. Uses lifelines for
Kaplan-Meier survival curves and Cox Proportional Hazards models.

Requires: pip install lifelines
"""

import numpy as np
import pandas as pd
from typing import Optional, Dict, Tuple
import warnings


def classify_aging_rate(
    bio_ages: np.ndarray,
    chrono_ages: np.ndarray,
    threshold: float = 5.0,
) -> np.ndarray:
    """
    Classify individuals by aging rate.

    Args:
        bio_ages: Predicted biological ages.
        chrono_ages: Chronological ages.
        threshold: Years of delta to classify as accelerated/decelerated.

    Returns:
        Array of labels: "accelerated", "decelerated", or "normal".
    """
    delta = np.asarray(bio_ages) - np.asarray(chrono_ages)
    labels = np.full(len(delta), "normal", dtype=object)
    labels[delta >= threshold] = "accelerated"
    labels[delta <= -threshold] = "decelerated"
    return labels


def prepare_survival_data(
    df: pd.DataFrame,
    bio_age_col: str = "bio_age",
    chrono_age_col: str = "RIDAGEYR",
    dead_col: str = "is_dead",
    months_col: str = "months_until_death",
    threshold: float = 5.0,
) -> pd.DataFrame:
    """
    Prepare DataFrame for survival analysis.

    Adds computed columns: aging_rate, years_until_death,
    chronological_age_at_event, biological_age_at_event.
    """
    out = df.copy()
    out["aging_rate"] = classify_aging_rate(
        out[bio_age_col].values, out[chrono_age_col].values, threshold
    )
    out["years_until_death"] = out[months_col] / 12.0
    out["chrono_age_at_event"] = out["years_until_death"] + out[chrono_age_col]
    out["bio_age_at_event"] = out["years_until_death"] + out[bio_age_col]
    return out


def compute_kaplan_meier(
    df: pd.DataFrame,
    duration_col: str = "chrono_age_at_event",
    event_col: str = "is_dead",
    group_col: str = "aging_rate",
    groups: Optional[list] = None,
    ax=None,
) -> Dict:
    """
    Compute and optionally plot Kaplan-Meier survival curves.

    Args:
        df: DataFrame with duration, event, and group columns.
        duration_col: Time-to-event column.
        event_col: Event indicator column (1=event, 0=censored).
        group_col: Column to group by.
        groups: Specific groups to plot. Default: ["accelerated", "decelerated"].
        ax: Matplotlib axis for plotting. If None, creates a new figure.

    Returns:
        Dict mapping group names to fitted KaplanMeierFitter objects.
    """
    try:
        from lifelines import KaplanMeierFitter
    except ImportError:
        raise ImportError(
            "lifelines is required for survival analysis. Install with: pip install lifelines"
        )

    if groups is None:
        groups = ["accelerated", "decelerated"]

    if ax is None:
        import matplotlib.pyplot as plt
        fig, ax = plt.subplots(figsize=(10, 7))

    kmf_results = {}
    for group in groups:
        mask = df[group_col] == group
        if mask.sum() == 0:
            warnings.warn(f"No samples in group '{group}', skipping")
            continue

        group_df = df[mask]
        kmf = KaplanMeierFitter()
        kmf.fit(
            durations=group_df[duration_col],
            event_observed=group_df[event_col],
            label=f"{group} aging (n={mask.sum():,})",
        )
        kmf.plot_survival_function(ax=ax)
        kmf_results[group] = kmf

    ax.set_title("Survival by Biological Aging Rate", fontsize=14, fontweight="bold")
    ax.set_xlabel("Age (years)", fontsize=12)
    ax.set_ylabel("Survival Probability", fontsize=12)
    ax.grid(True, alpha=0.3)
    ax.legend(fontsize=11)

    return kmf_results


def compute_cox_hazard_ratios(
    df: pd.DataFrame,
    duration_col: str = "years_until_death",
    event_col: str = "is_dead",
    covariates: Optional[list] = None,
    penalizer: float = 1e-9,
) -> Dict:
    """
    Fit a Cox Proportional Hazards model and return hazard ratios.

    Args:
        df: DataFrame with duration, event, and covariate columns.
        duration_col: Time-to-event column.
        event_col: Event indicator column.
        covariates: Columns to include as covariates.
            Default: ["RIDAGEYR", "bio_age"].
        penalizer: Regularization penalty for CoxPHFitter.

    Returns:
        Dict with:
            - "model": Fitted CoxPHFitter object
            - "concordance": Concordance index
            - "hazard_ratios": DataFrame of hazard ratios
            - "summary": Full model summary DataFrame
    """
    try:
        from lifelines import CoxPHFitter
    except ImportError:
        raise ImportError(
            "lifelines is required for survival analysis. Install with: pip install lifelines"
        )

    if covariates is None:
        covariates = ["RIDAGEYR", "bio_age"]

    cols_needed = covariates + [duration_col, event_col]
    cph_data = df[cols_needed].dropna()

    cph = CoxPHFitter(penalizer=penalizer)
    cph.fit(cph_data, duration_col=duration_col, event_col=event_col)

    return {
        "model": cph,
        "concordance": cph.concordance_index_,
        "hazard_ratios": np.exp(cph.params_),
        "summary": cph.summary,
    }
