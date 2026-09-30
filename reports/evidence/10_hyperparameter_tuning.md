# T10 Leakage-Safe Hyperparameter Tuning Evidence

## Objective and scope

T10 tunes the four existing T09 classifiers using Train-only, whole-date,
expanding-window cross-validation. It then refits each selected configuration
on complete Train and evaluates it once on Validation. Test remains completely
unused for prediction, scoring, plotting, comparison, and selection.

No new model family, resampling, feature selection, threshold optimization,
final-model selection, Test evaluation, or T11+ work was performed.

## Chronological populations

| Split | Date range | Rows | T10 role |
|---|---|---:|---|
| Train | 2007-11-01 to 2015-01-12 | 99,546 | CV selection and final refit |
| Validation | 2015-01-13 to 2016-04-08 | 21,342 | One post-search evaluation per family |
| Test | 2016-04-09 to 2017-06-25 | 21,305 | Reserved; not evaluated |

## CV strategy and exact boundaries

Three expanding windows are built from the 2,541 ordered unique Train dates.
Applying `TimeSeriesSplit(n_splits=3)` to unique dates, then mapping complete
date blocks back to source rows, prevents observations from one calendar date
being divided across fold Train and fold Validation.

| Fold | Train date range | Validation date range | Train rows | Validation rows | Train unique dates | Validation unique dates |
|---:|---|---|---:|---:|---:|---:|
| 1 | 2007-11-01 to 2009-07-28 | 2009-07-29 to 2011-05-24 | 11,819 | 28,665 | 636 | 635 |
| 2 | 2007-11-01 to 2011-05-24 | 2011-05-25 to 2013-04-17 | 40,484 | 28,720 | 1,271 | 635 |
| 3 | 2007-11-01 to 2013-04-17 | 2013-04-18 to 2015-01-12 | 69,204 | 30,342 | 1,906 | 635 |

Every fold passed: zero row overlap, zero date overlap, and
`max(Train date) < min(Validation date)`.

## Leakage safeguards

Each fold starts from raw Train-period rows. Default T08 features are created,
then a new engineered `RainfallPreprocessor` fits only on that fold's Train
rows. It transforms fold Train and fold Validation without refitting. Fitted
row counts matched 11,819 / 40,484 / 69,204 for both scaled and unscaled paths.

Fold matrices are reused across candidates only after this fold-local fitting.
No preprocessing statistic from later Train dates, outer Validation, or Test
can influence an earlier fold. Logistic Regression uses scaled matrices; the
three tree/ensemble families use unscaled matrices. `RainTomorrow=Yes` remains
the positive class, and its probability is identified through `model.classes_`.

## Search objective, methods, and sizes

Average Precision (`PR-AUC`) is the sole primary selection metric. CV ROC-AUC,
Yes-class F1/recall, and balanced accuracy are recorded for interpretation and
do not influence candidate selection. Exact mean CV PR-AUC ties are resolved
only by original candidate number as a neutral deterministic tie-break. Every
current winner has a unique highest PR-AUC, so no tie-break was required.

| Model | Search method | Candidates | Folds | Fits | Search seconds |
|---|---|---:|---:|---:|---:|
| Logistic Regression | Exhaustive grid | 8 | 3 | 24 | 10.821 |
| Decision Tree | Deterministic randomized | 12 | 3 | 36 | 21.009 |
| Random Forest | Deterministic randomized | 8 | 3 | 24 | 55.149 |
| Gradient Boosting | Deterministic randomized | 6 | 3 | 18 | 96.338 |

The complete spaces are saved in `10_search_configurations.csv`. Logistic
Regression searches `C` and `class_weight`. Decision Tree searches criterion,
depth, split/leaf support, and class weight. Random Forest searches estimator
count, depth, split/leaf support, feature sampling, and class weight. Gradient
Boosting searches estimator count, learning rate, weak-tree controls, and
subsample.

## Best Train-CV configurations

| Model | Best parameters | CV PR-AUC mean | CV PR-AUC std | CV ROC-AUC mean | CV F1 mean | CV Recall mean | CV Balanced Accuracy mean |
|---|---|---:|---:|---:|---:|---:|---:|
| Logistic Regression | `C=0.1, class_weight=None` | 0.707032 | 0.003944 | 0.871800 | 0.607155 | 0.520694 | 0.731958 |
| Decision Tree | `criterion=gini, max_depth=10, min_samples_split=20, min_samples_leaf=20, class_weight=balanced` | 0.640795 | 0.015415 | 0.830150 | 0.589375 | 0.721195 | 0.754032 |
| Random Forest | `n_estimators=150, max_depth=20, min_samples_split=2, min_samples_leaf=1, max_features=sqrt, class_weight=None` | 0.722824 | 0.008788 | 0.877995 | 0.593762 | 0.483190 | 0.720426 |
| Gradient Boosting | `n_estimators=100, learning_rate=0.1, max_depth=3, min_samples_split=20, min_samples_leaf=5, subsample=0.8` | 0.721177 | 0.002886 | 0.875586 | 0.609896 | 0.516066 | 0.732200 |

## Tuned Validation metrics

| Model | Accuracy | Balanced Accuracy | Precision Yes | Recall Yes | F1 Yes | ROC-AUC | PR-AUC |
|---|---:|---:|---:|---:|---:|---:|---:|
| Logistic Regression | 0.854934 | 0.704893 | 0.734854 | 0.451517 | 0.559351 | 0.869321 | 0.677184 |
| Decision Tree | 0.800768 | 0.768042 | 0.508191 | 0.712776 | 0.593344 | 0.844848 | 0.635289 |
| Random Forest | 0.859385 | 0.700083 | 0.781341 | 0.431066 | 0.555605 | 0.883234 | 0.704679 |
| Gradient Boosting | 0.856714 | 0.704473 | 0.748846 | 0.447381 | 0.560127 | 0.875352 | 0.692540 |

## Tuned Validation confusion counts

| Model | TN | FP | FN | TP |
|---|---:|---:|---:|---:|
| Logistic Regression | 16,281 | 709 | 2,387 | 1,965 |
| Decision Tree | 13,988 | 3,002 | 1,250 | 3,102 |
| Random Forest | 16,465 | 525 | 2,476 | 1,876 |
| Gradient Boosting | 16,337 | 653 | 2,405 | 1,947 |

Each matrix reconciles to 16,990 Validation `No`, 4,352 Validation `Yes`, and
21,342 total rows.

## Baseline versus tuned Validation changes

| Model | Δ Accuracy | Δ Balanced Accuracy | Δ Precision Yes | Δ Recall Yes | Δ F1 Yes | Δ ROC-AUC | Δ PR-AUC |
|---|---:|---:|---:|---:|---:|---:|---:|
| Logistic Regression | -0.000094 | -0.000401 | +0.000153 | -0.000919 | -0.000660 | +0.000368 | +0.000354 |
| Decision Tree | +0.007544 | +0.081140 | +0.015004 | +0.205423 | +0.093174 | +0.157946 | +0.284610 |
| Random Forest | -0.001031 | -0.003639 | +0.001023 | -0.008042 | -0.006371 | +0.002579 | +0.004452 |
| Gradient Boosting | -0.000422 | -0.000863 | -0.001250 | -0.001608 | -0.001610 | +0.001446 | +0.001672 |

Decision Tree shows the largest changes, especially higher Yes recall and
ranking metrics, alongside 733 more false positives than its baseline. The
other three families show small mixed changes: their PR-AUC/ROC-AUC rise
slightly while several default-threshold metrics decline slightly. These are
descriptive results from one outer Validation period, not statistical
significance or a final-model decision.

## Runtime

Fold preprocessing for both representations took 1.792 seconds. Search took
183.317 seconds across the four families. Complete-Train preprocessing took
0.982 seconds. Selected-model final fits took 0.691 / 1.151 / 3.183 / 23.142
seconds for Logistic Regression / Decision Tree / Random Forest / Gradient
Boosting, respectively. The recorded preprocessing, searches, final fits, and
Validation predictions totaled approximately 214.533 seconds. Runtime is
environment-specific, and Gradient Boosting was the largest cost.

## Interpretation and limitations

Train-CV PR-AUC selected each configuration independently. Outer Validation
does not participate in parameter selection. The bounded spaces are meaningful
but not exhaustive, and three time folds cannot eliminate distribution shift.
Small Validation changes should not be overinterpreted. Class weighting caused
the Decision Tree's major default-threshold recall/false-positive trade-off.
No threshold was optimized.

No tuned configuration is declared the final project model. Test remains
reserved for later final evaluation after development decisions are complete.

## Remaining work for T11+

Any later class-balancing experiments, threshold optimization, feature
selection, final-model selection, and eventual one-time Test evaluation remain
future work. None of those activities was started in T10.

## Tests and verification

- Focused T10 tests: 11/11 passed.
- Full regression suite: 88/88 passed.
- `python -B scripts/verify_stage1.py`: T00-T08 all passed.
- `notebooks/09_hyperparameter_tuning.ipynb`: 11/11 code cells executed with
  zero saved errors and four inline `image/png` figure outputs.
- Test-isolation review found no Test prediction, probability, metric, plot,
  comparison, or selection path in the T10 implementation or artifacts.
- T09 baseline metrics remain unchanged; the maximum parsed floating-point
  difference against the recorded baseline values was `5.55e-17`.
- Raw SHA-256 after the full search:
  `573FD715CD69FCACC4DF32024D823B450AE3EDAAE7E8FF2EEB623ADBED424014`.

## Generated artifacts

Implementation and documentation:

- `src/fdm_rainfall/tuning.py`
- `tests/test_tuning.py`
- `notebooks/09_hyperparameter_tuning.ipynb`
- `docs/decisions/hyperparameter_tuning_decisions.md`
- `reports/evidence/10_hyperparameter_tuning.md`

Tables:

- `reports/tables/10_cv_fold_boundaries.csv`
- `reports/tables/10_search_configurations.csv`
- `reports/tables/10_cv_fold_results.csv`
- `reports/tables/10_cv_candidate_summary.csv`
- `reports/tables/10_best_hyperparameters.csv`
- `reports/tables/10_tuned_validation_metrics.csv`
- `reports/tables/10_tuned_validation_confusion_counts.csv`
- `reports/tables/10_final_fit_times.csv`
- `reports/tables/10_baseline_vs_tuned_validation.csv`
- `reports/tables/10_runtime_summary.csv`

Figures:

- `reports/figures/hyperparameter_tuning/10_tuned_validation_confusion_matrices.png`
- `reports/figures/hyperparameter_tuning/10_tuned_validation_roc_curves.png`
- `reports/figures/hyperparameter_tuning/10_tuned_validation_precision_recall_curves.png`
- `reports/figures/hyperparameter_tuning/10_baseline_vs_tuned_validation_metrics.png`

## Status

T10 is `DONE`. All required implementation, artifacts, focused and regression
tests, prior-stage verification, notebook validation, Test-isolation review,
baseline-preservation check, and raw-data checksum verification passed.
