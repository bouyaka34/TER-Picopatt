from __future__ import annotations

import numpy as np
import pandas as pd


def summary_stats(df: pd.DataFrame, cols):
    """Compute descriptive statistics used in exploratory notebooks."""
    quantiles = df[cols].quantile([0.10, 0.25, 0.50, 0.75, 0.90], numeric_only=True).T
    return pd.DataFrame(
        {
            "mean": df[cols].mean(numeric_only=True),
            "std": df[cols].std(numeric_only=True),
            "min": df[cols].min(numeric_only=True),
            "p10": quantiles[0.10],
            "p25": quantiles[0.25],
            "median": quantiles[0.50],
            "p75": quantiles[0.75],
            "p90": quantiles[0.90],
            "max": df[cols].max(numeric_only=True),
        }
    )


def circular_mean_deg(series: pd.Series):
    """Circular mean for angles expressed in degrees."""
    radians = np.deg2rad(series.dropna().astype(float) % 360.0)
    if radians.size == 0:
        return np.nan
    angle = np.arctan2(np.sin(radians).mean(), np.cos(radians).mean())
    return np.rad2deg(angle) % 360.0
