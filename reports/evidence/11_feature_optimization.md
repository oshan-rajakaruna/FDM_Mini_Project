# T11 Controlled Feature / Representation Optimization Evidence

## Objective and boundary

T11 evaluates exactly four pre-declared T08 representations for each of the
four fixed T10-tuned model families. Representation selection uses Train-only
mean CV PR-AUC. Selected representations are refitted on all Train rows and
evaluated once on outer Validation. Test is not transformed for T11 modeling,
predicted, scored, plotted, compared, or used for selection.

No broad tuning, resampling, threshold optimization, extra feature search,
final-model selection, Test evaluation, or T12 work was performed.

## Variants and outer populations

- V0_DEFAULT: T08 default.
- V1_ADD_YEAR: V0 plus Year.
- V2_LOG_RAINFALL_REPLACE: `Rainfall_log1p` replaces raw Rainfall.
- V3_YEAR_AND_LOG_RAINFALL: V1 plus the Rainfall replacement.

Train remains 99,546 rows from 2007-11-01 through 2015-01-12. Validation
remains 21,342 rows from 2015-01-13 through 2016-04-08. Reserved Test remains
21,305 rows from 2016-04-09 through 2017-06-25.

## CV strategy and leakage safeguards

The same three T10 expanding windows over 2,541 unique Train dates were used:

| Fold | Train date range | Validation date range | Train rows | Validation rows | Train unique dates | Validation unique dates |
|---:|---|---|---:|---:|---:|---:|
| 1 | 2007-11-01 to 2009-07-28 | 2009-07-29 to 2011-05-24 | 11,819 | 28,665 | 636 | 635 |
| 2 | 2007-11-01 to 2011-05-24 | 2011-05-25 to 2013-04-17 | 40,484 | 28,720 | 1,271 | 635 |
| 3 | 2007-11-01 to 2013-04-17 | 2013-04-18 to 2015-01-12 | 69,204 | 30,342 | 1,906 | 635 |

All folds have zero row overlap, zero date overlap, whole-date membership, and
strict chronology. Twenty-four variant/scale fold representations were fitted
independently. Every learned median, Location fallback, category vocabulary,
and scaler statistic came from that fold's Train rows only. Fold Validation
was transform-only. Logistic Regression used scaled matrices; the other three
families used unscaled matrices.

## Controlled experiment and runtime

Four fixed models x four variants x three folds produced exactly 48 CV fits.
No hyperparameter changed from T10. The recorded end-to-end preprocessing, CV,
final-fit, and Validation-prediction time was 197.849 seconds. Fold
preprocessing took 9.712 seconds and final fits/predictions took 36.976
seconds. Detailed model/variant runtimes are in
`reports/tables/11_runtime_summary.csv`.

## Model-by-variant Train-CV PR-AUC

| Model | V0 mean +/- std | V1 mean +/- std | V2 mean +/- std | V3 mean +/- std |
|---|---:|---:|---:|---:|
| Logistic Regression | 0.707032 +/- 0.003944 | 0.705935 +/- 0.003164 | 0.708542 +/- 0.004509 | 0.707561 +/- 0.003963 |
| Decision Tree | 0.640795 +/- 0.015415 | 0.639196 +/- 0.014772 | 0.640794 +/- 0.015414 | 0.639195 +/- 0.014771 |
| Random Forest | 0.722824 +/- 0.008788 | 0.722548 +/- 0.007862 | 0.722811 +/- 0.008811 | 0.722559 +/- 0.007854 |
| Gradient Boosting | 0.721177 +/- 0.002886 | 0.721401 +/- 0.002877 | 0.721168 +/- 0.002900 | 0.721400 +/- 0.002881 |

Complete fold-level metrics, dates, row counts, feature counts, and runtimes
are saved in `reports/tables/11_cv_fold_results.csv`. The aggregate table also
records interpretive ROC-AUC, balanced accuracy, precision, recall, and F1;
none participates in representation selection.

## Selected representations

| Model | Selected variant | Mean CV PR-AUC | Std | Difference versus V0 | Tie-break |
|---|---|---:|---:|---:|---|
| Logistic Regression | V2_LOG_RAINFALL_REPLACE | 0.708542 | 0.004509 | +0.001510 | No |
| Decision Tree | V0_DEFAULT | 0.640795 | 0.015415 | 0.000000 | No |
| Random Forest | V0_DEFAULT | 0.722824 | 0.008788 | 0.000000 | No |
| Gradient Boosting | V1_ADD_YEAR | 0.721401 | 0.002877 | +0.000224 | No |

Selection sorts only by mean CV PR-AUC descending, followed by fixed variant
order for an exact tie. Outer Validation is not accepted by the selection
function.

## T11 outer Validation metrics

| Model | Variant | Accuracy | Balanced Accuracy | Precision Yes | Recall Yes | F1 Yes | ROC-AUC | PR-AUC |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| Logistic Regression | V2 | 0.854278 | 0.704396 | 0.731199 | 0.451287 | 0.558113 | 0.870140 | 0.678523 |
| Decision Tree | V0 | 0.800768 | 0.768042 | 0.508191 | 0.712776 | 0.593344 | 0.844848 | 0.635289 |
| Random Forest | V0 | 0.859385 | 0.700083 | 0.781341 | 0.431066 | 0.555605 | 0.883234 | 0.704679 |
| Gradient Boosting | V1 | 0.856855 | 0.704647 | 0.749519 | 0.447610 | 0.560495 | 0.875246 | 0.692330 |

## Validation confusion counts

| Model | TN | FP | FN | TP |
|---|---:|---:|---:|---:|
| Logistic Regression | 16,268 | 722 | 2,388 | 1,964 |
| Decision Tree | 13,988 | 3,002 | 1,250 | 3,102 |
| Random Forest | 16,465 | 525 | 2,476 | 1,876 |
| Gradient Boosting | 16,339 | 651 | 2,404 | 1,948 |

Each matrix reconciles to 16,990 Validation No, 4,352 Validation Yes, and
21,342 total rows.

## T09/T10/T11 comparison and interpretation

Relative to T10, Logistic Regression gained 0.001339 Validation PR-AUC and
0.000819 ROC-AUC with log Rainfall, while its threshold metrics declined
slightly. Decision Tree and Random Forest selected V0 and reproduce T10.
Gradient Boosting's Year variant gained 0.000174 balanced accuracy and 0.000368
F1, but lost 0.000210 PR-AUC. These changes are small and mixed.

Year hurt Train-CV PR-AUC for three families and gave Gradient Boosting only a
0.000224 gain. Log Rainfall helped Logistic Regression modestly, had negligible
effects on the tree families, and did not improve Gradient Boosting. Apparent
CV gains transferred partially for Logistic Regression but not for Gradient
Boosting's Validation PR-AUC. No effect is claimed material or statistically
significant, and no final model is selected.

The full seven-metric T09/T10/T11 comparison and all arithmetic differences
are saved in `reports/tables/11_t09_t10_t11_validation_comparison.csv`.

## Tests and verification

- Focused T11 tests: 12/12 passed.
- Full regression suite: 100/100 passed.
- `python -B scripts/verify_stage1.py`: T00-T08 all passed.
- `notebooks/10_feature_optimization.ipynb`: 10/10 code cells executed,
  zero saved errors, and four inline `image/png` outputs.
- All 48 expected fold results are present: three folds for each of 16
  model/variant combinations.
- Static and behavioral checks found no Test predictor, target, prediction,
  probability, metric, figure, comparison, or selection path.
- T09 baseline and T10 tuned-default metrics remain unchanged.
- Raw SHA-256 expected and observed:
  `573FD715CD69FCACC4DF32024D823B450AE3EDAAE7E8FF2EEB623ADBED424014`.

## Generated artifacts

Implementation and documentation:

- `src/fdm_rainfall/feature_optimization.py`
- `tests/test_feature_optimization.py`
- `notebooks/10_feature_optimization.ipynb`
- `docs/decisions/feature_optimization_decisions.md`
- `reports/evidence/11_feature_optimization.md`

Tables:

- `11_cv_fold_boundaries.csv`
- `11_feature_variants.csv`
- `11_fixed_model_configurations.csv`
- `11_cv_fold_results.csv`
- `11_model_variant_runtimes.csv`
- `11_model_variant_summary.csv`
- `11_representation_winners.csv`
- `11_validation_metrics.csv`
- `11_validation_confusion_counts.csv`
- `11_final_fit_times.csv`
- `11_t09_t10_t11_validation_comparison.csv`
- `11_runtime_summary.csv`

Figures:

- `11_train_cv_pr_auc_by_variant.png`
- `11_t10_vs_t11_validation_metrics.png`
- `11_validation_confusion_matrices.png`
- `11_validation_precision_recall_curves.png`

## Limitations and T12 handoff

The experiment is deliberately limited to four pre-declared representations,
three temporal folds, and fixed T10 parameters. Small differences can reflect
time-period variation. T12 must make any final-model decision using completed
development evidence before accessing Test, then perform only the reserved
one-time holdout evaluation.

## Status

T11 is `DONE`. All four variants and four fixed T10 model families were
evaluated across the required 48 Train-CV fits; PR-AUC-only selection, final
Train refits, Validation-only evaluation, artifacts, tests, prior-stage
verification, Test isolation, preservation checks, and checksum all passed.
