import struct

import pytest

from pipeline.tiling.png import encode_rgba_png


def test_encoder_writes_valid_rgba_png_signature_and_header() -> None:
    png = encode_rgba_png(bytes((255, 0, 0, 255)), 1, 1)

    assert png[:8] == b"\x89PNG\r\n\x1a\n"
    assert struct.unpack(">2I", png[16:24]) == (1, 1)


def test_encoder_rejects_incorrect_buffer_size() -> None:
    with pytest.raises(ValueError):
        encode_rgba_png(b"\x00", 1, 1)
