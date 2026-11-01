# Methods

## Monthly regional anomaly series

For a rectangular region, the application averages included grid cells with a cosine-of-latitude area weight. Missing cells are omitted independently at each month. GISTEMP v4 already contains monthly temperature anomalies; MODIS vegetation indices use a monthly climatology removed per grid cell before trend calculation. The regional display also removes the selected period's monthly climatology. Statistics use the deseasonalized series.

## Base trend

Ordinary least squares fits `y = a + b t` with time measured in years. The slope unit follows the selected variable (for example K/year for GISTEMP and index/year for MODIS NDVI/EVI). A two-sided Student t test uses `n - 2` degrees of freedom. Its 95% confidence interval is `b ± t(0.975, n-2) × SE(b)`. This assumes a linear relationship and independent, normally distributed residuals; serial correlation can make the basic test too optimistic.

Sen's slope is the median of all pairwise slopes `(y[j]-y[i])/(t[j]-t[i])`. Its confidence bounds use SciPy's `theilslopes` implementation at 95%. Mann-Kendall tests for a monotonic trend without requiring normally distributed values. These tests are complementary: the OLS line estimates linear change, while Sen and Mann-Kendall are robust rank-based measures.

For Mann-Kendall, `S = sum(sign(y[j] - y[i]))` over all `i < j`; the standardized statistic is compared with the standard normal distribution. The reference implementation accounts for tied values in the variance. Hamed-Rao replaces the independent-observation variance with an autocorrelation-adjusted variance estimate; its p-value is therefore conditional on the chosen lag correction and should be read alongside the OLS and classic Mann-Kendall results.

## Autocorrelation-aware test

The advanced p-value uses the Hamed-Rao modified Mann-Kendall procedure. It detrends with Sen's slope, ranks the residuals, and adjusts the variance using the first three autocorrelation lags that exceed the 95% white-noise bounds. The lag limit is explicit (`lag=3` in `pymannkendall`) and is used consistently in the regional and grid paths. Some short or noisy samples can produce a non-positive corrected variance in the reference implementation; in that case the result is returned as unavailable rather than reporting a misleading p-value.

## Multiple testing

Spatial maps apply Benjamini-Hochberg false discovery rate correction with `alpha=0.10` across finite p-values. This is the project brief's chosen exploratory map threshold. It controls the expected false-discovery proportion under independence or certain positive dependence, not the probability of any false pixel. Under strong arbitrary spatial dependence, Benjamini-Yekutieli is a more conservative alternative.

At global 2° resolution, every valid grid cell receives OLS slope/95% CI/t-test, Sen slope/95% CI, classic Mann-Kendall, and Hamed-Rao statistics. The kernel is compiled with Numba `@njit(parallel=True)` and called through `xarray.apply_ufunc` with Dask parallelization. Hamed-Rao p-values receive Benjamini-Hochberg correction at FDR 0.10 for the map. Pairwise Sen slopes use float32 storage to control memory; seeded comparisons against SciPy are tested to an absolute tolerance of 1e-6 K/year. The grid took 161.42 seconds for 16,200 cells and 1,761 months on the four-core development container, above the brief's two-minute target.

The `--annual` pipeline option repeats the analysis on calendar-year means and stores annual slope, p-value, significance, and sign-class fields alongside boolean maps showing monthly/annual sign and FDR-significance concordance.

## On-demand Pettitt change point

The regional and point APIs apply Pettitt's rank-based homogeneity test to the displayed deseasonalized monthly anomalies. They report the candidate split date, its analytic approximation `min(1, 2 exp(-6 K² / (n³+n²)))`, the maximum absolute rank statistic `K`, and whether `p < 0.05`. Missing values are skipped and the date points to the final valid month before the split. A detected shift is a statistical candidate, not a cause; a sustained linear trend can also influence a one-break test, so interpret this result alongside the trend analysis. The implementation follows the statistic and analytic p-value option in [pyHomogeneity](https://github.com/mmhs013/pyHomogeneity); its default Monte Carlo p-value is deliberately not used because it is stochastic.

## Limitations

Results describe statistical change, not its cause. Conclusions depend on the selected region and time window. Short periods, spatially varying data coverage, autocorrelation, and GISTEMP's blended land/ocean analysis affect interpretation. A trend can be interesting without meeting a significance threshold. Analysis is limited to linear trend summaries; it does not imply that the climate signal itself is linear.
