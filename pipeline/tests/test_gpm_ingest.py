import h5py
import numpy as np
import pytest

from pipeline.ingest.gpm_precipitation import _coarsen_monthly_grid, _read_month


def test_gpm_coarsening_masks_fill_and_averages_valid_source_cells():
    source = np.array(
        [[1, 3, -9999.9, 4], [5, 7, 8, 10], [2, 4, 6, 8], [4, 6, 8, 10]],
        dtype=np.float32,
    )

    grid = _coarsen_monthly_grid(source, fill_value=-9999.9, block_size=2)

    np.testing.assert_allclose(grid, [[4.0, 22 / 3], [4.0, 8.0]])


def test_gpm_reader_uses_source_time_units_and_coordinate_order(tmp_path):
    source_path = tmp_path / "verified-sample.HDF5"
    with h5py.File(source_path, "w") as source:
        grid = source.create_group("Grid")
        dataset = grid.create_dataset(
            "precipitation", data=np.arange(32, dtype=np.float32).reshape(1, 8, 4)
        )
        dataset.attrs["units"] = "mm/hr"
        dataset.attrs["_FillValue"] = np.float32(-9999.9)
        grid.create_dataset("lat", data=[1.5, 0.5, -0.5, -1.5])
        grid.create_dataset("lon", data=[-3.5, -2.5, -1.5, -0.5, 0.5, 1.5, 2.5, 3.5])
        source.attrs["FileHeader"] = (
            "DOI=10.5067/GPM/IMERG/3B-MONTH/07;"
            "StartGranuleDateTime=2024-01-01T00:00:00.000Z;TimeInterval=MONTH;"
        )

    month, values, lat, lon = _read_month(source_path, block_size=2)

    assert month == np.datetime64("2024-01-01")
    assert values.shape == (2, 4)
    np.testing.assert_array_equal(lat, [-1.5, -0.5, 0.5, 1.5])
    np.testing.assert_allclose(values, [[4.5, 12.5, 20.5, 28.5], [2.5, 10.5, 18.5, 26.5]])
    np.testing.assert_array_equal(lon, [-3.5, -2.5, -1.5, -0.5, 0.5, 1.5, 2.5, 3.5])


def test_gpm_reader_rejects_unexpected_units(tmp_path):
    path = tmp_path / "wrong-units.HDF5"
    with h5py.File(path, "w") as source:
        grid = source.create_group("Grid")
        dataset = grid.create_dataset("precipitation", data=np.zeros((1, 4, 4)))
        dataset.attrs["units"] = "mm/day"
        grid.create_dataset("lat", data=[-1.5, -0.5, 0.5, 1.5])
        grid.create_dataset("lon", data=[-1.5, -0.5, 0.5, 1.5])
        source.attrs["FileHeader"] = (
            "DOI=10.5067/GPM/IMERG/3B-MONTH/07;"
            "StartGranuleDateTime=2024-01-01T00:00:00.000Z;TimeInterval=MONTH;"
        )

    with pytest.raises(ValueError, match="Unexpected GPM precipitation units"):
        _read_month(path, block_size=2)
