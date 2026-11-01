# Methods

## Monthly regional anomaly series

The GISTEMP v4 source already contains monthly anomalies. For a rectangular region, the MVP averages included grid cells with a cosine-of-latitude area weight. Missing cells are omitted independently at each month. The monthly climatology of the selected analysis period is removed for the displayed deseasonalized series; statistics use that deseasonalized series.

## Base trend

Ordinary least squares fits `y = a + b t` with time measured in years. The reported slope is `b` in K/year. A two-sided Student t test uses `n - 2` degrees of freedom. Its 95% confidence interval is `b ± t(0.975, n-2) × SE(b)`. This assumes a linear relationship and independent, normally distributed residuals; serial correlation can make the basic test too optimistic.

Sen's slope is the median of all pairwise slopes `(y[j]-y[i])/(t[j]-t[i])`. Its confidence bounds use SciPy's `theilslopes` implementation at 95%. Mann-Kendall tests for a monotonic trend without requiring normally distributed values. These tests are complementary: the OLS line estimates linear change, while Sen and Mann-Kendall are robust rank-based measures.

For Mann-Kendall, `S = sum(sign(y[j] - y[i]))` over all `i < j`; the standardized statistic is compared with the standard normal distribution. The reference implementation accounts for tied values in the variance. Hamed-Rao replaces the independent-observation variance with an autocorrelation-adjusted variance estimate; its p-value is therefore conditional on the chosen lag correction and should be read alongside the OLS and classic Mann-Kendall results.

## Autocorrelation-aware test

The advanced p-value uses the Hamed-Rao modified Mann-Kendall procedure, through the `pymannkendall` implementation. It adjusts the variance for significant serial autocorrelation. Some short or noisy samples can produce a non-positive corrected variance in the reference implementation; in that case the result is returned as unavailable rather than reporting a misleading p-value.

## Multiple testing

Spatial maps apply Benjamini-Hochberg false discovery rate correction with `alpha=0.10` across finite p-values. This is the project brief's chosen exploratory map threshold. It controls the expected false-discovery proportion under independence or certain positive dependence, not the probability of any false pixel. Under strong arbitrary spatial dependence, Benjamini-Yekutieli is a more conservative alternative.

## Limitations

Results describe statistical change, not its cause. Conclusions depend on the selected region and time window. Short periods, spatially varying data coverage, autocorrelation, and GISTEMP's blended land/ocean analysis affect interpretation. A trend can be interesting without meeting a significance threshold. Analysis is limited to linear trend summaries; it does not imply that the climate signal itself is linear.
