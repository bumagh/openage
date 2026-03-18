"""
NHANES data loading utilities.

Downloads and merges XPT (SAS Transport) files from the CDC NHANES website.
Supports all survey cycles from 1999-2000 through 2017-2020.
"""

import os
import pandas as pd
import numpy as np
from pathlib import Path
from typing import List, Optional, Dict, Union
import warnings


NHANES_BASE_URL = "https://wwwn.cdc.gov/Nchs/Nhanes"

# XPT files needed for the aging clock, keyed by category.
# Pre-pandemic (2017-2020) uses "P_" prefix; earlier cycles use different names.
NHANES_XPT_FILES = {
    "2017-2020": {
        "biochemistry": "P_BIOPRO.XPT",
        "cbc": "P_CBC.XPT",
        "mcq": "P_MCQ.XPT",
        "triglycerides": "P_TRIGLY.XPT",
        "hscrp": "P_HSCRP.XPT",
        "hdl": "P_HDL.XPT",
        "glycohemoglobin": "P_GHB.XPT",
        "demographics": "P_DEMO.XPT",
    },
}

# Earlier cycles use different file naming conventions
NHANES_CYCLE_FILES = {
    "biochemistry": {"prefix": "BIOPRO", "suffix": ".XPT"},
    "cbc": {"prefix": "CBC", "suffix": ".XPT"},
    "mcq": {"prefix": "MCQ", "suffix": ".XPT"},
    "triglycerides": {"prefix": "TRIGLY", "suffix": ".XPT"},
    "hscrp": {"prefix": "HSCRP", "suffix": ".XPT"},
    "hdl": {"prefix": "HDL", "suffix": ".XPT"},
    "glycohemoglobin": {"prefix": "GHB", "suffix": ".XPT"},
    "demographics": {"prefix": "DEMO", "suffix": ".XPT"},
}

AVAILABLE_CYCLES = [
    "1999-2000", "2001-2002", "2003-2004", "2005-2006",
    "2007-2008", "2009-2010", "2011-2012", "2013-2014",
    "2015-2016", "2017-2018", "2017-2020",
]


def load_xpt(filepath: Union[str, Path], format: str = "xport") -> pd.DataFrame:
    """Load a single SAS XPT file."""
    return pd.read_sas(str(filepath), format=format)


def load_nhanes_cycle(
    data_dir: Union[str, Path],
    merge_on: str = "SEQN",
) -> pd.DataFrame:
    """
    Load and merge all XPT files from a single NHANES cycle directory.

    Expects the directory to contain XPT files (BIOPRO, CBC, MCQ, etc.).
    All files are outer-joined on SEQN (respondent sequence number).

    Args:
        data_dir: Path to directory containing XPT files for one cycle.
        merge_on: Column to merge on (default: SEQN).

    Returns:
        Merged DataFrame with all biomarker and questionnaire data.
    """
    data_dir = Path(data_dir)
    if not data_dir.exists():
        raise FileNotFoundError(f"NHANES data directory not found: {data_dir}")

    xpt_files = sorted(data_dir.glob("*.XPT")) + sorted(data_dir.glob("*.xpt"))
    if not xpt_files:
        raise FileNotFoundError(f"No XPT files found in {data_dir}")

    merged = None
    for xpt_path in xpt_files:
        try:
            df = load_xpt(xpt_path)
            if merge_on not in df.columns:
                continue
            if merged is None:
                merged = df
            else:
                overlap_cols = set(merged.columns) & set(df.columns) - {merge_on}
                if overlap_cols:
                    df = df.drop(columns=list(overlap_cols), errors="ignore")
                merged = merged.merge(df, on=merge_on, how="outer")
        except Exception as e:
            warnings.warn(f"Failed to load {xpt_path.name}: {e}")

    if merged is None:
        raise ValueError(f"No valid XPT files could be loaded from {data_dir}")

    return merged


def load_nhanes_specific(
    data_dir: Union[str, Path],
    files: List[str],
    merge_on: str = "SEQN",
) -> pd.DataFrame:
    """
    Load and merge specific XPT files from a directory.

    This mirrors the exact loading pattern from the training notebook:
    BIOPRO + MCQ + TRIGLY + HSCRP + HDL + CBC + GHB + DEMO.

    Args:
        data_dir: Path to directory containing XPT files.
        files: List of XPT filenames to load and merge.
        merge_on: Column to merge on.

    Returns:
        Merged DataFrame.
    """
    data_dir = Path(data_dir)
    merged = None

    for filename in files:
        filepath = data_dir / filename
        if not filepath.exists():
            warnings.warn(f"File not found, skipping: {filepath}")
            continue

        df = load_xpt(filepath)
        if merge_on not in df.columns:
            warnings.warn(f"{merge_on} not in {filename}, skipping")
            continue

        if merged is None:
            merged = df
        else:
            merged = merged.merge(df, on=merge_on, how="outer")

    return merged


def load_nhanes_all(
    cycle_dirs: Dict[str, Union[str, Path]],
    merge_on: str = "SEQN",
) -> pd.DataFrame:
    """
    Load and concatenate NHANES data from multiple survey cycles.

    Args:
        cycle_dirs: Dict mapping cycle names to directory paths.
            Example: {"2017-2020": "/data/NHANES/2017-2020", "2015-2016": "/data/NHANES/2015-16"}
        merge_on: Column to merge on within each cycle.

    Returns:
        Concatenated DataFrame across all cycles.
    """
    all_data = []

    for cycle_name, cycle_dir in cycle_dirs.items():
        try:
            df = load_nhanes_cycle(cycle_dir, merge_on=merge_on)
            df["_nhanes_cycle"] = cycle_name
            all_data.append(df)
            print(f"  Loaded {cycle_name}: {len(df)} records, {len(df.columns)} columns")
        except Exception as e:
            warnings.warn(f"Failed to load cycle {cycle_name}: {e}")

    if not all_data:
        raise ValueError("No NHANES cycles could be loaded")

    combined = pd.concat(all_data, ignore_index=True)
    print(f"Total: {len(combined)} records across {len(all_data)} cycles")
    return combined


def prepare_training_data(
    df: pd.DataFrame,
    features: List[str],
    age_col: str = "RIDAGEYR",
    fillna_strategy: str = "mean",
) -> tuple:
    """
    Prepare NHANES data for model training.

    Extracts feature columns and age target, applies imputation,
    and returns (X, y) arrays ready for sklearn.

    Args:
        df: Raw NHANES DataFrame.
        features: List of feature column names in the desired order.
        age_col: Column name for chronological age.
        fillna_strategy: "mean" to fill NaN with column means.

    Returns:
        Tuple of (X, y) numpy arrays.
    """
    subset = df[features + [age_col]].copy()

    if fillna_strategy == "mean":
        subset = subset.fillna(subset.mean())
    else:
        raise ValueError(f"Unknown fillna_strategy: {fillna_strategy}")

    subset = subset.dropna()

    X = subset[features].values
    y = subset[age_col].values

    return X, y
