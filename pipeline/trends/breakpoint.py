"""On-demand Pettitt change-point test for one monthly series."""

from __future__ import annotations

import numpy as np
from scipy.stats import rankdata


def analyze_pettitt(values: np.ndarray, dates: list[str]) -> dict[str, str | float | bool] | None:
    """Return Pettitt's largest rank shift and its analytic p-value.

    The reported date is the last valid month before the candidate split, matching
    pyHomogeneity's one-based change-point convention. Missing months are skipped.
    """
    series = np.asarray(values, dtype=np.float64)
    valid_positions = np.flatnonzero(np.isfinite(series))
    valid = series[valid_positions]
    n = valid.size
    if n < 3 or np.ptp(valid) == 0:
        return None

    ranks = rankdata(valid, method="average")
    cumulative_ranks = np.cumsum(ranks)[:-1]
    split_indices = np.arange(1, n, dtype=np.float64)
    statistic_by_split = 2.0 * cumulative_ranks - split_indices * (n + 1.0)
    split = int(np.argmax(np.abs(statistic_by_split)))
    statistic = float(abs(statistic_by_split[split]))
    p_value = float(min(1.0, 2.0 * np.exp(-6.0 * statistic**2 / (n**3 + n**2))))
    original_position = int(valid_positions[split])
    if original_position >= len(dates):
        raise ValueError("Pettitt dates and series must have the same length")
    return {
        "date": dates[original_position],
        "p": p_value,
        "significant": p_value < 0.05,
        "statistic": statistic,
    }
