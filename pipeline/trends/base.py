"""Base and autocorrelation-aware trend statistics for monthly series."""

from __future__ import annotations

import numpy as np
import pymannkendall as mk
import xarray as xr
from scipy import stats
from statsmodels.stats.multitest import multipletests


def analyze_series(
    values: np.ndarray, months_per_year: float = 12.0
) -> dict[str, float | int | None]:
    """Analyze a one-dimensional monthly series, ignoring missing observations.

    Slopes are reported per year. The input should be deseasonalized anomalies.
    Degenerate or short series return explicit null statistics.
    """
    series = np.asarray(values, dtype=np.float64)
    valid = np.isfinite(series)
    y = series[valid]
    n = int(y.size)
    empty: dict[str, float | int | None] = {
        "n_valid": n,
        "slope_ols": None,
        "slope_ols_lo": None,
        "slope_ols_hi": None,
        "p_ols": None,
        "slope": None,
        "slope_lo": None,
        "slope_hi": None,
        "p_mk": None,
        "p_value": None,
    }
    if n < 3 or np.ptp(y) == 0:
        return empty

    # Preserve actual elapsed time across gaps; input indices are monthly.
    x = np.flatnonzero(valid).astype(np.float64) / months_per_year
    ols = stats.linregress(x, y)
    dof = n - 2
    tcrit = stats.t.ppf(0.975, dof)
    ols_se = float(ols.stderr)
    slope_per_year = float(ols.slope)

    sen = stats.theilslopes(y, x, alpha=0.95)
    mk_result = mk.original_test(y)
    hamed_rao = mk.hamed_rao_modification_test(y, lag=min(3, n - 1))
    p_hamed_rao = float(hamed_rao.p) if np.isfinite(hamed_rao.p) else None
    return {
        "n_valid": n,
        "slope_ols": slope_per_year,
        "slope_ols_lo": slope_per_year - tcrit * ols_se,
        "slope_ols_hi": slope_per_year + tcrit * ols_se,
        "p_ols": float(ols.pvalue),
        "slope": float(sen.slope),
        "slope_lo": float(sen.low_slope),
        "slope_hi": float(sen.high_slope),
        "p_mk": float(mk_result.p),
        # The reference implementation can yield negative corrected variance
        # on short/noisy series. Keep that unavailable instead of serializing NaN.
        "p_value": p_hamed_rao,
    }


def deseasonalize_monthly(values: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """Return monthly anomalies and the repeating 12-month climatology."""
    series = np.asarray(values, dtype=np.float64)
    months = np.arange(series.size) % 12
    seasonal = np.full(12, np.nan, dtype=np.float64)
    for month in range(12):
        sample = series[(months == month) & np.isfinite(series)]
        if sample.size:
            seasonal[month] = sample.mean()
    cycle = seasonal[months]
    return series - cycle, cycle


def apply_fdr(p_values: np.ndarray, alpha: float = 0.10) -> np.ndarray:
    """Apply Benjamini-Hochberg, preserving missing p-values as False."""
    p = np.asarray(p_values, dtype=np.float64)
    valid = np.isfinite(p)
    significant = np.zeros(p.shape, dtype=bool)
    if np.any(valid):
        significant[valid] = multipletests(p[valid], alpha=alpha, method="fdr_bh")[0]
    return significant


def classify_sign(slope: np.ndarray, significant: np.ndarray) -> np.ndarray:
    """Encode significant warming as 1, cooling as -1, and other cells as 0."""
    slope_values, sig = np.broadcast_arrays(np.asarray(slope, dtype=float), significant)
    classes = np.zeros(slope_values.shape, dtype=np.int8)
    classes[sig & (slope_values > 0)] = 1
    classes[sig & (slope_values < 0)] = -1
    return classes


def analyze_grid(data: xr.DataArray, alpha_fdr: float = 0.10) -> xr.Dataset:
    """Run Base and Hamed-Rao pixel statistics with Numba and Dask parallelism."""
    from pipeline.trends.numba_grid import analyze_grid_numba

    return analyze_grid_numba(data, alpha_fdr=alpha_fdr)
