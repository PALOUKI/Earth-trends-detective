"""Analysis of externally downloaded observation series (Giovanni/AppEEARS/CDO)."""

from __future__ import annotations

import csv
import io
from dataclasses import dataclass

import numpy as np
import pandas as pd

from pipeline.trends.base import analyze_series, deseasonalize_monthly


@dataclass(frozen=True)
class ExternalAnalysis:
    dates: list[str]
    values: list[float | None]
    seasonal: list[float | None]
    anomalies: list[float | None]
    statistics: dict[str, float | int | None]
    start: str
    end: str
    n_months: int


def analyze_monthly_observations(
    dates: list[str], values: list[float | None], *, minimum_months: int = 36
) -> ExternalAnalysis:
    """Aggregate observations by calendar month and analyze a regular monthly series."""
    parsed = pd.to_datetime(pd.Series(dates), errors="coerce", utc=True)
    numeric = pd.to_numeric(pd.Series(values), errors="coerce")
    frame = pd.DataFrame({"date": parsed, "value": numeric}).dropna()
    frame = frame[np.isfinite(frame["value"].to_numpy(dtype=float))]
    if frame.empty:
        raise ValueError("No rows contain both a valid date and a finite numeric value.")
    frame["month"] = frame["date"].dt.strftime("%Y-%m")
    monthly = frame.groupby("month", sort=True)["value"].mean()
    full_index = pd.period_range(monthly.index[0], monthly.index[-1], freq="M").astype(str)
    monthly = monthly.reindex(full_index)
    if len(monthly) < minimum_months:
        raise ValueError(
            f"At least {minimum_months} calendar months are required; found {len(monthly)}."
        )
    data = monthly.to_numpy(dtype=float)
    adjusted, seasonal = deseasonalize_monthly(data)
    stats = analyze_series(adjusted)

    def nullable(array: np.ndarray) -> list[float | None]:
        return [float(x) if np.isfinite(x) else None for x in array]

    return ExternalAnalysis(
        dates=list(full_index),
        values=nullable(data),
        seasonal=nullable(seasonal[np.arange(len(data)) % 12]),
        anomalies=nullable(adjusted),
        statistics=stats,
        start=full_index[0],
        end=full_index[-1],
        n_months=len(full_index),
    )


def parse_csv_series(
    content: str, date_column: str, value_column: str
) -> tuple[list[str], list[float | None]]:
    if len(content.encode("utf-8")) > 5_000_000:
        raise ValueError("CSV files must be 5 MB or smaller.")
    reader = csv.DictReader(io.StringIO(content))
    if (
        not reader.fieldnames
        or date_column not in reader.fieldnames
        or value_column not in reader.fieldnames
    ):
        raise ValueError("Selected columns were not found in the CSV header.")
    dates: list[str] = []
    values: list[float | None] = []
    for row in reader:
        dates.append(str(row.get(date_column, "")))
        try:
            number = float(str(row.get(value_column, "")).strip())
            values.append(number if np.isfinite(number) else None)
        except (TypeError, ValueError):
            values.append(None)
    if not dates:
        raise ValueError("The CSV contains no data rows.")
    return dates, values
