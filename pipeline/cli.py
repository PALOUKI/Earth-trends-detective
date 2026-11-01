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
    raise SystemExit(f"Pipeline stage {args.stage!r} is not implemented yet.")


if __name__ == "__main__":
    main()
