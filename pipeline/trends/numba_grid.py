"""Exact per-pixel trend statistics compiled and parallelized with Numba."""

from __future__ import annotations

import math

import numpy as np
import xarray as xr
from numba import get_num_threads, get_thread_id, njit, prange
from scipy import stats
from statsmodels.stats.multitest import multipletests

_METRICS = (
    "n_valid",
    "slope_ols",
    "slope_ols_lo",
    "slope_ols_hi",
    "p_ols",
    "slope",
    "slope_lo",
    "slope_hi",
    "p_mk",
    "p_value",
)
_SQRT2 = math.sqrt(2.0)
_Z_975 = 1.959963984540054
_HR_MAX_LAG = 3


@njit(cache=True)
def _beta_fraction(a: float, b: float, x: float) -> float:
    """Continued fraction used by the regularized incomplete beta function."""
    qab = a + b
    qap = a + 1.0
    qam = a - 1.0
    c = 1.0
    d = 1.0 - qab * x / qap
    if abs(d) < 1e-300:
        d = 1e-300
    d = 1.0 / d
    result = d
    for m in range(1, 201):
        m2 = 2 * m
        aa = m * (b - m) * x / ((qam + m2) * (a + m2))
        d = 1.0 + aa * d
        if abs(d) < 1e-300:
            d = 1e-300
        c = 1.0 + aa / c
        if abs(c) < 1e-300:
            c = 1e-300
        d = 1.0 / d
        result *= d * c
        aa = -(a + m) * (qab + m) * x / ((a + m2) * (qap + m2))
        d = 1.0 + aa * d
        if abs(d) < 1e-300:
            d = 1e-300
        c = 1.0 + aa / c
        if abs(c) < 1e-300:
            c = 1e-300
        d = 1.0 / d
        delta = d * c
        result *= delta
        if abs(delta - 1.0) < 3e-14:
            break
    return result


@njit(cache=True)
def _regularized_beta(x: float, a: float, b: float) -> float:
    if x <= 0.0:
        return 0.0
    if x >= 1.0:
        return 1.0
    log_term = (
        math.lgamma(a + b)
        - math.lgamma(a)
        - math.lgamma(b)
        + a * math.log(x)
        + b * math.log1p(-x)
    )
    term = math.exp(log_term)
    if x < (a + 1.0) / (a + b + 2.0):
        return term * _beta_fraction(a, b, x) / a
    return 1.0 - term * _beta_fraction(b, a, 1.0 - x) / b


@njit(cache=True)
def _student_two_sided_p(t_value: float, degrees: int) -> float:
    if not math.isfinite(t_value):
        return 0.0
    x = degrees / (degrees + t_value * t_value)
    return _regularized_beta(x, 0.5 * degrees, 0.5)


@njit(cache=True)
def _select_k(
    values: np.ndarray,
    kth: int,
    lower: int,
    upper: int,
) -> float:
    """Select within an existing partition, avoiding repeated full-array scans."""
    while lower < upper:
        pivot = values[(lower + upper) // 2]
        left = lower
        right = upper
        while left <= right:
            while values[left] < pivot:
                left += 1
            while values[right] > pivot:
                right -= 1
            if left <= right:
                temporary = values[left]
                values[left] = values[right]
                values[right] = temporary
                left += 1
                right -= 1
        if kth <= right:
            upper = right
        elif kth >= left:
            lower = left
        else:
            break
    return values[kth]


@njit(cache=True)
def _rank_average(values: np.ndarray) -> np.ndarray:
    order = np.argsort(values)
    ranks = np.empty(values.size, dtype=np.float64)
    start = 0
    while start < values.size:
        end = start + 1
        while end < values.size and values[order[end]] == values[order[start]]:
            end += 1
        rank = 0.5 * ((start + 1) + end)
        for index in range(start, end):
            ranks[order[index]] = rank
        start = end
    return ranks


@njit(cache=True)
def _tied_variance(sorted_values: np.ndarray) -> float:
    n = sorted_values.size
    variance = n * (n - 1) * (2 * n + 5)
    start = 0
    while start < n:
        end = start + 1
        while end < n and sorted_values[end] == sorted_values[start]:
            end += 1
        count = end - start
        variance -= count * (count - 1) * (2 * count + 5)
        start = end
    return variance / 18.0


@njit(cache=True)
def _fenwick_prefix(tree: np.ndarray, index: int) -> int:
    total = 0
    while index > 0:
        total += tree[index]
        index -= index & -index
    return total


@njit(cache=True)
def _mk_score(values: np.ndarray, sorted_values: np.ndarray) -> int:
    """Compute Mann-Kendall S in O(n log n) using a Fenwick rank tree."""
    tree = np.zeros(values.size + 1, dtype=np.int64)
    score = 0
    seen = 0
    for value in values:
        rank = np.searchsorted(sorted_values, value) + 1
        less = _fenwick_prefix(tree, rank - 1)
        less_equal = _fenwick_prefix(tree, rank)
        score += less - (seen - less_equal)
        index = rank
        while index < tree.size:
            tree[index] += 1
            index += index & -index
        seen += 1
    return score


@njit(cache=True, fastmath=True)
def _fill_pairwise_slopes(
    values: np.ndarray,
    months: np.ndarray,
    annual_rate_per_lag: np.ndarray,
    sen_slopes: np.ndarray,
    hr_slopes: np.ndarray,
    has_gaps: bool,
) -> None:
    """Fill Sen slope workspaces; compact inputs contain finite values only."""
    count = values.size
    pair = 0
    if has_gaps:
        for i in range(count - 1):
            for j in range(i + 1, count):
                difference = values[j] - values[i]
                sen_slopes[pair] = difference * 12.0 / (months[j] - months[i])
                hr_slopes[pair] = difference / (j - i)
                pair += 1
    else:
        for i in range(count - 1):
            for j in range(i + 1, count):
                difference = values[j] - values[i]
                sen_slopes[pair] = difference * annual_rate_per_lag[j - i]
                pair += 1


@njit(cache=True)
def _series_metrics(
    series: np.ndarray,
    time_index: np.ndarray,
    t_critical: np.ndarray,
    sen_slopes: np.ndarray,
    hr_slopes: np.ndarray,
) -> np.ndarray:
    max_n = series.size
    valid_count = 0
    for i in range(max_n):
        if math.isfinite(series[i]):
            valid_count += 1
    result = np.full(len(_METRICS), np.nan, dtype=np.float64)
    result[0] = valid_count
    if valid_count < 3:
        return result

    y = np.empty(valid_count, dtype=np.float64)
    months = np.empty(valid_count, dtype=np.float64)
    cursor = 0
    for i in range(max_n):
        if math.isfinite(series[i]):
            y[cursor] = series[i]
            months[cursor] = time_index[i]
            cursor += 1
    if np.max(y) == np.min(y):
        return result

    # OLS on elapsed calendar time, expressed in years.
    x_mean = np.mean(months)
    y_mean = np.mean(y)
    sxx = 0.0
    sxy = 0.0
    for i in range(valid_count):
        dx = months[i] - x_mean
        sxx += dx * dx
        sxy += dx * (y[i] - y_mean)
    if sxx <= 0.0:
        return result
    slope_month = sxy / sxx
    slope_year = slope_month * 12.0
    residual_sum = 0.0
    for i in range(valid_count):
        residual = (y[i] - y_mean) - slope_month * (months[i] - x_mean)
        residual_sum += residual * residual
    degrees = valid_count - 2
    standard_error = 12.0 * math.sqrt(residual_sum / degrees / sxx)
    t_value = slope_year / standard_error if standard_error > 0 else math.inf
    p_ols = _student_two_sided_p(abs(t_value), degrees)
    result[1] = slope_year
    result[2] = slope_year - t_critical[valid_count] * standard_error
    result[3] = slope_year + t_critical[valid_count] * standard_error
    result[4] = p_ols

    has_gaps = False
    for i in range(valid_count):
        if months[i] != i:
            has_gaps = True
            break
    tied = np.sort(y.copy())
    sen_variance = _tied_variance(tied)
    score = _mk_score(y, tied)
    pair_count = valid_count * (valid_count - 1) // 2
    if not has_gaps:
        hr_slopes = sen_slopes
    annual_rate_per_lag = np.empty(valid_count, dtype=np.float64)
    for lag in range(1, valid_count):
        annual_rate_per_lag[lag] = 12.0 / lag
    _fill_pairwise_slopes(
        y,
        months,
        annual_rate_per_lag,
        sen_slopes,
        hr_slopes,
        has_gaps,
    )

    pair_count = sen_slopes.size
    lower, upper = 0, pair_count - 1
    z_lower = -_Z_975
    ci_sigma = math.sqrt(sen_variance) if sen_variance > 0.0 else 0.0
    lower = max(int(np.rint((pair_count + z_lower * ci_sigma) / 2.0)) - 1, 0)
    upper = min(int(np.rint((pair_count - z_lower * ci_sigma) / 2.0)), pair_count - 1)
    middle_lo = (pair_count - 1) // 2
    middle_hi = pair_count // 2
    selected_ranks = np.array([lower, middle_lo, middle_hi, upper])
    # Select ranks in ascending order so subsequent quickselects operate on
    # progressively smaller partitions.
    ranks = np.sort(selected_ranks)
    selected = np.empty(4, dtype=np.float64)
    search_from = 0
    for i in range(4):
        if i > 0 and ranks[i] == ranks[i - 1]:
            selected[i] = selected[i - 1]
        else:
            selected[i] = _select_k(
                sen_slopes,
                ranks[i],
                search_from,
                pair_count - 1,
            )
            search_from = ranks[i] + 1
    values = np.empty(4, dtype=np.float64)
    for i in range(4):
        values[i] = selected[np.searchsorted(ranks, selected_ranks[i])]
    result[5] = 0.5 * (values[1] + values[2])
    result[6] = values[0]
    result[7] = values[3]

    # Classic Mann-Kendall, using tie-corrected variance.
    if sen_variance > 0.0:
        continuity = 1.0 if score > 0 else -1.0 if score < 0 else 0.0
        z_classic = (score - continuity) / math.sqrt(sen_variance)
        result[8] = math.erfc(abs(z_classic) / _SQRT2)

    # Hamed-Rao (1998): detrend with Sen's per-observation slope and use the
    # first three autocorrelation lags, the explicit PyMannKendall lag option.
    if has_gaps:
        hr_median_lo = _select_k(hr_slopes, middle_lo, 0, pair_count - 1)
        hr_median_hi = (
            hr_median_lo
            if middle_hi == middle_lo
            else _select_k(hr_slopes, middle_hi, middle_lo + 1, pair_count - 1)
        )
        hr_slope = 0.5 * (hr_median_lo + hr_median_hi)
    else:
        hr_slope = result[5] / 12.0
    detrended = np.empty(valid_count, dtype=np.float64)
    for i in range(valid_count):
        detrended[i] = y[i] - (i + 1) * hr_slope
    ranks = _rank_average(detrended)
    rank_mean = np.mean(ranks)
    acov_zero = 0.0
    for i in range(valid_count):
        centered = ranks[i] - rank_mean
        acov_zero += centered * centered
    if acov_zero <= 0.0:
        return result
    threshold = 1.959963984540054 / math.sqrt(valid_count)
    correction_sum = 0.0
    for lag in range(1, min(_HR_MAX_LAG, valid_count - 1) + 1):
        cross = 0.0
        for i in range(valid_count - lag):
            cross += (ranks[i] - rank_mean) * (ranks[i + lag] - rank_mean)
        autocorrelation = cross / acov_zero
        if autocorrelation > threshold or autocorrelation < -threshold:
            remaining = valid_count - lag
            correction_sum += remaining * (remaining - 1) * (remaining - 2) * autocorrelation
    inflation = 1.0 + 2.0 * correction_sum / (
        valid_count * (valid_count - 1) * (valid_count - 2)
    )
    adjusted_variance = sen_variance * inflation
    if adjusted_variance > 0.0:
        z_score = 0.0
        if score > 0:
            z_score = (score - 1.0) / math.sqrt(adjusted_variance)
        elif score < 0:
            z_score = (score + 1.0) / math.sqrt(adjusted_variance)
        result[9] = math.erfc(abs(z_score) / _SQRT2)
    return result


@njit(parallel=True)
def _parallel_grid_metrics(values: np.ndarray, t_critical: np.ndarray) -> np.ndarray:
    lat_count, lon_count, time_count = values.shape
    pixels = lat_count * lon_count
    flattened = values.reshape((pixels, time_count))
    time_index = np.arange(time_count, dtype=np.float64)
    output = np.empty((pixels, len(_METRICS)), dtype=np.float64)
    max_pairs = time_count * (time_count - 1) // 2
    thread_count = get_num_threads()
    # Reuse a pair-slope workspace per Numba worker instead of allocating up to
    # two multi-million-value arrays for every pixel.
    sen_workspaces = np.empty((thread_count, max_pairs), dtype=np.float32)
    hr_workspaces = np.empty((thread_count, max_pairs), dtype=np.float32)
    for pixel in prange(pixels):
        worker = get_thread_id()
        output[pixel] = _series_metrics(
            flattened[pixel],
            time_index,
            t_critical,
            sen_workspaces[worker],
            hr_workspaces[worker],
        )
    return output.reshape((lat_count, lon_count, len(_METRICS)))


def analyze_grid_numba(
    data: xr.DataArray,
    alpha_fdr: float = 0.10,
    slope_unit: str = "K/year",
    source: str = "NASA GISS GISTEMP v4",
) -> xr.Dataset:
    """Compute Base and Hamed-Rao statistics for every map cell in parallel."""
    if set(data.dims) != {"time", "lat", "lon"}:
        raise ValueError("Input must have exactly time, lat, and lon dimensions")
    ntime = data.sizes["time"]
    t_critical = np.full(ntime + 1, np.nan, dtype=np.float64)
    for n in range(3, ntime + 1):
        t_critical[n] = stats.t.ppf(0.975, n - 2)

    values = data.transpose("lat", "lon", "time")
    packed = xr.apply_ufunc(
        _parallel_grid_metrics,
        values,
        kwargs={"t_critical": t_critical},
        input_core_dims=[["time"]],
        output_core_dims=[["metric"]],
        vectorize=False,
        dask="parallelized",
        output_dtypes=[np.float64],
        dask_gufunc_kwargs={"output_sizes": {"metric": len(_METRICS)}},
    ).assign_coords(metric=list(_METRICS))
    result = xr.Dataset(
        {name: packed.sel(metric=name, drop=True) for name in _METRICS}
    ).compute()
    p_values = np.asarray(result.p_value.values)
    valid = np.isfinite(p_values)
    significant = np.zeros(p_values.shape, dtype=bool)
    if valid.any():
        significant[valid] = multipletests(
            p_values[valid], alpha=alpha_fdr, method="fdr_bh"
        )[0]
    result["significant_fdr"] = (("lat", "lon"), significant)
    result["n_valid"] = result.n_valid.astype(np.int32)
    slope = np.asarray(result.slope.values)
    sign_class = np.zeros(slope.shape, dtype=np.int8)
    sign_class[significant & (slope > 0)] = 1
    sign_class[significant & (slope < 0)] = -1
    result["sign_class"] = (("lat", "lon"), sign_class)
    result.attrs.update(
        {
            "alpha_fdr": alpha_fdr,
            "fdr_method": "Benjamini-Hochberg",
            "map_test": "Hamed-Rao modified Mann-Kendall p-values",
            "engine": "Numba @njit(parallel=True), xarray.apply_ufunc, Dask parallelized",
        }
    )
    units = {
        "n_valid": "months",
        "slope_ols": slope_unit,
        "slope_ols_lo": slope_unit,
        "slope_ols_hi": slope_unit,
        "p_ols": "1",
        "slope": slope_unit,
        "slope_lo": slope_unit,
        "slope_hi": slope_unit,
        "p_mk": "1",
        "p_value": "1",
        "significant_fdr": "1",
        "sign_class": "-1 significant negative, 0 not FDR-significant, 1 significant positive",
    }
    for metric, unit in units.items():
        result[metric].attrs["units"] = unit
        result[metric].attrs["source"] = source
    result.attrs["slope_unit"] = slope_unit
    result.attrs["source"] = source
    return result
