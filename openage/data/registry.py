"""
Extensible data source registry.

Allows community contributors to register new data sources beyond NHANES.
Each data source provides a loader function that returns a standardized DataFrame.
"""

from typing import Callable, Dict, Optional, List
import pandas as pd


_REGISTRY: Dict[str, dict] = {}


def register_data_source(
    name: str,
    loader: Callable,
    description: str = "",
    url: str = "",
    features_available: Optional[List[str]] = None,
    has_mortality: bool = False,
):
    """
    Register a new data source.

    Args:
        name: Unique identifier for this data source.
        loader: Callable that returns a pd.DataFrame with biomarker columns.
        description: Human-readable description.
        url: URL to the data source documentation.
        features_available: List of NHANES-compatible feature codes this source provides.
        has_mortality: Whether this source includes mortality outcomes.

    Example:
        >>> def load_uk_biobank(path):
        ...     df = pd.read_csv(path)
        ...     # ... map columns to NHANES codes ...
        ...     return df
        >>> register_data_source(
        ...     "uk_biobank", load_uk_biobank,
        ...     description="UK Biobank blood biomarkers",
        ...     has_mortality=True,
        ... )
    """
    _REGISTRY[name] = {
        "loader": loader,
        "description": description,
        "url": url,
        "features_available": features_available or [],
        "has_mortality": has_mortality,
    }


def get_data_source(name: str) -> dict:
    """Get a registered data source by name."""
    if name not in _REGISTRY:
        available = list(_REGISTRY.keys())
        raise KeyError(
            f"Data source '{name}' not registered. Available: {available}"
        )
    return _REGISTRY[name]


def list_data_sources() -> pd.DataFrame:
    """List all registered data sources."""
    if not _REGISTRY:
        return pd.DataFrame(columns=["name", "description", "n_features", "has_mortality"])

    rows = []
    for name, info in _REGISTRY.items():
        rows.append({
            "name": name,
            "description": info["description"],
            "n_features": len(info["features_available"]),
            "has_mortality": info["has_mortality"],
            "url": info["url"],
        })
    return pd.DataFrame(rows)


def load_from_registry(name: str, *args, **kwargs) -> pd.DataFrame:
    """Load data from a registered source."""
    source = get_data_source(name)
    return source["loader"](*args, **kwargs)
