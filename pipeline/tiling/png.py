"""Small dependency-free RGBA PNG encoder for global regular grids."""

from __future__ import annotations

import struct
import zlib


def encode_rgba_png(rgba: bytes, width: int, height: int) -> bytes:
    """Encode a row-major RGBA8 buffer as a standards-compliant PNG."""
    if len(rgba) != width * height * 4:
        raise ValueError("RGBA byte buffer must contain exactly width × height × 4 bytes")

    def chunk(kind: bytes, payload: bytes) -> bytes:
        body = kind + payload
        return struct.pack(">I", len(payload)) + body + struct.pack(">I", zlib.crc32(body))

    scanlines = b"".join(
        b"\0" + rgba[row * width * 4 : (row + 1) * width * 4] for row in range(height)
    )
    header = struct.pack(">2I5B", width, height, 8, 6, 0, 0, 0)
    return (
        b"\x89PNG\r\n\x1a\n"
        + chunk(b"IHDR", header)
        + chunk(b"IDAT", zlib.compress(scanlines, level=9))
        + chunk(b"IEND", b"")
    )
