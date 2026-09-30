# T09 Baseline Model Development Evidence

## Objective and completed scope

T09 implements four reproducible, untuned classification baselines for
`RainTomorrow`: Logistic Regression, Decision Tree, Random Forest, and Gradient
Boosting. Each model was fitted on Train only and evaluated on Validation only.
No tuning, resampling, result-based feature selection, threshold optimization,
final-model selection, or T10+ implementation was performed.

## Algorithms and rationale

| Algorithm | Baseline rationale |
|---|---|
| Logistic Regression | Interpretable linear reference; uses scaled numerical inputs. |
| Decision Tree | Simple nonlinear and interaction-aware tree baseline; no scaling needed. |
| Random Forest | Bagging ensemble that reduces single-tree instability and handles mixed engineered weather signals. |
| Gradient Boosting | Sequential boosting ensemble that supplies a different nonlinear strategy from Random Forest. |

## Exact model configurations

- `LogisticRegression(max_iter=1000, random_state=42)`
- `DecisionTreeClassifier(random_state=42)`
- `RandomForestClassifier(random_state=42, n_jobs=-1)`
- `GradientBoostingClassifier(random_state=42)`

All other estimator settings are scikit-learn defaults. The non-default values
are technical settings for repeatability, Logistic Regression convergence, and
Random Forest execution parallelism; they were not tuned.

## Data representation and leakage controls

The exact T06 labelled whole-date split was recreated:

| Split | Date range | Rows |
|---|---|---:|
| Train | 2007-11-01 to 2015-01-12 | 99,546 |
| Validation | 2015-01-13 to 2016-04-08 | 21,342 |
| Test | 2016-04-09 to 2017-06-25 | 21,305 |

The default T08 feature engineer produced the established 34 raw engineered
inputs, and Train-fitted preprocessing produced 89 finite columns. Both model
paths used processed shapes Train `(99,546, 89)` and Validation `(21,342, 89)`.
Logistic Regression used the scaled path; Decision Tree, Random Forest, and
Gradient Boosting used the unscaled path. Both preprocessors report 99,546 fit
rows, confirming that preprocessing parameters came from Train only.

The implementation order was:

`raw labelled data -> chronological split -> feature engineering -> fit preprocessing on Train -> transform Validation -> fit models on Train -> evaluate Validation`

The established preprocessing helper also produced its standard Test
transformation. No baseline estimator received Test predictors, no Test
prediction or probability was generated, and `y_test` was not used in any
metric. No Test result appears in T09 tables, figures, or decisions.

## Validation class balance

Validation contains 4,352 `Yes` rows out of 21,342 rows, a positive-class
prevalence of 20.3917%. This imbalance makes overall accuracy potentially
misleading and motivates balanced accuracy, Yes-class precision/recall/F1, and
PR-AUC alongside ROC-AUC and confusion counts.

## Validation metrics

| Model | Accuracy | Balanced Accuracy | Precision (Yes) | Recall (Yes) | F1 (Yes) | ROC-AUC | PR-AUC |
|---|---:|---:|---:|---:|---:|---:|---:|
| Logistic Regression | 0.855028 | 0.705294 | 0.734701 | 0.452436 | 0.560011 | 0.868953 | 0.676829 |
| Decision Tree | 0.793225 | 0.686902 | 0.493187 | 0.507353 | 0.500170 | 0.686902 | 0.350679 |
| Random Forest | 0.860416 | 0.703721 | 0.780318 | 0.439108 | 0.561976 | 0.880655 | 0.700227 |
| Gradient Boosting | 0.857136 | 0.705336 | 0.750096 | 0.448989 | 0.561736 | 0.873906 | 0.690868 |

## Validation confusion counts

| Model | TN | FP | FN | TP |
|---|---:|---:|---:|---:|
| Logistic Regression | 16,279 | 711 | 2,383 | 1,969 |
| Decision Tree | 14,721 | 2,269 | 2,144 | 2,208 |
| Random Forest | 16,452 | 538 | 2,441 | 1,911 |
| Gradient Boosting | 16,339 | 651 | 2,398 | 1,954 |

## Interpretation

Random Forest has the highest baseline accuracy (0.860416), Yes precision
(0.780318), Yes F1 (0.561976), ROC-AUC (0.880655), and PR-AUC (0.700227).
Gradient Boosting has the highest balanced accuracy (0.705336), narrowly above
Logistic Regression (0.705294). Decision Tree has the highest Yes recall
(0.507353), but this comes with 2,269 false positives, Yes precision of
0.493187, and substantially lower ranking metrics.

The comparison shows a clear precision/recall trade-off. Random Forest issues
the fewest false rain predictions and has the strongest positive precision,
but it misses 2,441 of 4,352 actual rain events. Decision Tree detects more
actual rain events, yet its extra false positives reduce precision and overall
accuracy. Logistic Regression and Gradient Boosting occupy similar middle
positions at the default thresholds.

Accuracy between 0.793 and 0.860 does hide weak minority detection: no baseline
recalls more than 50.74% of Validation `Yes` rows. Balanced accuracies of about
0.687 to 0.705 make the gap clearer. PR-AUC is especially useful here because
it evaluates positive retrieval against a 0.203927 prevalence reference;
Random Forest, Gradient Boosting, and Logistic Regression substantially exceed
that reference, while the single Decision Tree is much weaker at probability
ranking. These are associative validation observations, not causal claims.

The different outcomes are consistent with distinct baseline structures: a
linear decision surface, an unconstrained single tree, a bagging ensemble, and
a sequential boosting ensemble. T09 does not treat any of these validation
leaders as an optimized or final project model.

## Runtime

Measured full-data fit times were 0.812 seconds for Logistic Regression, 1.991
seconds for Decision Tree, 2.380 seconds for Random Forest, and 27.650 seconds
for Gradient Boosting. All four model fits plus Validation predictions and
probabilities took 33.807 seconds. Creating both preprocessing representations
took 1.198 seconds. These timings are environment-specific.

## Limitations and T10+ boundary

The evidence covers one fixed chronological Validation period with default
decision thresholds and essentially default estimator behavior. It does not
assess hyperparameter alternatives, class weighting, resampling, calibration,
threshold trade-offs, feature alternatives, or final Test generalization.
Those remain T10+ development questions. The Test set must stay reserved until
a later final evaluation, and no final model is selected here.

## Tests and checks executed

- `python -m unittest tests.test_modeling -v`: 12 focused T09 tests passed.
- `notebooks/08_baseline_models.ipynb`: 8/8 code cells executed with zero error
  outputs.
- The four saved figure files were visually inspected for readable labels,
  legends, and counts.
- `python -m unittest discover -s tests -v`: all 77 tests passed, including the
  12 new T09 tests and all existing T00-T08 tests.
- `python scripts/verify_stage1.py`: all T00-T08 verification checks passed.
- Raw SHA-256 matched
  `573FD715CD69FCACC4DF32024D823B450AE3EDAAE7E8FF2EEB623ADBED424014`
  before and after notebook execution.

## Generated artifacts

Code, tests, notebook, and documentation:

- `src/fdm_rainfall/modeling.py`
- `tests/test_modeling.py`
- `notebooks/08_baseline_models.ipynb`
- `docs/decisions/baseline_model_decisions.md`
- `reports/evidence/09_baseline_models.md`

Tables:

- `reports/tables/09_baseline_model_configurations.csv`
- `reports/tables/09_processed_train_validation_shapes.csv`
- `reports/tables/09_validation_baseline_comparison.csv`
- `reports/tables/09_validation_confusion_counts.csv`
- `reports/tables/09_execution_times.csv`

Figures:

- `reports/figures/baseline_models/09_validation_confusion_matrices.png`
- `reports/figures/baseline_models/09_validation_roc_curves.png`
- `reports/figures/baseline_models/09_validation_precision_recall_curves.png`
- `reports/figures/baseline_models/09_validation_metric_comparison.png`

## Status

**DONE** — implementation, executed notebook, Validation-only comparison,
required figures and tables, documentation, 77-test regression suite, T00-T08
stage verification, and raw checksum verification all passed. Test remained
unevaluated, and work stopped after T09.
