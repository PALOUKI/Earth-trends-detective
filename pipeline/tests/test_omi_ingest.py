import h5py
import numpy as np
import pytest

from pipeline.ingest import omi_no2
from pipeline.ingest.omi_no2 import FIELD, FILL_VALUE, _coarsen_daily_grid, _read_daily

GRID_METADATA = (
    'XDim=1440\nYDim=720\n'
    'UpperLeftPointMtrs=(-180000000.000000,-90000000.000000)\n'
    'LowerRightMtrs=(180000000.000000,90000000.000000)\n'
    'PixelRegistration=HE5_HDFE_CENTER\nProjection=HE5_GCTP_GEO\n'
)


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
        source.create_dataset("HDFEOS INFORMATION/StructMetadata.0", data=GRID_METADATA)

    day, grid = _read_daily(path)

    assert day == np.datetime64("2010-02-03")
    assert grid[0, 0] == pytest.approx(2.5e15)
    assert np.isnan(grid[0, 1])


def test_omi_reader_rejects_wrong_units(tmp_path):
    path = tmp_path / "OMI-Aura_L3-OMNO2d_2010m0203_v004-test.he5"
    with h5py.File(path, "w") as source:
        dataset = source.create_dataset(FIELD, data=np.zeros((720, 1440), dtype=np.float32))
        dataset.attrs["Units"] = "molec/m2"
        source.create_dataset("HDFEOS INFORMATION/StructMetadata.0", data=GRID_METADATA)

    with pytest.raises(ValueError, match="Unexpected OMNO2d units"):
        _read_daily(path)


def test_omi_download_resumes_partial_payload_with_bounded_timeout(tmp_path, monkeypatch):
    payload = b"abcdef"
    partial = tmp_path / "OMI-Aura_L3-OMNO2d_2007m0326_v004-test.he5.partial"
    partial.write_bytes(b"abc")

    class Response:
        status_code = 206
        headers = {"Content-Range": "bytes 3-5/6"}

        def __enter__(self):
            return self

        def __exit__(self, *_args):
            return False

        def raise_for_status(self):
            return None

        def iter_content(self, chunk_size):
            assert chunk_size == 1024 * 1024
            yield payload[3:]

    class Session:
        def __init__(self):
            self.headers = {}
            self.cookies = {}
            self.auth = None
            self.calls = []

        def get(self, url, **kwargs):
            self.calls.append((url, kwargs))
            return Response()

    class Granule:
        def data_links(self, access):
            assert access == "https"
            return ["https://example.test/OMI-Aura_L3-OMNO2d_2007m0326_v004-test.he5"]

    template = Session()
    monkeypatch.setattr(
        omi_no2,
        "_is_complete_daily",
        lambda path: path.exists() and path.stat().st_size == len(payload),
    )
    if hasattr(omi_no2._THREAD_SESSIONS, "session"):
        del omi_no2._THREAD_SESSIONS.session

    result = omi_no2._download_one_omi(Granule(), tmp_path, template)
    worker_session = omi_no2._THREAD_SESSIONS.session

    assert result.read_bytes() == payload
    assert worker_session.calls[0][1]["headers"] == {"Range": "bytes=3-"}
    assert worker_session.calls[0][1]["timeout"] == (30, 120)
