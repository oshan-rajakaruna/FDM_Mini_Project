# T12 Final Model Selection and Holdout Evaluation Evidence

## 1. Objective

T12 completes Progress Evaluation 2 modeling by selecting one final model from
pre-Test development evidence, freezing it, refitting on Train+Validation,
evaluating the untouched chronological Test set once, and persisting the
deployable fitted pipeline.

## 2. Pre-Test selection policy

The deterministic primary rule was highest full-precision T11 Validation
PR-AUC. The fixed model order Logistic Regression, Decision Tree, Random
Forest, Gradient Boosting was reserved only for an exact tie. No tie occurred.
All other metrics were interpretive and Test was prohibited from selection.

## 3. Pre-Test candidates

| Rank | Candidate | T11 representation | Validation PR-AUC |
|---:|---|---|---:|
| 1 | Random Forest | V0_DEFAULT | 0.704679 |
| 2 | Gradient Boosting | V1_ADD_YEAR | 0.692330 |
| 3 | Logistic Regression | V2_LOG_RAINFALL_REPLACE | 0.678523 |
| 4 | Decision Tree | V0_DEFAULT | 0.635289 |

The complete seven-metric evidence and confusion counts are in
`reports/tables/12_pretest_candidate_selection.csv`.

## 4. Selected final model

Random Forest with V0_DEFAULT was derived programmatically from the saved T11
table before the raw split was loaded in the T12 notebook.

## 5. Frozen configuration

- Model: Random Forest, `random_state=42`.
- T10 parameters: 150 estimators, depth 20, minimum split 2, minimum leaf 1,
  square-root feature sampling, no class weighting.
- Representation: V0_DEFAULT.
- Preprocessing route: unscaled.
- Positive/negative classes: Yes/No.
- Threshold: 0.5, not optimized.
- Test consulted during selection: No.
- Execution-only portability setting: `n_jobs=1`.

The machine-readable record is
`reports/tables/12_final_frozen_configuration.csv`.

## 6. Train+Validation refit

Only after configuration freeze, Train and Validation were combined:

| Population | Rows | Date range |
|---|---:|---|
| Train | 99,546 | 2007-11-01 to 2015-01-12 |
| Validation | 21,342 | 2015-01-13 to 2016-04-08 |
| Final development | 120,888 | 2007-11-01 to 2016-04-08 |
| Test | 21,305 | 2016-04-09 to 2017-06-25 |

V0 feature engineering was applied independently to final development and
Test. Every final median, Location fallback, encoder vocabulary, and other
preprocessing state was fitted on final development only. Test was
transform-only and was excluded from estimator fitting.

## 7. Final processed feature count

Final development and Test both had the same ordered 89-feature schema with no
missing or non-finite values.

## 8. Final Test metrics

| Metric | Value |
|---|---:|
| Accuracy | 0.844215 |
| Balanced Accuracy | 0.724577 |
| Precision Yes | 0.766068 |
| Recall Yes | 0.496447 |
| F1 Yes | 0.602467 |
| ROC-AUC | 0.875865 |
| PR-AUC | 0.729349 |

RainTomorrow=Yes was located safely through `model.classes_`. Predicted labels
used the frozen 0.5 probability threshold.

## 9. Test confusion matrix

| TN | FP | FN | TP | Total |
|---:|---:|---:|---:|---:|
| 15,471 | 768 | 2,551 | 2,515 | 21,305 |

The matrix reconciles to 16,239 Test No and 5,066 Test Yes observations.

## 10. Validation versus Test

| Metric | T11 Validation | Final Test | Test minus Validation |
|---|---:|---:|---:|
| Accuracy | 0.859385 | 0.844215 | -0.015170 |
| Balanced Accuracy | 0.700083 | 0.724577 | +0.024494 |
| Precision Yes | 0.781341 | 0.766068 | -0.015273 |
| Recall Yes | 0.431066 | 0.496447 | +0.065381 |
| F1 Yes | 0.555605 | 0.602467 | +0.046862 |
| ROC-AUC | 0.883234 | 0.875865 | -0.007369 |
| PR-AUC | 0.704679 | 0.729349 | +0.024670 |

## 11. Interpretation

Discrimination remained reasonably consistent in the later chronological
period. PR-AUC, balanced accuracy, recall, and F1 improved; accuracy,
precision, and ROC-AUC declined modestly. This mixed pattern does not justify
changing the frozen model.

Test Yes prevalence was 23.7785%, versus 20.3917% in Validation. Despite that
increase, No remains the majority class. The final model was relatively
precise when predicting Yes but detected only 49.64% of actual Yes cases. Its
2,551 false negatives exceeded its 768 false positives, an important
decision-support limitation at the fixed threshold.

## 12. Generalization discussion

The holdout follows development chronologically, so the results provide useful
evidence about a later historical period. They do not prove stability under
future climate, station, data-quality, or operational changes. Only one
dataset and one final holdout were used. No causal or statistical-significance
claim is made. Test must remain final evidence rather than an optimization
signal.

## 13. Artifact and serialization verification

The compressed 46,192,170-byte artifact is
`models/final_rainfall_model.joblib`. It contains the fitted Random Forest,
fitted preprocessing state, V0 identifier, ordered 89-feature schema, expected
raw schema, class/threshold definitions, exact parameters, and provenance
metadata. It contains no Test labels or raw dataset.

- Loaded bundle type verified: Yes.
- Loaded predicted labels match in-memory labels: Yes.
- Loaded positive probabilities match within tolerance: Yes.

## 14. Test-isolation chronology

1. Saved T11 Validation evidence was loaded.
2. Candidate ranking selected Random Forest solely by full-precision
   Validation PR-AUC.
3. Configuration CSV was written and frozen.
4. Only then was the raw chronological split loaded.
5. Train and Validation were combined.
6. Preprocessing was fitted on Train+Validation and Test was transformed.
7. Exactly one selected estimator was fitted and evaluated on Test.
8. Serialization used a small inference sample only for integrity checking.

No alternative model was fitted on, predicted on, or compared using Test.

## 15. No-post-Test-change statement

No model, feature representation, hyperparameter, preprocessing policy,
resampling policy, or threshold changed after Test evaluation. Test metrics did
not trigger another search.

## 16. Tests and checks

- Focused T12 tests: 22/22 passed.
- Full regression suite: 123/123 passed.
- Narrow T12 model-artifact verifier allowance regression: passed.
- T00-T08 verifier: all nine stages passed.
- Notebook: 8/8 code cells executed, zero saved errors, four inline PNGs.
- Model artifact load and inference round trip: passed.
- T09/T10/T11 preservation assertions: passed.
- Raw checksum: passed.

## 17. Artifacts

Implementation and documentation:

- `src/fdm_rainfall/final_model.py`
- `tests/test_final_model.py`
- `tests/test_stage_verifier.py`
- `scripts/verify_stage1.py`
- `notebooks/11_final_model_selection.ipynb`
- `docs/decisions/final_model_selection.md`
- `reports/evidence/12_final_model_selection.md`
- `models/final_rainfall_model.joblib`

Tables:

- `12_pretest_candidate_selection.csv`
- `12_final_frozen_configuration.csv`
- `12_final_test_metrics.csv`
- `12_final_test_confusion_counts.csv`
- `12_validation_vs_test_metrics.csv`
- `12_final_artifact_metadata.csv`

Figures:

- `12_final_test_confusion_matrix.png`
- `12_final_test_roc_curve.png`
- `12_final_test_precision_recall_curve.png`
- `12_validation_vs_test_metrics.png`

## 18. PE2 completion

T12 is complete. The final model was selected before Test, frozen, refitted on
Train+Validation, evaluated once on Test, serialized, and verified without any
post-Test optimization. Progress Evaluation 2 modeling and optimization
implementation is complete. Backend and frontend work have not started.
