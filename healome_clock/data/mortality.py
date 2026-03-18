"""
NHANES linked mortality data loader.

Downloads and parses CDC linked mortality files that provide
follow-up vital status for NHANES participants. Used for
survival analysis (Kaplan-Meier, Cox Proportional Hazards).

Data source: https://ftp.cdc.gov/pub/Health_Statistics/NCHS/datalinkage/linked_mortality/
"""

import pandas as pd
import numpy as np
from pathlib import Path
from typing import Optional, List, Union
import warnings

MORTALITY_BASE_URL = (
    "https://ftp.cdc.gov/pub/Health_Statistics/NCHS/datalinkage/linked_mortality"
)

MORTALITY_YEARS = [2000, 2002, 2004, 2006, 2008, 2010, 2012, 2014, 2016, 2018]

MORTALITY_WIDTHS = [14, 1, 1, 3, 1, 1, 1, 4, 8, 8, 3, 3]


def download_mortality_file(
    year: int,
    save_dir: Optional[Union[str, Path]] = None,
    cache: bool = True,
) -> Path:
    """
    Download an NHANES linked mortality .dat file from the CDC FTP server.

    Args:
        year: The ending year of the NHANES cycle (e.g., 2000 for 1999-2000).
        save_dir: Directory to save the file. Defaults to a temp directory.
        cache: If True, skip download if file already exists.

    Returns:
        Path to the downloaded file.
    """
    filename = f"NHANES_{year - 1}_{year}_MORT_2019_PUBLIC.dat"
    url = f"{MORTALITY_BASE_URL}/{filename}"

    if save_dir is None:
        import tempfile
        save_dir = Path(tempfile.gettempdir()) / "nhanes_mortality"

    save_dir = Path(save_dir)
    save_dir.mkdir(parents=True, exist_ok=True)
    filepath = save_dir / filename

    if cache and filepath.exists():
        return filepath

    try:
        import urllib.request
        print(f"  Downloading {filename}...")
        urllib.request.urlretrieve(url, filepath)
    except Exception as e:
        raise RuntimeError(
            f"Failed to download mortality data for {year} from {url}: {e}\n"
            "You may need to download manually from the CDC FTP server."
        )

    return filepath


def parse_mortality_file(filepath: Union[str, Path]) -> pd.DataFrame:
    """
    Parse an NHANES linked mortality .dat file (fixed-width format).

    Returns DataFrame with columns:
        - SEQN: Respondent sequence number (index)
        - is_dead: 1 if deceased, 0 otherwise
        - months_until_death: Months from exam to death (or end of follow-up)
    """
    filepath = Path(filepath)
    mort = pd.read_fwf(
        filepath,
        index_col=0,
        header=None,
        widths=MORTALITY_WIDTHS,
    )
    mort.index = mort.index.rename("SEQN")

    # Column 1 = ELIGSTAT (1=eligible), Column 2 = MORTSTAT (0=alive, 1=dead)
    # Column 10 = PERMTH_EXM (person-months from exam to death/censoring)
    dead = mort[mort[1] == 1][[2, 10]].copy()
    dead.columns = ["is_dead", "months_until_death"]
    dead = dead.astype(int)

    return dead


def load_mortality_data(
    years: Optional[List[int]] = None,
    data_dir: Optional[Union[str, Path]] = None,
    download: bool = True,
) -> pd.DataFrame:
    """
    Load mortality data for multiple NHANES cycles.

    Args:
        years: List of cycle end-years. Defaults to all available (2000-2018).
        data_dir: Directory containing .dat files (or where to save downloads).
        download: If True, download missing files from the CDC FTP server.

    Returns:
        DataFrame indexed by SEQN with is_dead and months_until_death columns.
    """
    if years is None:
        years = MORTALITY_YEARS

    all_mort = []

    for year in years:
        try:
            filename = f"NHANES_{year - 1}_{year}_MORT_2019_PUBLIC.dat"

            if data_dir:
                filepath = Path(data_dir) / filename
                if filepath.exists():
                    df = parse_mortality_file(filepath)
                    all_mort.append(df)
                    continue

            if download:
                filepath = download_mortality_file(year, save_dir=data_dir)
                df = parse_mortality_file(filepath)
                all_mort.append(df)
            else:
                warnings.warn(f"Mortality file for {year} not found and download=False")

        except Exception as e:
            warnings.warn(f"Failed to load mortality data for {year}: {e}")

    if not all_mort:
        raise ValueError("No mortality data could be loaded")

    combined = pd.concat(all_mort, axis=0)
    combined = combined[~combined.index.duplicated(keep="first")]

    print(f"Loaded mortality data: {len(combined)} records, "
          f"{combined['is_dead'].sum()} deceased")
    return combined


def merge_with_mortality(
    nhanes_df: pd.DataFrame,
    mortality_df: pd.DataFrame,
    seqn_col: str = "SEQN",
) -> pd.DataFrame:
    """
    Merge NHANES biomarker data with mortality outcomes.

    Args:
        nhanes_df: NHANES data with SEQN column.
        mortality_df: Mortality data indexed by SEQN.
        seqn_col: Name of the SEQN column in nhanes_df.

    Returns:
        Merged DataFrame with is_dead and months_until_death columns added.
    """
    merged = nhanes_df.merge(
        mortality_df,
        left_on=seqn_col,
        right_index=True,
        how="inner",
    )
    print(f"Merged: {len(merged)} records with mortality data "
          f"({merged['is_dead'].sum()} deceased)")
    return merged
