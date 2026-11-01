"""Command line entry point for the data pipeline."""

import argparse

from pipeline.ingest.gistemp import ingest


def main() -> None:
    parser = argparse.ArgumentParser(prog="pipeline")
    parser.add_argument("stage", choices=("ingest", "preprocess", "trends", "tiles"))
    parser.add_argument("variable")
    args = parser.parse_args()
    if args.variable != "gistemp_tas_anom":
        raise SystemExit(f"Unknown variable: {args.variable}")
    if args.stage == "ingest":
        print(ingest())
        return
    if args.stage == "preprocess":
        from pipeline.ingest.gistemp import prepare_gistemp

        print(prepare_gistemp())
        return
    if args.stage == "trends":
        from pathlib import Path

        import xarray as xr

        from pipeline.trends.base import analyze_grid

        source = xr.open_zarr("data/processed/gistemp_tas_anom.zarr")
        windows = {
            "full": (None, None),
            "2010-fin": ("2010-01-01", None),
            "2015-fin": ("2015-01-01", None),
        }
        output_root = Path("data/processed") / args.variable
        for name, (start, end) in windows.items():
            selected = source.temperature_anomaly
            if start or end:
                selected = selected.sel(time=slice(start, end))
            result = analyze_grid(selected)
            result.attrs.update({"variable": args.variable, "window": name})
            output = output_root / f"trend_{name}.zarr"
            result.to_zarr(output, mode="w", zarr_format=2)
            print(output)
        source.close()
        return
    if args.stage == "tiles":
        from pathlib import Path

        from pipeline.tiling.render import render_trend_map

        for window in ("full", "2010-fin", "2015-fin"):
            trends = Path("data/processed") / args.variable / f"trend_{window}.zarr"
            output = Path("data/tiles") / args.variable / window
            render_trend_map(trends, output)
            print(output)
        return
    raise SystemExit(f"Pipeline stage {args.stage!r} is not implemented yet.")


if __name__ == "__main__":
    main()
