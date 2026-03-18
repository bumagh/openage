"""
Visualization utilities for the Healome Aging Clock.

Generates plots for model outputs, calibration, and subgroup analysis.
"""

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
from typing import Optional, List, Tuple
from pathlib import Path


def plot_predicted_vs_actual(
    y_true: np.ndarray,
    y_pred: np.ndarray,
    title: str = "Predicted vs. Actual Age",
    save_path: Optional[str] = None,
    figsize: Tuple[int, int] = (8, 8),
) -> plt.Figure:
    """
    Scatter plot of predicted biological age vs chronological age.

    The ideal model lies on the diagonal. Systematic deviations indicate
    calibration issues at specific age ranges.
    """
    fig, ax = plt.subplots(figsize=figsize)

    ax.scatter(y_true, y_pred, alpha=0.15, s=8, c="#2563EB", edgecolors="none")

    lims = [
        min(y_true.min(), y_pred.min()) - 2,
        max(y_true.max(), y_pred.max()) + 2,
    ]
    ax.plot(lims, lims, "--", color="#94A3B8", linewidth=1.5, label="y = x")

    z = np.polyfit(y_true, y_pred, 1)
    p = np.poly1d(z)
    x_line = np.linspace(lims[0], lims[1], 100)
    ax.plot(x_line, p(x_line), "-", color="#DC2626", linewidth=1.5,
            label=f"Fit: y = {z[0]:.2f}x + {z[1]:.1f}")

    mae = np.mean(np.abs(y_true - y_pred))
    r2 = 1 - np.sum((y_true - y_pred) ** 2) / np.sum((y_true - y_true.mean()) ** 2)
    ax.text(
        0.05, 0.92,
        f"MAE = {mae:.2f} years\nR² = {r2:.3f}\nn = {len(y_true):,}",
        transform=ax.transAxes,
        fontsize=11,
        verticalalignment="top",
        bbox=dict(boxstyle="round,pad=0.4", facecolor="white", edgecolor="#E2E8F0", alpha=0.9),
    )

    ax.set_xlabel("Chronological Age (years)", fontsize=12)
    ax.set_ylabel("Predicted Biological Age (years)", fontsize=12)
    ax.set_title(title, fontsize=14, fontweight="bold")
    ax.legend(loc="lower right", fontsize=10)
    ax.set_xlim(lims)
    ax.set_ylim(lims)
    ax.set_aspect("equal")
    ax.grid(True, alpha=0.3)

    plt.tight_layout()
    if save_path:
        fig.savefig(save_path, dpi=150, bbox_inches="tight")
    return fig


def plot_calibration(
    y_true: np.ndarray,
    y_pred: np.ndarray,
    n_bins: int = 10,
    title: str = "Calibration Plot",
    save_path: Optional[str] = None,
    figsize: Tuple[int, int] = (8, 6),
) -> plt.Figure:
    """
    Calibration plot showing mean predicted age vs mean actual age per bin.

    A well-calibrated model has all points near the diagonal.
    """
    bins = np.linspace(y_true.min(), y_true.max(), n_bins + 1)
    bin_centers = []
    mean_preds = []
    std_preds = []
    counts = []

    for i in range(n_bins):
        mask = (y_true >= bins[i]) & (y_true < bins[i + 1])
        if mask.sum() > 0:
            bin_centers.append(y_true[mask].mean())
            mean_preds.append(y_pred[mask].mean())
            std_preds.append(y_pred[mask].std())
            counts.append(mask.sum())

    bin_centers = np.array(bin_centers)
    mean_preds = np.array(mean_preds)
    std_preds = np.array(std_preds)

    fig, ax = plt.subplots(figsize=figsize)

    lims = [bins[0] - 2, bins[-1] + 2]
    ax.plot(lims, lims, "--", color="#94A3B8", linewidth=1.5, label="Perfect calibration")
    ax.errorbar(
        bin_centers, mean_preds, yerr=std_preds,
        fmt="o-", color="#2563EB", capsize=4, markersize=8,
        linewidth=2, label="Model calibration",
    )

    ax.set_xlabel("Mean Chronological Age (years)", fontsize=12)
    ax.set_ylabel("Mean Predicted Age (years)", fontsize=12)
    ax.set_title(title, fontsize=14, fontweight="bold")
    ax.legend(fontsize=10)
    ax.grid(True, alpha=0.3)

    plt.tight_layout()
    if save_path:
        fig.savefig(save_path, dpi=150, bbox_inches="tight")
    return fig


def plot_subgroup_performance(
    results: pd.DataFrame,
    group_col: str,
    y_true_col: str = "chronological_age",
    y_pred_col: str = "predicted_age",
    title: str = "Subgroup Performance",
    save_path: Optional[str] = None,
    figsize: Tuple[int, int] = (10, 6),
) -> plt.Figure:
    """
    Bar chart of MAE and RMSE by subgroup.

    Args:
        results: DataFrame with columns for group, true age, predicted age.
        group_col: Column name for the subgroup variable.
    """
    groups = results[group_col].unique()
    maes = []
    rmses = []
    ns = []

    for g in groups:
        mask = results[group_col] == g
        y_true = results.loc[mask, y_true_col].values
        y_pred = results.loc[mask, y_pred_col].values
        maes.append(np.mean(np.abs(y_true - y_pred)))
        rmses.append(np.sqrt(np.mean((y_true - y_pred) ** 2)))
        ns.append(mask.sum())

    fig, ax = plt.subplots(figsize=figsize)
    x = np.arange(len(groups))
    width = 0.35

    bars1 = ax.bar(x - width / 2, maes, width, label="MAE", color="#2563EB", alpha=0.85)
    bars2 = ax.bar(x + width / 2, rmses, width, label="RMSE", color="#DC2626", alpha=0.85)

    ax.set_xlabel(group_col, fontsize=12)
    ax.set_ylabel("Error (years)", fontsize=12)
    ax.set_title(title, fontsize=14, fontweight="bold")
    ax.set_xticks(x)
    group_labels = [f"{g}\n(n={n:,})" for g, n in zip(groups, ns)]
    ax.set_xticklabels(group_labels, fontsize=10)
    ax.legend(fontsize=10)
    ax.grid(True, alpha=0.3, axis="y")

    for bar in bars1:
        ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.1,
                f"{bar.get_height():.1f}", ha="center", va="bottom", fontsize=9)
    for bar in bars2:
        ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.1,
                f"{bar.get_height():.1f}", ha="center", va="bottom", fontsize=9)

    plt.tight_layout()
    if save_path:
        fig.savefig(save_path, dpi=150, bbox_inches="tight")
    return fig


def plot_age_acceleration(
    chronological_ages: np.ndarray,
    biological_ages: np.ndarray,
    title: str = "Age Acceleration Distribution",
    save_path: Optional[str] = None,
    figsize: Tuple[int, int] = (8, 5),
) -> plt.Figure:
    """
    Histogram of age acceleration (biological - chronological age).

    Positive values indicate accelerated aging; negative values indicate
    decelerated aging relative to the population norm.
    """
    acceleration = biological_ages - chronological_ages

    fig, ax = plt.subplots(figsize=figsize)

    ax.hist(acceleration, bins=50, color="#2563EB", alpha=0.7, edgecolor="white", linewidth=0.5)
    ax.axvline(0, color="#DC2626", linewidth=2, linestyle="--", label="Zero acceleration")
    ax.axvline(acceleration.mean(), color="#059669", linewidth=2, linestyle="-",
               label=f"Mean = {acceleration.mean():.2f}")

    ax.set_xlabel("Age Acceleration (years)", fontsize=12)
    ax.set_ylabel("Count", fontsize=12)
    ax.set_title(title, fontsize=14, fontweight="bold")
    ax.legend(fontsize=10)
    ax.grid(True, alpha=0.3, axis="y")

    plt.tight_layout()
    if save_path:
        fig.savefig(save_path, dpi=150, bbox_inches="tight")
    return fig
