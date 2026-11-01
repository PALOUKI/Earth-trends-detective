import numpy as np
import pytest

from pipeline.ingest.modis_vegetation import _aggregate_arrays


def test_modis_aggregation_applies_fill_qa_scale_and_40_cell_mean() -> None:
    raw = np.full((40, 80), 5000, dtype=np.int16)
    qa = np.zeros_like(raw)
    raw[:, :40] = 2500
    qa[0, 0] = 2  # snow/ice is excluded
    raw[0, 1] = -3000  # product fill value is excluded
    qa[:, 40:] = 3  # cloudy cells are excluded

    result = _aggregate_arrays(
        raw,
        qa,
        fill_value=-3000,
        valid_range=(-2000, 10000),
        scale_factor=10000,
    )

    assert result.shape == (1, 2)
    assert result[0, 0] == pytest.approx(0.25)
    assert np.isnan(result[0, 1])


def test_modis_aggregation_rejects_misaligned_arrays() -> None:
    with pytest.raises(ValueError, match="same-shaped 2D"):
        _aggregate_arrays(
            np.zeros((40, 40), dtype=np.int16),
            np.zeros((40, 39), dtype=np.int16),
            fill_value=-3000,
            valid_range=(-2000, 10000),
            scale_factor=10000,
        )
