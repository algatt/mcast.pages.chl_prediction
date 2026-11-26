# Chlorophyll forecasting around Malta — research review

26 November 2026 · Experiment v2 · Historical observations through 2025 and the saved near-real-time evaluation of 14 November 2026

The strongest result is the next-day forecast of satellite-observed chlorophyll. On the 2025 test year, the promoted model reduced log-scale RMSE by 6.84% relative to damped persistence. The four-day gain was smaller. At seven days the evidence depends on how neighbouring days are handled. Operational performance remains an open question because the saved near-real-time evaluation reconstructs some forecasts with files retrieved after their issue times.

## What the 2025 experiment establishes

The project retains missing L3 observations, uses chronological splits, keeps the longest lead's targets within each split, builds the reference climatology on the training period, and compares against a fitted blend of the latest observation and the target month's usual value. The L4 gap-filled comparison is correctly labelled as a consistency check. These choices make the historical comparison informative.

I ran the existing reproduction check against the local NetCDFs and model bundles. The shared inputs, targets, original model and baseline scores passed. The promoted step 09 model reproduced its 2025 log-RMSE and scored-pixel counts at all three leads.

| Lead from issue day | Model log-RMSE | Blend log-RMSE | Gain in 2025 | 95% interval using 7-day blocks | Gain in 14 Nov NRT replay | Scored NRT issue days |
|---|---:|---:|---:|---:|---:|---:|
| +1 day | 0.09174 | 0.09847 | +6.84% | +4.38% to +9.25% | −5.26% | 16 |
| +4 days | 0.10375 | 0.10812 | +4.04% | +0.59% to +7.76% | −12.98% | 13 |
| +7 days | 0.11057 | 0.11350 | +2.58% | −1.60% to +6.96% | −11.76% | 10 |

Gain is the percentage reduction in log10 RMSE against the blend on paired pixel-days. Positive values favour the model. The NRT column reproduces the saved evaluation's own eligibility rules. It covers part of one autumn and has the timing limitation below.

**Uncertainty check.** The project bootstrap keeps each issue day's pixels together, then draws individual days independently. For the table I used 3,000 paired circular block-bootstrap replicates, seed 42, on the 358 calendar issue days from 1 January to 24 December 2025. I resampled the daily model and blend squared-error sums together, retained zero-coverage days and truncated each replicate to 358 days. The source was step 12's `issue_days.csv`, restricted to the exact step 09 test dates. Its point gains and pixel counts match the model bundle. With 14-day blocks, the intervals were +4.38% to +9.41%, +0.46% to +8.12% and −2.05% to +7.35%. The saved independent-day interval for +7 days was +0.16% to +4.86%.

## Findings in order of priority

### 1. The archive stopped collecting after the product change

The 24 November afternoon run and both 25 November runs failed. The 26 November morning run also exhausted all three retries. The local log reports that the pinned NRT chlorophyll version `202211` disappeared and that the catalogue offered `202611`. The last archived L3 CHL observation was 22 November. SST and both wind passes reached 23 November. The collector opens all remote products before saving any of them, so a failure on CHL also interrupts collection of the other products.

**Action.** Capture the replacement feed separately while overlap is available. Check coordinates, units, valid-pixel coverage, paired log-CHL differences and feature compatibility before feeding it to the model. Preserve the old files, mark the version boundary, and let healthy sources continue when another fails. Step 01 also identifies retirement dates for historical product pins. Include version identifiers in its CHL cache filenames or validate existing file metadata before reusing a download. Preserve a checksummed copy of the historical inputs used for the reported scores.

Evidence in [archive.py](chlforecast/archive.py), the local `data/raw/nrt_archive/scheduled_runs.log` and step 01.

### 2. The NRT replay can use inputs acquired after forecast issue

`archive.load` chooses one version of each observation date for the whole time series. When the first eligible issue had no on-time copy, it returns the first late copy. Conversely, a revision legitimately available for a later issue can be ignored. Step 07 derives eligibility from the calendar and reconstructs predictions with the current bundle. A row in its evaluation therefore does not establish that the forecast existed at 20:30 UTC.

I reproduced the 14 November replay gains from the local holdings, then compared stored retrieval timestamps with each issue cutoff. On **11 of 16** scored +1 days, at least one of the two newest required CHL/SST inputs was absent from the local archive at issue time. On **9 days** the archive had no CHL history at all by cutoff. Across the original 92,919 scored +1 pixel-days, only 25,125 had any CHL history using versions retrieved by that issue. These counts establish local availability. They cannot establish when Copernicus first made the files available upstream.

**Action.** For each issue, select the newest version of each eligible observation retrieved by that issue's cutoff, including revisions. Keep missing inputs missing and record the fallback used. Record file-level completion times since the collector currently stamps the entire run at its start. Save the actual issue timestamp, product versions, input manifest, model identifier and predictions at issuance. Verify the frozen predictions against a separately defined target version. Label archive replays separately from forecasts actually issued. Report non-issuance, fallback coverage and comparable paired scores.

Evidence in [archive.py](chlforecast/archive.py), [step 07](07-NRT-Input-Validation.ipynb) and the [saved NRT evaluation](data/processed/nrt_evaluation/20261114T171050Z/gain_intervals.json).

### 3. The model-selection decision needs a fixed endpoint and a publishing path

The hedge test begins on 15 November and calls for a decision after 30 scored +1 days. Step 07 uses every eligible day on each subsequent rerun, so both the sample and decision can change after day 30. The decision compares two alternatives against the model. The map and primary NetCDF field are written from the model before that decision is computed. A recorded hedge or blend win would still leave that run's primary forecast pointing to the original model.

**Action.** Define the first 30 eligible issue days and freeze the result once. Specify one primary comparison or account for the two comparisons. Decide whether +1 alone selects a method for all leads. Apply the persisted choice to the next issuance and check that its published field matches the chosen method. Keep all three candidates in the verification record. Report each season and repeat the evaluation over a longer span.

Evidence in [step 07](07-NRT-Input-Validation.ipynb) and [the hedge configuration](chlforecast/config.py).

### 4. Historical gains and map coverage need distinct denominators

The scoring pool gives a clear day with thousands of valid targets much more influence than a cloudy day with a few hundred. The NRT regression score additionally requires a finite persistence prediction, removing pixels where the deployed model falls back to climatology. The bloom score includes every observed target in the model mask. These choices answer different questions. There is just one full held-out year, and step 06 had already examined its errors before the step 09 improvements. Step 11 explicitly labels its earlier comparison years as in-sample.

**Action.** Report the current pixel-weighted metric alongside an equal-issue-day metric, target coverage, and model-versus-blend skill on all observable forecast pixels. Retain a second common-pixel table for plain persistence. Break results down by season, target coverage, coastal distance and age of the last CHL observation. Use expanding-year backtests that refit models, climatologies and blend coefficients inside each fold. Reserve a subsequent period for confirmation. For accuracy under persistent clouds, a matchup with independent in-water observations would address a question the L4 comparison cannot resolve.

Step 11B already tests whether the distinction between NRT and historical CHL explains the autumn losses. On its 11 common +1 issue days, gain was about −6.7% with NRT CHL inputs and targets and −6.8% with MY inputs and targets, using NRT temperature throughout. Changing CHL product alone did little on these days. Repeat this comparison across more seasons and both sides of the November version change before attributing the loss to a product shift.

Evidence in [step 11B's matched comparison](data/processed/my_vs_nrt/20261114T130505Z_part_b/inputs_targets_test.json) and [the paired scoring code](chlforecast/scoring.py).

### 5. The warning is a relative chlorophyll exceedance with a high false-alarm ratio

The target is a single observed pixel-day at least 0.2 log10 units above its pixel's monthly climatology, approximately 1.58 times the usual concentration. That is a reproducible remote-sensing target. Calling it a bloom warning adds an ecological interpretation that requires validation. In the saved +1 NRT evaluation the classifier issued 5,102 pixel warnings, caught 16.2% of observed exceedances and had a 93.1% false-alarm ratio. At +4 days the corresponding figures were 5.8% and 97.6%. Even in 2025 the classifier's Brier skill versus the simple anomaly rule was −1.59%, −1.37% and −0.97% across the three leads.

**Action.** Label the maps as probabilities of unusually high chlorophyll. Keep the anomaly rule as a candidate for publication. If the intended use is field sampling, define an alert by spatial extent, duration, lead time and an acceptable false-alarm cost. Score distinct events and the number of alerts a field team would have received. Recalibrate probabilities and choose thresholds using earlier held-out dates, then evaluate them on fresh dates. Test any proposed ecological bloom definition against independent event records or field observations.

Evidence in [blooms.py](chlforecast/blooms.py) and the [saved warning scores](data/processed/nrt_evaluation/20261114T171050Z/bloom_scores.json).

### 6. Wind is worth testing as a predictor of uncertainty

Step 12's “next-day change” compares the target with the latest available CHL. At +1 day the freshest possible reference was measured two calendar days before the target. Cloud gaps make some intervals longer. The reported 1.92-fold excess of sudden changes in the windiest fifth could therefore partly reflect observation age or coverage.

I repeated the comparison using only pixels observed on both issue day minus one and issue day plus one. I kept the original model mask, CHL quality bounds, minimum of 500 paired pixels per day, seasonal top-decile definition, wind classes and weekly bootstrap. The original analysis reproduced at **1.92×** (95% interval **1.26–3.01**). The fixed two-day comparison gave **2.24×** (**1.30–4.03**, 1,510 wind-eligible days). The association survives this check. Coverage still selects which days and pixels can contribute.

**Action.** Run a controlled comparison of the current model with and without the strongest wind in the prior three days and a wind-coverage indicator. Evaluate spread as well as mean concentration. A useful first test is whether prediction intervals widen appropriately on windy days while retaining their stated coverage on held-out years. Step 12's signed-change correlation of about +0.03 gives little support for assuming wind predicts the direction of change.

Evidence in [step 12](12-Wind-Event-Check.ipynb) and its [daily results](data/processed/wind_check/20261114T142542Z/issue_days.csv).

## Implementation order

1. Restore collection across the Copernicus version boundary and retain an auditable overlap.
2. Introduce per-issue input selection and immutable forecast outputs. Start a clean prospective scorecard.
3. Reissue the historical comparison with blocked intervals and coverage denominators. Freeze the hedge decision procedure before its evaluation matures.
4. Backtest wind and warning calibration on multiple held-out years. Promote changes only after comparison with the existing blend and anomaly rules.

Two small maintenance fixes would help future readers reproduce this work. Step 11 constructs both ends of its comparison window in the same calendar year, which will reverse the dates when the archive runs from autumn into January. Represent the window by a start and a duration. The repository README also leads with v1's XGBoost description and later gives v1's +3-day results. Lead the README with v2's scikit-learn histogram gradient boosting model, +1/+4/+7-day horizons and v2 reproduction command.

The review used existing model bundles, local observations, archived versions and saved results. No models were retrained and no service, data product or forecast publication was changed.
