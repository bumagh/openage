"""
Data loading utilities for NHANES and linked mortality data.

Provides clean interfaces for downloading and loading NHANES survey data
and CDC linked mortality files. Designed to be extensible — new data
sources can be registered via the registry module.
"""

from healome_clock.data.nhanes import load_nhanes_cycle, load_nhanes_all, NHANES_XPT_FILES
from healome_clock.data.mortality import load_mortality_data, download_mortality_file

__all__ = [
    "load_nhanes_cycle",
    "load_nhanes_all",
    "NHANES_XPT_FILES",
    "load_mortality_data",
    "download_mortality_file",
]
