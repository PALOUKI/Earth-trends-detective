import numpy as np
import pandas as pd
import pymannkendall as mk
import xarray as xr
from scipy import stats

from pipeline.trends.annual import add_annual_comparison
from pipeline.trends.base import analyze_grid
from pipeline.trends.export import write_trend_cog


def test_grid_analysis_is_dask_parallelized_and_applies_fdr() -> None:
    time = pd.date_range("2000-01-01", periods=60, freq="MS")
    years = np.arange(time.size) / 12
    values = np.zeros((time.size, 2, 2), dtype=np.float64)
    values[:, 0, 0] = 0.05 * years
    values[:, 0, 1] = -0.03 * years
    values[:, 1, 0] = np.sin(years * 4)
    values[:, 1, 1] = np.nan
    data = xr.DataArray(
        values,
        dims=("time", "lat", "lon"),
        coords={"time": time, "lat": [-1, 1], "lon": [10, 12]},
    ).chunk({"time": -1, "lat": 1, "lon": 1})

    result = analyze_grid(data)

    assert result.sizes == {"lat": 2, "lon": 2}
    assert np.isclose(result.slope.sel(lat=-1, lon=10).compute(), 0.05)
    assert result.n_valid.sel(lat=1, lon=12).compute() == 0
    assert not result.significant_fdr.sel(lat=1, lon=12).item()
    assert np.isclose(result.slope_ols.sel(lat=-1, lon=10), 0.05)
    assert np.isfinite(result.p_mk.sel(lat=-1, lon=10))
    assert np.isfinite(result.p_value.sel(lat=-1, lon=10))


def test_numba_grid_matches_reference_methods_for_1000_seeded_pixels() -> None:
    rng = np.random.default_rng(2031)
    values = rng.normal(size=(36, 1, 1000))
    dates = pd.date_range("2000-01-01", periods=36, freq="MS")
    data = xr.DataArray(
        values,
        dims=("time", "lat", "lon"),
        coords={"time": dates, "lat": [0.0], "lon": np.arange(1000)},
    ).chunk({"time": -1, "lon": 100})

    result = analyze_grid(data)
    years = np.arange(36, dtype=float) / 12
    for pixel in range(1000):
        series = values[:, 0, pixel]
        sen = stats.theilslopes(series, years, alpha=0.95)
        ols = stats.linregress(years, series)
        mann_kendall = mk.original_test(series)
        hamed_rao = mk.hamed_rao_modification_test(series, lag=3)

        assert abs(result.slope.values[0, pixel] - sen.slope) < 1e-6
        assert abs(result.slope_lo.values[0, pixel] - sen.low_slope) < 1e-6
        assert abs(result.slope_hi.values[0, pixel] - sen.high_slope) < 1e-6
        assert abs(result.p_ols.values[0, pixel] - ols.pvalue) < 1e-9
        assert abs(result.p_mk.values[0, pixel] - mann_kendall.p) < 1e-12
        if np.isfinite(hamed_rao.p):
            assert abs(result.p_value.values[0, pixel] - hamed_rao.p) < 1e-4
        else:
            assert np.isnan(result.p_value.values[0, pixel])


def test_annual_comparison_adds_concordance_fields() -> None:
    time = pd.date_range("2000-01-01", periods=120, freq="MS")
    years = np.arange(time.size) / 12
    values = np.empty((time.size, 1, 2), dtype=float)
    values[:, 0, 0] = 0.02 * years + 0.01 * np.sin(np.arange(time.size))
    values[:, 0, 1] = -0.01 * years + 0.01 * np.cos(np.arange(time.size))
    monthly_data = xr.DataArray(
        values,
        dims=("time", "lat", "lon"),
        coords={"time": time, "lat": [0.0], "lon": [0.0, 2.0]},
    ).chunk({"time": -1, "lat": 1, "lon": 2})
    monthly = analyze_grid(monthly_data)
    annual_data = monthly_data.groupby("time.year").mean("time", skipna=True)
    annual_data = annual_data.rename({"year": "time"}).assign_coords(
        time=pd.date_range("2000-01-01", periods=10, freq="YS")
    )
    annual = analyze_grid(annual_data.chunk({"time": -1, "lat": 1, "lon": 2}))

    result = add_annual_comparison(monthly, annual)

    assert result.annual_sign_concordant.values.tolist() == [[True, True]]
    assert result.annual_significance_concordant.shape == (1, 2)
    assert "slope_annual" in result
    assert result.attrs["annual_comparison"]


def test_grid_matches_reference_with_missing_months_and_ties() -> None:
    values = np.tile(np.array([0.0, 0.0, 0.2, 0.2]), 24)
    values[7] = np.nan
    values[18] = np.nan
    dates = pd.date_range("2000-01-01", periods=values.size, freq="MS")
    data = xr.DataArray(
        values[:, None, None],
        dims=("time", "lat", "lon"),
        coords={"time": dates, "lat": [0.0], "lon": [0.0]},
    ).chunk({"time": -1})

    result = analyze_grid(data)
    valid = np.isfinite(values)
    elapsed_years = np.flatnonzero(valid) / 12
    sen = stats.theilslopes(values[valid], elapsed_years)
    mk_result = mk.original_test(values[valid])
    hr_result = mk.hamed_rao_modification_test(values, lag=3)

    assert abs(result.slope.item() - sen.slope) < 1e-6
    assert abs(result.slope_lo.item() - sen.low_slope) < 1e-6
    assert abs(result.slope_hi.item() - sen.high_slope) < 1e-6
    assert abs(result.p_mk.item() - mk_result.p) < 1e-12
    if np.isfinite(hr_result.p):
        assert abs(result.p_value.item() - hr_result.p) < 1e-4
    else:
        assert np.isnan(result.p_value.item())


def test_grid_metrics_write_to_cog_with_named_bands(tmp_path) -> None:
    values = np.random.default_rng(27).normal(size=(48, 1, 2))
    dates = pd.date_range("2000-01-01", periods=48, freq="MS")
    data = xr.DataArray(
        values,
        dims=("time", "lat", "lon"),
        coords={"time": dates, "lat": [0.0], "lon": [0.0, 2.0]},
    )
    trends = analyze_grid(data)
    path = write_trend_cog(trends, tmp_path / "trend.tif")

    import rasterio

    with rasterio.open(path) as source:
        assert source.crs.to_epsg() == 4326
        assert source.count == 12
        assert source.descriptions[0] == "slope_ols"
        assert source.tags(ns="IMAGE_STRUCTURE")["LAYOUT"] == "COG"
