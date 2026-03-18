"""
Age prediction evaluation metrics.

Track 1 of the Healome benchmarking framework.
"""

import numpy as np
import pandas as pd
from typing import Optional, Dict, List
from sklearn.metrics import mean_squared_error, r2_score


def compute_age_metrics(
    y_true: np.ndarray,
    y_pred: np.ndarray,
) -> Dict[str, float]:
    """
    Compute standard age prediction metrics.

    Returns:
        Dict with MAE, RMSE, R², MSE, and Pearson correlation.
    """
    y_true = np.asarray(y_true).flatten()
    y_pred = np.asarray(y_pred).flatten()

    mae = float(np.mean(np.abs(y_true - y_pred)))
    mse = float(mean_squared_error(y_true, y_pred))
    rmse = float(np.sqrt(mse))
    r2 = float(r2_score(y_true, y_pred))
    pearson = float(np.corrcoef(y_true, y_pred)[0, 1])

    return {
        "mae": mae,
        "rmse": rmse,
        "mse": mse,
        "r2": r2,
        "pearson_r": pearson,
        "n_samples": len(y_true),
    }


def compute_subgroup_metrics(
    y_true: np.ndarray,
    y_pred: np.ndarray,
    groups: np.ndarray,
    group_name: str = "subgroup",
) -> pd.DataFrame:
    """
    Compute metrics for each subgroup.

    Args:
        y_true: True chronological ages.
        y_pred: Predicted biological ages.
        groups: Array of group labels (same length as y_true).
        group_name: Name for the group column.

    Returns:
        DataFrame with one row per subgroup and columns for each metric.
    """
    y_true = np.asarray(y_true).flatten()
    y_pred = np.asarray(y_pred).flatten()
    groups = np.asarray(groups).flatten()

    rows = []
    for g in sorted(set(groups)):
        mask = groups == g
        if mask.sum() < 2:
            continue
        metrics = compute_age_metrics(y_true[mask], y_pred[mask])
        metrics[group_name] = g
        rows.append(metrics)

    df = pd.DataFrame(rows)
    cols = [group_name] + [c for c in df.columns if c != group_name]
    return df[cols]


def compute_age_bucket_metrics(
    y_true: np.ndarray,
    y_pred: np.ndarray,
    buckets: Optional[List[tuple]] = None,
) -> pd.DataFrame:
    """
    Compute metrics by age range buckets.

    Args:
        y_true: True chronological ages.
        y_pred: Predicted biological ages.
        buckets: List of (low, high) tuples. Default: [(20,39), (40,59), (60,100)].
    """
    if buckets is None:
        buckets = [(20, 39), (40, 59), (60, 100)]

    y_true = np.asarray(y_true).flatten()
    y_pred = np.asarray(y_pred).flatten()

    labels = np.empty(len(y_true), dtype=object)
    for low, high in buckets:
        mask = (y_true >= low) & (y_true <= high)
        labels[mask] = f"Age {low}-{high}"

    labels[labels == None] = "Other"  # noqa: E711
    return compute_subgroup_metrics(y_true, y_pred, labels, group_name="age_bucket")


def print_metrics(metrics: Dict[str, float], title: str = "Model Performance"):
    """Pretty-print metrics dict."""
    print(f"\n{'=' * 50}")
    print(f"  {title}")
    print(f"{'=' * 50}")
    print(f"  MAE:       {metrics['mae']:.2f} years")
    print(f"  RMSE:      {metrics['rmse']:.2f} years")
    print(f"  R²:        {metrics['r2']:.4f}")
    print(f"  Pearson r: {metrics['pearson_r']:.4f}")
    print(f"  N:         {metrics['n_samples']:,}")
    print(f"{'=' * 50}\n")
