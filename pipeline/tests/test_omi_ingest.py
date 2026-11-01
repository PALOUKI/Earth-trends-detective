import h5py
import numpy as np
import pytest

from pipeline.ingest.omi_no2 import FIELD, FILL_VALUE, _coarsen_daily_grid, _read_daily


def test_omi_coarsening_averages_valid_cloud_screened_values():
    source = np.full((720, 1440), FILL_VALUE, dtype=np.float32)
    source[:8, :8] = np.arange(64, dtype=np.float32).reshape(8, 8)

    grid = _coarsen_daily_grid(source)

    assert grid.shape == (90, 180)
    assert grid[0, 0] == pytest.approx(31.5)
    assert np.isnan(grid[0, 1])


def test_omi_reader_verifies_daily_field_units_and_date(tmp_path):
    path = tmp_path / "OMI-Aura_L3-OMNO2d_2010m0203_v004-test.he5"
    values = np.full((720, 1440), FILL_VALUE, dtype=np.float32)
    values[:8, :8] = 2.5e15
    with h5py.File(path, "w") as source:
        dataset = source.create_dataset(FIELD, data=values)
        dataset.attrs["Units"] = "molec/cm2"
        dataset.attrs["_FillValue"] = FILL_VALUE

    day, grid = _read_daily(path)

    assert day == np.datetime64("2010-02-03")
    assert grid[0, 0] == pytest.approx(2.5e15)
    assert np.isnan(grid[0, 1])


def test_omi_reader_rejects_wrong_units(tmp_path):
    path = tmp_path / "OMI-Aura_L3-OMNO2d_2010m0203_v004-test.he5"
    with h5py.File(path, "w") as source:
        dataset = source.create_dataset(FIELD, data=np.zeros((720, 1440), dtype=np.float32))
        dataset.attrs["Units"] = "molec/m2"

    with pytest.raises(ValueError, match="Unexpected OMNO2d units"):
        _read_daily(path)
