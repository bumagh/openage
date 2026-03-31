"""
PhenoAge (Levine 2018) implementation for benchmarking.

Reference: Levine et al. "An epigenetic biomarker of aging for lifespan
and healthspan." Aging (2018). DOI: 10.18632/aging.101414

This is a blood-based phenotypic age formula using 9 biomarkers + chronological age.
Implemented here for head-to-head comparison with OpenAge.
"""

import numpy as np
import pandas as pd
from typing import Optional

PHENOAGE_COEFFICIENTS = {
    "age": 0.0804,
    "albumin": -0.034,
    "creatinine": 0.0095,
    "glucose": 0.1953,
    "c_reactive_protein": 0.0954,
    "lymphocyte_percent": -0.012,
    "mean_cell_volume": 0.0268,
    "red_blood_cell_distribution_width": 0.3356,
    "alkaline_phosphatase": 0.00188,
    "white_blood_cell_count": 0.0554,
}

PHENOAGE_CONSTANT = -19.9067
PHENOAGE_GAMMA = 0.0077
PHENOAGE_TRANSFORM = [141.50225, -0.00553, 0.090165]

NHANES_TO_PHENOAGE = {
    "RIDAGEYR": "age",
    "LBDSALSI": "albumin",
    "LBDSCRSI": "creatinine",
    "LBXSGL": "glucose",
    "LBXHSCRP": "c_reactive_protein",
    "LBXLYPCT": "lymphocyte_percent",
    "LBXMCVSI": "mean_cell_volume",
    "LBXRDW": "red_blood_cell_distribution_width",
    "LBXSAPSI": "alkaline_phosphatase",
    "LBXWBCSI": "white_blood_cell_count",
}


def compute_phenoage(df: pd.DataFrame, nhanes_format: bool = True) -> pd.Series:
    """
    Compute PhenoAge (Levine 2018) from biomarker data.

    Args:
        df: DataFrame with either NHANES column codes or PhenoAge variable names.
        nhanes_format: If True, remap NHANES codes to PhenoAge variable names.

    Returns:
        Series of phenotypic age estimates.
    """
    data = df.copy()

    if nhanes_format:
        rename_map = {k: v for k, v in NHANES_TO_PHENOAGE.items() if k in data.columns}
        data = data.rename(columns=rename_map)

    required = list(PHENOAGE_COEFFICIENTS.keys())
    missing = [c for c in required if c not in data.columns]
    if missing:
        raise ValueError(
            f"Missing columns for PhenoAge: {missing}. "
            f"Required: {required}"
        )

    data = data.copy()
    data["c_reactive_protein"] = np.log(data["c_reactive_protein"].clip(lower=0.01))
    data["glucose"] = 0.05551 * data["glucose"]

    pheno_score = sum(
        data[col] * coef for col, coef in PHENOAGE_COEFFICIENTS.items()
    )

    mortality_score = 1 - np.exp(
        -np.exp(PHENOAGE_CONSTANT + pheno_score)
        * ((np.exp(120 * PHENOAGE_GAMMA) - 1) / PHENOAGE_GAMMA)
    )

    cs = PHENOAGE_TRANSFORM
    phenotypic_age = cs[0] + np.log(cs[1] * np.log(1.00001 - mortality_score)) / cs[2]

    return phenotypic_age
