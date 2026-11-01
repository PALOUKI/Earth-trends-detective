import numpy as np
from pyhdf.SD import SD, SDC

from pipeline.ingest.airs_temperature import _read


def test_airs_reader_verifies_month_grid_and_masks_fill(tmp_path) -> None:
    path = tmp_path / "AIRS.2010.01.01.L3.RetStd_IR031.v7.0.3.0.G20218213525.hdf"
    source = SD(str(path), SDC.WRITE | SDC.CREATE)
    field = source.create("SurfAirTemp_A", SDC.FLOAT32, (180, 360))
    values = np.full((180, 360), 280.0, dtype=np.float32)
    values[10, 20] = -9999.0
    field[:] = values
    field.attr("_FillValue").set(SDC.FLOAT32, -9999.0)
    source.end()

    timestamp, grid = _read(path)

    assert str(timestamp.date()) == "2010-01-01"
    assert grid.shape == (90, 180)
    assert np.nanmedian(grid) == 280.0
    assert np.isnan(grid).any()
