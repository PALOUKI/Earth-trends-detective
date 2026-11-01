import numpy as np
import xarray as xr

from pipeline.regions import area_weighted_region_series


def test_region_mean_ignores_missing_cells_and_uses_cosine_weights() -> None:
    values = np.array([[[2.0], [4.0]], [[np.nan], [8.0]]])
    dataset = xr.Dataset(
        {"temperature_anomaly": (("time", "lat", "lon"), values)},
        coords={"time": ["2000-01-01", "2000-02-01"], "lat": [0.0, 60.0], "lon": [0.0]},
    )

    series = area_weighted_region_series(dataset, (-1.0, -1.0, 1.0, 61.0))

    assert np.allclose(series.values, [8 / 3, 8.0])
