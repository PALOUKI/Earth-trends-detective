"""Compare monthly and calendar-year trend signs and significance maps."""

from __future__ import annotations

import numpy as np
import xarray as xr


def add_annual_comparison(monthly: xr.Dataset, annual: xr.Dataset) -> xr.Dataset:
    """Attach annual metrics and monthly-vs-annual concordance to a monthly result."""
    result = monthly.copy()
    for metric in ("slope", "p_value", "significant_fdr", "sign_class"):
        result[f"{metric}_annual"] = annual[metric]
    monthly_slope = np.asarray(monthly.slope.values)
    annual_slope = np.asarray(annual.slope.values)
    comparable = np.isfinite(monthly_slope) & np.isfinite(annual_slope)
    result["annual_sign_concordant"] = (
        ("lat", "lon"),
        comparable & (np.sign(monthly_slope) == np.sign(annual_slope)),
    )
    result["annual_significance_concordant"] = (
        ("lat", "lon"),
        comparable
        & (
            np.asarray(monthly.significant_fdr.values)
            == np.asarray(annual.significant_fdr.values)
        ),
    )
    result.attrs["annual_comparison"] = (
        "Monthly vs calendar-year means; sign and FDR-significance concordance."
    )
    return result
