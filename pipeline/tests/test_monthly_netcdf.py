import numpy as np
import pandas as pd
import xarray as xr

from pipeline.ingest.monthly_netcdf import PRODUCTS, _read_month, _valid_file


def test_merra_reader_masks_file_missing_value_and_uses_selected_flux(tmp_path):
    values = np.array(
        [[[1.0, 2.0, 3.0], [4.0, 5.0, 6.0], [7.0, 8.0, 1.0e15]]],
        dtype=np.float32,
    )
    dataset = xr.Dataset(
        {"EVAP": (("time", "lat", "lon"), values)},
        coords={
            "time": [pd.Timestamp("2000-01-01")],
            "lat": [-90.0, 0.0, 90.0],
            "lon": [-180.0, 0.0, 179.375],
        },
    )
    dataset["EVAP"].attrs = {"units": "kg m-2 s-1", "fmissing_value": 1.0e15}
    path = tmp_path / "MERRA2_400.tavgM_2d_flx_Nx.200001.nc4"
    dataset.to_netcdf(path, engine="netcdf4")

    month, grid = _read_month(path, PRODUCTS["merra2_flux"])

    assert month == pd.Timestamp("2000-01-01")
    assert np.isfinite(grid[0, 0])
    assert np.isnan(grid[-1, -1])
    assert np.nanmax(grid) < 1.0e14


def test_gldas_reader_uses_topsoil_moisture_and_verified_units(tmp_path):
    values = np.full((1, 2, 2), 12.0, dtype=np.float32)
    dataset = xr.Dataset(
        {"SoilMoi0_10cm_inst": (("time", "lat", "lon"), values)},
        coords={
            "time": [pd.Timestamp("2000-01-01")],
            "lat": [-59.875, 89.875],
            "lon": [-179.875, 179.875],
        },
    )
    dataset["SoilMoi0_10cm_inst"].attrs = {"units": "kg m-2"}
    path = tmp_path / "GLDAS_NOAH025_M.A200001.021.nc4"
    dataset.to_netcdf(path, engine="netcdf4")

    assert _valid_file(path, PRODUCTS["gldas_noah_monthly"])
    month, grid = _read_month(path, PRODUCTS["gldas_noah_monthly"])

    assert month == pd.Timestamp("2000-01-01")
    assert np.allclose(grid[np.isfinite(grid)], 12.0)
