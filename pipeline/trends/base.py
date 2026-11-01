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
    hamed_rao = mk.hamed_rao_modification_test(y)
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


_GRID_METRICS = ("n_valid", "slope", "slope_lo", "slope_hi", "p_value")


def _fast_ols_metrics(values: np.ndarray) -> np.ndarray:
    """Vector-friendly OLS metrics for exploratory map cells."""
    y = np.asarray(values, dtype=np.float64)
    valid = np.isfinite(y)
    n = int(valid.sum())
    if n < 3:
        return np.asarray([n, np.nan, np.nan, np.nan, np.nan])
    x = np.arange(y.size, dtype=np.float64) / 12.0
    xv = x[valid]
    yv = y[valid]
    x_bar = xv.mean()
    y_bar = yv.mean()
    centered_x = xv - x_bar
    centered_y = yv - y_bar
    sxx = np.dot(centered_x, centered_x)
    if sxx == 0:
        return np.asarray([n, np.nan, np.nan, np.nan, np.nan])
    slope = float(np.dot(centered_x, centered_y) / sxx)
    residual = centered_y - slope * centered_x
    dof = n - 2
    standard_error = float(np.sqrt(np.dot(residual, residual) / dof / sxx))
    if standard_error == 0:
        p_value = 0.0 if slope != 0 else 1.0
        margin = 0.0
    else:
        statistic = abs(slope / standard_error)
        p_value = float(2 * stats.t.sf(statistic, dof))
        margin = float(stats.t.ppf(0.975, dof) * standard_error)
    return np.asarray([n, slope, slope - margin, slope + margin, p_value])


def analyze_grid(data: xr.DataArray, alpha_fdr: float = 0.10) -> xr.Dataset:
    """Run fast OLS map statistics over lat/lon using xarray's Dask gufunc path.

    The selected-region path remains the authoritative Base+Hamed-Rao analysis.
    Grid OLS is used to keep the discovery map computationally tractable.
    """
    if set(data.dims) != {"time", "lat", "lon"}:
        raise ValueError("Input must have exactly time, lat, and lon dimensions")
    packed = xr.apply_ufunc(
        _fast_ols_metrics,
        data.transpose("lat", "lon", "time"),
        input_core_dims=[["time"]],
        output_core_dims=[["metric"]],
        vectorize=True,
        dask="parallelized",
        output_dtypes=[np.float64],
        dask_gufunc_kwargs={"output_sizes": {"metric": len(_GRID_METRICS)}},
    ).assign_coords(metric=list(_GRID_METRICS))
    result = xr.Dataset({name: packed.sel(metric=name, drop=True) for name in _GRID_METRICS})
    p_values = np.asarray(result.p_value.values)
    fdr = apply_fdr(p_values, alpha=alpha_fdr)
    result["significant_fdr"] = (("lat", "lon"), fdr)
    result["sign_class"] = (("lat", "lon"), classify_sign(result.slope.values, fdr))
    result.attrs["alpha_fdr"] = alpha_fdr
    result.attrs["fdr_method"] = "Benjamini-Hochberg"
    result.attrs["map_test"] = (
        "OLS slope t test; regional results also include Sen, Mann-Kendall, and Hamed-Rao"
    )
    return result
