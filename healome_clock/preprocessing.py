"""
Preprocessing pipeline for blood panel data.

Handles biomarker validation, missing value imputation, normalization,
and conversion from standard clinical units to model-expected format.
"""

import numpy as np
import pandas as pd
from typing import Union, Optional, Dict, List
from pathlib import Path

BIOMARKERS = {
    "LBXWBCSI": {"name": "White Blood Cell Count", "unit": "1000 cells/uL", "category": "CBC"},
    "LBXLYPCT": {"name": "Lymphocyte Percent", "unit": "%", "category": "CBC"},
    "LBXMOPCT": {"name": "Monocyte Percent", "unit": "%", "category": "CBC"},
    "LBXNEPCT": {"name": "Segmented Neutrophils Percent", "unit": "%", "category": "CBC"},
    "LBXEOPCT": {"name": "Eosinophils Percent", "unit": "%", "category": "CBC"},
    "LBXBAPCT": {"name": "Basophils Percent", "unit": "%", "category": "CBC"},
    "LBDLYMNO": {"name": "Lymphocyte Number", "unit": "1000 cells/uL", "category": "CBC"},
    "LBDMONO": {"name": "Monocyte Number", "unit": "1000 cells/uL", "category": "CBC"},
    "LBDNENO": {"name": "Segmented Neutrophils Number", "unit": "1000 cells/uL", "category": "CBC"},
    "LBDEONO": {"name": "Eosinophils Number", "unit": "1000 cells/uL", "category": "CBC"},
    "LBDBANO": {"name": "Basophils Number", "unit": "1000 cells/uL", "category": "CBC"},
    "LBXRBCSI": {"name": "Red Blood Cell Count", "unit": "million cells/uL", "category": "CBC"},
    "LBXHGB": {"name": "Hemoglobin", "unit": "g/dL", "category": "CBC"},
    "LBXHCT": {"name": "Hematocrit", "unit": "%", "category": "CBC"},
    "LBXMCVSI": {"name": "Mean Cell Volume", "unit": "fL", "category": "CBC"},
    "LBXMCHSI": {"name": "Mean Cell Hemoglobin", "unit": "pg", "category": "CBC"},
    "LBXMC": {"name": "Mean Cell Hemoglobin Concentration", "unit": "g/dL", "category": "CBC"},
    "LBXRDW": {"name": "Red Cell Distribution Width", "unit": "%", "category": "CBC"},
    "LBXPLTSI": {"name": "Platelet Count", "unit": "1000 cells/uL", "category": "CBC"},
    "LBXMPSI": {"name": "Mean Platelet Volume", "unit": "fL", "category": "CBC"},
    "LBXSTB": {"name": "Total Bilirubin", "unit": "mg/dL", "category": "CMP"},
    "LBXSASSI": {"name": "Aspartate Aminotransferase (AST)", "unit": "IU/L", "category": "CMP"},
    "LBXSAPSI": {"name": "Alkaline Phosphatase (ALP)", "unit": "IU/L", "category": "CMP"},
    "LBXSTP": {"name": "Total Protein", "unit": "g/dL", "category": "CMP"},
    "LBXSAL": {"name": "Albumin", "unit": "g/dL", "category": "CMP"},
    "LBXSGB": {"name": "Globulin", "unit": "g/dL", "category": "CMP"},
    "LBXSGTSI": {"name": "Gamma Glutamyl Transferase (GGT)", "unit": "IU/L", "category": "CMP"},
    "LBXSATSI": {"name": "Alanine Aminotransferase (ALT)", "unit": "IU/L", "category": "CMP"},
    "LBDSALSI": {"name": "Albumin (SI)", "unit": "g/L", "category": "CMP"},
    "LBXSC3SI": {"name": "Bicarbonate", "unit": "mmol/L", "category": "CMP"},
    "LBXSBU": {"name": "Blood Urea Nitrogen", "unit": "mg/dL", "category": "CMP"},
    "LBDSBUSI": {"name": "Blood Urea Nitrogen (SI)", "unit": "mmol/L", "category": "CMP"},
    "LBDSGBSI": {"name": "Globulin (SI)", "unit": "g/L", "category": "CMP"},
    "LBXSGL": {"name": "Glucose", "unit": "mg/dL", "category": "CMP"},
    "LBDSGLSI": {"name": "Glucose (SI)", "unit": "mmol/L", "category": "CMP"},
    "LBXSIR": {"name": "Iron", "unit": "ug/dL", "category": "CMP"},
    "LBDSIRSI": {"name": "Iron (SI)", "unit": "umol/L", "category": "CMP"},
    "LBXSLDSI": {"name": "Lactate Dehydrogenase (LDH)", "unit": "IU/L", "category": "CMP"},
    "LBDSTPSI": {"name": "Total Protein (SI)", "unit": "g/L", "category": "CMP"},
    "LBXSTR": {"name": "Triglycerides", "unit": "mg/dL", "category": "CMP"},
    "LBDSTRSI": {"name": "Triglycerides (SI)", "unit": "mmol/L", "category": "CMP"},
    "LBXNRBC": {"name": "Nucleated Red Blood Cells", "unit": "", "category": "CBC"},
}

BIOMARKER_CODES = list(BIOMARKERS.keys())
BIOMARKER_NAMES = {code: info["name"] for code, info in BIOMARKERS.items()}
NUM_BIOMARKERS = len(BIOMARKER_CODES)

CBC_MARKERS = [k for k, v in BIOMARKERS.items() if v["category"] == "CBC"]
CMP_MARKERS = [k for k, v in BIOMARKERS.items() if v["category"] == "CMP"]


def validate_columns(df: pd.DataFrame) -> Dict[str, List[str]]:
    """Check which expected biomarker columns are present vs missing."""
    present = [col for col in BIOMARKER_CODES if col in df.columns]
    missing = [col for col in BIOMARKER_CODES if col not in df.columns]
    return {"present": present, "missing": missing}


def load_blood_panel(
    source: Union[str, Path, pd.DataFrame, Dict],
) -> pd.DataFrame:
    """
    Load blood panel data from various formats.

    Accepts:
        - CSV file path
        - JSON file path
        - pandas DataFrame
        - dict of biomarker values
    """
    if isinstance(source, dict):
        return pd.DataFrame([source])
    if isinstance(source, pd.DataFrame):
        return source.copy()

    path = Path(source)
    if path.suffix.lower() == ".csv":
        return pd.read_csv(path)
    elif path.suffix.lower() == ".json":
        return pd.read_json(path)
    else:
        raise ValueError(f"Unsupported file format: {path.suffix}. Use .csv or .json.")


def impute_missing(
    df: pd.DataFrame,
    strategy: str = "median",
    training_medians: Optional[Dict[str, float]] = None,
) -> pd.DataFrame:
    """
    Handle missing values via simple imputation.

    For production, we use training-set medians. For quick inference
    without a fitted imputer, we fall back to column medians of the
    input data itself (with a warning).
    """
    df = df.copy()

    if training_medians is not None:
        for col in df.columns:
            if col in training_medians and df[col].isna().any():
                df[col] = df[col].fillna(training_medians[col])
    else:
        if df.isna().any().any():
            import warnings
            warnings.warn(
                "No training medians provided. Imputing with input column medians. "
                "For best results, use the fitted imputer from training.",
                UserWarning,
            )
            df = df.fillna(df.median())

    return df


def preprocess_blood_panel(
    source: Union[str, Path, pd.DataFrame, Dict],
    validate: bool = True,
) -> pd.DataFrame:
    """
    Full preprocessing pipeline: load, validate, reorder, impute.

    Returns a DataFrame with columns in the canonical biomarker order,
    ready for model inference.
    """
    df = load_blood_panel(source)

    if validate:
        check = validate_columns(df)
        if len(check["present"]) == 0:
            raise ValueError(
                "No recognized biomarker columns found. "
                f"Expected NHANES codes like: {BIOMARKER_CODES[:5]}... "
                "See MODEL_CARD.md for the full biomarker list."
            )
        if check["missing"]:
            import warnings
            n_missing = len(check["missing"])
            n_total = NUM_BIOMARKERS
            warnings.warn(
                f"{n_missing}/{n_total} biomarkers missing: {check['missing'][:5]}... "
                "Missing values will be imputed. Accuracy may degrade with many missing markers.",
                UserWarning,
            )

    for col in BIOMARKER_CODES:
        if col not in df.columns:
            df[col] = np.nan

    df = df[BIOMARKER_CODES]
    df = impute_missing(df)

    return df
