"""Command line entry point for the data pipeline."""

import argparse
from pathlib import Path

from pipeline.ingest.gistemp import ingest


def main() -> None:
    parser = argparse.ArgumentParser(prog="pipeline")
    parser.add_argument("stage", choices=("ingest", "preprocess", "trends", "tiles"))
    parser.add_argument("variable")
    parser.add_argument(
        "--annual",
        action="store_true",
        help="Also compare monthly trends with annual-mean trends and save concordance fields.",
    )
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
        import time

        import pandas as pd
        import xarray as xr

        from pipeline.trends.annual import add_annual_comparison
        from pipeline.trends.base import analyze_grid
        from pipeline.trends.export import write_trend_cog

        source = xr.open_zarr(
            "data/processed/gistemp_tas_anom.zarr",
            chunks={"time": -1, "lat": -1, "lon": -1},
        )
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
            stats_started = time.perf_counter()
            result = analyze_grid(selected.chunk({"time": -1, "lat": -1, "lon": -1}))
            print(f"{name} monthly grid statistics: {time.perf_counter() - stats_started:.2f}s")
            result.attrs.update(
                {
                    "variable": args.variable,
                    "window": name,
                    "temporal_resolution": "monthly",
                    "source": "NASA GISS GISTEMP v4",
                }
            )
            if args.annual:
                annual = selected.groupby("time.year").mean("time", skipna=True)
                year_values = annual.year.values
                annual = annual.rename({"year": "time"}).assign_coords(
                    time=pd.to_datetime([f"{int(year)}-01-01" for year in year_values])
                )
                annual_started = time.perf_counter()
                annual_result = analyze_grid(
                    annual.chunk({"time": -1, "lat": -1, "lon": -1})
                )
                annual_result.n_valid.attrs["units"] = "years"
                print(
                    f"{name} annual grid statistics: "
                    f"{time.perf_counter() - annual_started:.2f}s"
                )
                result = add_annual_comparison(result, annual_result)
            output = output_root / f"trend_{name}.zarr"
            result.to_zarr(output, mode="w", zarr_format=2)
            cog_path = output_root / f"trend_{name}.tif"
            write_trend_cog(result, cog_path)
            print(output)
            print(cog_path)
        source.close()
        return
    if args.stage == "tiles":
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
