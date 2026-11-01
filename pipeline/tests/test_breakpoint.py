import numpy as np
import pandas as pd
from scipy.stats import rankdata

from pipeline.trends.breakpoint import analyze_pettitt


def test_pettitt_matches_pyhomogeneity_statistic_and_reports_original_date() -> None:
    values = np.array([0.0, 0.1, np.nan, 0.0, 0.2, 2.0, 2.1, 2.2, 2.0])
    dates = pd.date_range("2000-01-01", periods=values.size, freq="MS").strftime("%Y-%m").tolist()
    valid = values[np.isfinite(values)]
    ranks = rankdata(valid, method="average")
    n = valid.size
    u = 2 * np.cumsum(ranks)[:-1] - np.arange(1, n) * (n + 1)
    split = int(np.argmax(np.abs(u)))
    statistic = float(abs(u[split]))
    expected_p = min(1.0, 2.0 * np.exp(-6.0 * statistic**2 / (n**3 + n**2)))

    result = analyze_pettitt(values, dates)

    assert result is not None
    assert result["date"] == dates[np.flatnonzero(np.isfinite(values))[split]]
    assert np.isclose(result["statistic"], statistic)
    assert np.isclose(result["p"], expected_p)
    assert bool(result["significant"]) == (expected_p < 0.05)


def test_pettitt_returns_no_result_for_constant_or_too_short_data() -> None:
    dates = pd.date_range("2000-01-01", periods=20, freq="MS").strftime("%Y-%m").tolist()
    assert analyze_pettitt(np.ones(20), dates) is None
    assert analyze_pettitt(np.array([1.0, np.nan]), ["2000-01", "2000-02"]) is None
