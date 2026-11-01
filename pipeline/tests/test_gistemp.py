import numpy as np
import pandas as pd
import xarray as xr


def test_gistemp_schema_and_metadata(tmp_path) -> None:
    from pipeline.ingest.gistemp import prepare_gistemp

    time = pd.date_range("2000-01-01", periods=132, freq="MS") + pd.Timedelta(days=14)
    data = np.ones((132, 2, 3), dtype=np.float32)
    dataset = xr.Dataset(
        {"tempanomaly": (("time", "lat", "lon"), data)},
        coords={"time": time, "lat": [-1.0, 1.0], "lon": [0.0, 120.0, 240.0]},
    )
    import gzip

    source = tmp_path / "sample.nc.gz"
    netcdf = tmp_path / "fixture.nc"
    dataset.to_netcdf(netcdf, engine="scipy")
    with netcdf.open("rb") as raw, gzip.open(source, "wb") as stream:
        stream.write(raw.read())
    output = tmp_path / "normalized.zarr"

    prepare_gistemp(source, tmp_path / "sample.nc", output)
    normalized = xr.open_zarr(output)

    assert normalized.temperature_anomaly.dims == ("time", "lat", "lon")
    assert normalized.time.values[0] == np.datetime64("2000-01-01")
    assert np.all((normalized.lon.values >= -180) & (normalized.lon.values <= 180))
    assert normalized.attrs["crs"] == "EPSG:4326"
    assert normalized.attrs["doi"] == "10.1029/2023JD040179"
    assert "n_valid" in normalized
