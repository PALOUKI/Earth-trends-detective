"""Command line entry point for the data pipeline."""

import argparse
from pathlib import Path

from pipeline.ingest.gistemp import ingest as ingest_gistemp
from pipeline.variables import VARIABLE_CONFIG


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
    if args.variable not in VARIABLE_CONFIG:
        raise SystemExit(f"Unknown variable: {args.variable}")
    if args.stage == "ingest":
        if args.variable == "gistemp_tas_anom":
            print(ingest_gistemp())
        elif args.variable == "gpm_precipitation":
            from pipeline.ingest.gpm_precipitation import ingest as ingest_gpm

            print(ingest_gpm())
        elif args.variable == "omi_no2":
            from pipeline.ingest.omi_no2 import ingest as ingest_omi

            print(ingest_omi())
        elif args.variable in {"merra2_flux", "gldas_noah_monthly"}:
            from pipeline.ingest.monthly_netcdf import (
                download_monthly_netcdf,
                prepare_monthly_netcdf,
            )

            download_monthly_netcdf(args.variable)
            print(prepare_monthly_netcdf(args.variable))
        else:
            from pipeline.ingest.modis_vegetation import download_modis, prepare_modis

            vegetation_index = args.variable.removeprefix("modis_")
            download_modis()
            print(prepare_modis(variable=vegetation_index))
        return
    if args.stage == "preprocess":
        if args.variable == "gistemp_tas_anom":
            from pipeline.ingest.gistemp import prepare_gistemp

            print(prepare_gistemp())
        elif args.variable == "gpm_precipitation":
            from pipeline.ingest.gpm_precipitation import prepare_gpm

            print(prepare_gpm())
        elif args.variable == "omi_no2":
            from pipeline.ingest.omi_no2 import prepare_omi

            print(prepare_omi())
        elif args.variable in {"merra2_flux", "gldas_noah_monthly"}:
            from pipeline.ingest.monthly_netcdf import prepare_monthly_netcdf

            print(prepare_monthly_netcdf(args.variable))
        else:
            from pipeline.ingest.modis_vegetation import prepare_modis

            print(prepare_modis(variable=args.variable.removeprefix("modis_")))
        return
    if args.stage == "trends":
        import time

        import pandas as pd
        import xarray as xr

        from pipeline.trends.annual import add_annual_comparison
        from pipeline.trends.base import analyze_grid
        from pipeline.trends.export import write_trend_cog

        config = VARIABLE_CONFIG[args.variable]
        source = xr.open_zarr(config["path"], chunks={"time": -1, "lat": -1, "lon": -1})
        windows = {
            "full": (None, None),
            "2010-fin": ("2010-01-01", None),
            "2015-fin": ("2015-01-01", None),
        }
        output_root = Path("data/processed") / args.variable
        for name, (start, end) in windows.items():
            seasonal_adjustment = bool(config.get("remove_monthly_climatology", False))
            selected = source[config["field"]]
            if start or end:
                selected = selected.sel(time=slice(start, end))
            if selected.sizes.get("time", 0) < 120:
                print(f"Skipping {name}: fewer than 120 monthly records are available.")
                continue
            if seasonal_adjustment:
                monthly_climatology = selected.groupby("time.month").mean(
                    "time", skipna=True
                )
                selected = selected.groupby("time.month") - monthly_climatology
            stats_started = time.perf_counter()
            result = analyze_grid(
                selected.chunk({"time": -1, "lat": -1, "lon": -1}),
                slope_unit=str(config["rate_unit"]),
                source=str(config["source"]),
            )
            print(f"{name} monthly grid statistics: {time.perf_counter() - stats_started:.2f}s")
            result.attrs.update(
                {
                    "variable": args.variable,
                    "window": name,
                    "temporal_resolution": "monthly",
                    "source": config["source"],
                    "seasonal_adjustment": (
                        "Removed per grid cell using the window's monthly climatology."
                        if seasonal_adjustment
                        else "Source GISTEMP values are already monthly anomalies."
                    ),
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
                    annual.chunk({"time": -1, "lat": -1, "lon": -1}),
                    slope_unit=str(config["rate_unit"]),
                    source=str(config["source"]),
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

        windows = VARIABLE_CONFIG[args.variable]["windows"]
        slope_unit = VARIABLE_CONFIG[args.variable]["rate_unit"]

        for window in windows:
            trends = Path("data/processed") / args.variable / f"trend_{window}.zarr"
            output = Path("data/tiles") / args.variable / window
            render_trend_map(trends, output, slope_unit=str(slope_unit))
            print(output)
        return
    raise SystemExit(f"Pipeline stage {args.stage!r} is not implemented yet.")


if __name__ == "__main__":
    main()
