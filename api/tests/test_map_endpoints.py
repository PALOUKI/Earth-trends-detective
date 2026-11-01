import asyncio
import json
from pathlib import Path

from httpx import ASGITransport, AsyncClient

from api.app.main import app


def test_precomputed_map_metadata_and_images_are_served(tmp_path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    tile_dir = Path("data/tiles/gistemp_tas_anom/full")
    tile_dir.mkdir(parents=True)
    (tile_dir / "slope.png").write_bytes(b"\x89PNG\r\n\x1a\nfixture")
    (tile_dir / "nonsignificant.png").write_bytes(b"\x89PNG\r\n\x1a\nfixture")
    (tile_dir / "palette.json").write_text(
        json.dumps(
            {
                "slope_unit": "K/year",
                "urls": {},
                "layers": {"nonsignificant": "nonsignificant.png"},
            }
        )
    )

    async def run_requests():
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            metadata = await client.get("/api/trend/gistemp_tas_anom?window=full")
            image = await client.get("/api/maps/gistemp_tas_anom/full/slope.png")
            return metadata, image

    metadata, image = asyncio.run(run_requests())

    assert metadata.status_code == 200
    assert metadata.json()["slope_unit"] == "K/year"
    assert metadata.json()["urls"]["nonsignificant"].endswith("nonsignificant.png")
    assert image.status_code == 200
    assert image.headers["content-type"] == "image/png"
    assert image.content.startswith(b"\x89PNG")
