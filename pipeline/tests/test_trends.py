import numpy as np
import pymannkendall as mk
from scipy import stats

from pipeline.trends.base import (
    analyze_series,
    apply_fdr,
    classify_sign,
    deseasonalize_monthly,
)


def test_recovers_known_linear_slope_and_sen_matches_scipy() -> None:
    rng = np.random.default_rng(2026)
    months = np.arange(600)
    years = months / 12
    ar = np.zeros(months.size)
    noise = rng.normal(0, 0.15, months.size)
    for i in range(1, months.size):
        ar[i] = 0.35 * ar[i - 1] + noise[i]
    values = 0.02 * years + ar

    result = analyze_series(values)
    reference = stats.theilslopes(values, years)

    assert abs(result["slope"] - 0.02) < 0.001
    assert abs(result["slope"] - reference.slope) < 1e-12
    assert result["slope_lo"] == reference.low_slope
    assert result["slope_hi"] == reference.high_slope
    assert result["p_ols"] < 0.05


def test_missing_constant_and_short_series_are_explicit() -> None:
    values = np.array([1.0, np.nan, 2.0, 3.0, np.nan, 5.0])
    result = analyze_series(values)
    assert result["n_valid"] == 4
    assert result["slope"] is not None
    assert analyze_series(np.ones(24))["p_mk"] is None
    assert analyze_series(np.array([1.0, np.nan]))["slope_ols"] is None


def test_deseasonalize_removes_repeating_monthly_cycle() -> None:
    cycle = np.tile(np.arange(12, dtype=float), 4)
    anomalies, seasonal = deseasonalize_monthly(cycle)

    assert np.allclose(anomalies, 0)
    assert np.array_equal(seasonal[:12], np.arange(12, dtype=float))


def test_trend_methods_match_references_over_seeded_series() -> None:
    rng = np.random.default_rng(17)
    for _ in range(1000):
        values = rng.normal(size=36)
        result = analyze_series(values)
        sen = stats.theilslopes(values, np.arange(values.size) / 12)
        original = mk.original_test(values)
        hamed_rao = mk.hamed_rao_modification_test(values)
        assert abs(result["slope"] - sen.slope) < 1e-12
        assert abs(result["p_mk"] - original.p) < 1e-12
        if np.isfinite(hamed_rao.p):
            assert abs(result["p_value"] - hamed_rao.p) < 1e-12
        else:
            assert result["p_value"] is None


def test_fdr_does_not_increase_significant_pixel_count() -> None:
    p_values = np.array([0.001, 0.01, 0.03, 0.20, np.nan])
    uncorrected_count = int(np.sum(p_values < 0.10))
    significant = apply_fdr(p_values, alpha=0.10)
    classes = classify_sign(np.array([1, -1, 1, -1, 1]), significant)

    assert significant.sum() <= uncorrected_count
    assert significant[-1] is np.False_
    assert set(classes).issubset({-1, 0, 1})


def test_mann_kendall_false_positive_rate_is_reasonable_without_trend() -> None:
    rng = np.random.default_rng(2027)
    false_positives = 0
    simulations = 120
    for _ in range(simulations):
        result = analyze_series(rng.normal(size=120))
        false_positives += result["p_mk"] < 0.05

    assert false_positives / simulations < 0.12
