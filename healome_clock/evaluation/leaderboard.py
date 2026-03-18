"""
Leaderboard submission format and scoring.

Standardized format for community model benchmarking.
Two tracks: age prediction accuracy and mortality prediction.
"""

import json
import numpy as np
import pandas as pd
from typing import Dict, Optional, Union
from pathlib import Path
from datetime import datetime

from healome_clock.evaluation.metrics import compute_age_metrics, compute_age_bucket_metrics


SUBMISSION_SCHEMA = {
    "model_name": str,
    "authors": str,
    "description": str,
    "date": str,
    "model_type": str,
    "n_features": int,
    "training_data": str,
    "track1_age_prediction": {
        "mae": float,
        "rmse": float,
        "r2": float,
        "pearson_r": float,
        "n_test_samples": int,
        "test_split_method": str,
    },
    "track2_survival": {
        "concordance": float,
        "n_mortality_records": int,
        "km_separation": str,
    },
}


def create_submission(
    model_name: str,
    y_true: np.ndarray,
    y_pred: np.ndarray,
    authors: str = "",
    description: str = "",
    model_type: str = "",
    n_features: int = 0,
    training_data: str = "NHANES",
    test_split_method: str = "random 70/30",
    concordance: Optional[float] = None,
    n_mortality_records: Optional[int] = None,
    km_separation: Optional[str] = None,
) -> Dict:
    """
    Create a standardized leaderboard submission.

    Args:
        model_name: Name of the model.
        y_true: True chronological ages on test set.
        y_pred: Predicted biological ages on test set.
        authors: Author(s) of the submission.
        description: Brief model description.
        concordance: Cox PH concordance index (track 2).

    Returns:
        Submission dict that can be saved as JSON.
    """
    metrics = compute_age_metrics(y_true, y_pred)

    submission = {
        "model_name": model_name,
        "authors": authors,
        "description": description,
        "date": datetime.now().strftime("%Y-%m-%d"),
        "model_type": model_type,
        "n_features": n_features,
        "training_data": training_data,
        "track1_age_prediction": {
            "mae": round(metrics["mae"], 4),
            "rmse": round(metrics["rmse"], 4),
            "r2": round(metrics["r2"], 4),
            "pearson_r": round(metrics["pearson_r"], 4),
            "n_test_samples": int(metrics["n_samples"]),
            "test_split_method": test_split_method,
        },
    }

    if concordance is not None:
        submission["track2_survival"] = {
            "concordance": round(concordance, 4),
            "n_mortality_records": n_mortality_records or 0,
            "km_separation": km_separation or "",
        }

    return submission


def save_submission(submission: Dict, filepath: Union[str, Path]):
    """Save a submission as JSON."""
    filepath = Path(filepath)
    filepath.parent.mkdir(parents=True, exist_ok=True)
    with open(filepath, "w") as f:
        json.dump(submission, f, indent=2)
    print(f"Submission saved to {filepath}")


def load_submission(filepath: Union[str, Path]) -> Dict:
    """Load a submission from JSON."""
    with open(filepath) as f:
        return json.load(f)


def compare_submissions(submission_dir: Union[str, Path]) -> pd.DataFrame:
    """
    Load all submissions from a directory and return a comparison table.

    Args:
        submission_dir: Directory containing .json submission files.

    Returns:
        DataFrame sorted by Track 1 MAE (ascending = better).
    """
    submission_dir = Path(submission_dir)
    rows = []

    for fp in sorted(submission_dir.glob("*.json")):
        sub = load_submission(fp)
        row = {
            "model": sub.get("model_name", fp.stem),
            "type": sub.get("model_type", ""),
            "features": sub.get("n_features", 0),
            "data": sub.get("training_data", ""),
        }
        if "track1_age_prediction" in sub:
            t1 = sub["track1_age_prediction"]
            row.update({
                "MAE": t1.get("mae"),
                "RMSE": t1.get("rmse"),
                "R²": t1.get("r2"),
                "Pearson": t1.get("pearson_r"),
                "N_test": t1.get("n_test_samples"),
            })
        if "track2_survival" in sub:
            t2 = sub["track2_survival"]
            row["Concordance"] = t2.get("concordance")
        rows.append(row)

    df = pd.DataFrame(rows)
    if "MAE" in df.columns:
        df = df.sort_values("MAE")
    return df.reset_index(drop=True)
