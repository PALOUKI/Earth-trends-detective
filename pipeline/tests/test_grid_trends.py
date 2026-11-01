import numpy as np
import pandas as pd
import xarray as xr

from pipeline.trends.base import analyze_grid


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
