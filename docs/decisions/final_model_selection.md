# T12 Final Model Selection Decision

## Decision boundary

T12 selects one final model before accessing Test, freezes its complete
configuration, refits it on Train plus Validation, and performs the reserved
one-time Test evaluation. Test is final evidence and cannot reopen model,
feature, hyperparameter, preprocessing, resampling, or threshold decisions.

## Evidence available before Test

The only candidates were the four T11-selected model/representation pairs.
Their full-precision saved Validation results were loaded from
`reports/tables/11_validation_metrics.csv` and checked against the T11
representation-winner record.

| Validation rank | Model | T11 representation | PR-AUC |
|---:|---|---|---:|
| 1 | Random Forest | V0_DEFAULT | 0.704679 |
| 2 | Gradient Boosting | V1_ADD_YEAR | 0.692330 |
| 3 | Logistic Regression | V2_LOG_RAINFALL_REPLACE | 0.678523 |
| 4 | Decision Tree | V0_DEFAULT | 0.635289 |

## Predeclared selection rule

Candidates are ranked by full-precision T11 Validation PR-AUC descending.
An exact tie would use the neutral fixed order Logistic Regression, Decision
Tree, Random Forest, then Gradient Boosting. Test is forbidden as a tie-break.
Accuracy, balanced accuracy, precision, recall, F1, ROC-AUC, confusion behavior,
CV stability, runtime, and complexity are interpretive only and cannot
override PR-AUC.

PR-AUC is primary because RainTomorrow=Yes is the minority outcome and the
project needs a threshold-independent measure focused on ranking positive
rainfall cases. No weighted score was constructed. No exact tie occurred.

## Frozen final configuration

The rule selected **Random Forest with V0_DEFAULT** before Test access.

- Hyperparameters: `n_estimators=150`, `max_depth=20`,
  `min_samples_split=2`, `min_samples_leaf=1`, `max_features=sqrt`,
  `class_weight=None`.
- Random state: 42.
- Representation: T08/T11 V0 default engineered representation.
- Preprocessing: unscaled, with medians, Location fallbacks, category
  vocabulary, and feature order learned from final development data only.
- Positive class: RainTomorrow=Yes.
- Classification threshold: unchanged default 0.5.
- Execution-only setting: `n_jobs=1` for portable fitting/serialization; this
  is not a tuned model hyperparameter.

Gradient Boosting, Logistic Regression, and Decision Tree were not selected
because their full-precision Validation PR-AUC values were lower. Their other
metrics did not override the declared primary rule. Test was not consulted.

The frozen record was written to
`reports/tables/12_final_frozen_configuration.csv` before raw split loading or
Test prediction.

## Final refit and Test policy

After freezing, the 99,546 Train rows and 21,342 Validation rows were combined
into 120,888 final development rows spanning 2007-11-01 through 2016-04-08.
Feature engineering and preprocessing were fitted afresh on this combined
population. Test remained transform-only and contained 21,305 rows spanning
2016-04-09 through 2017-06-25.

Exactly one Random Forest was fitted on the processed final development set
and evaluated on Test. No alternative candidate received Test predictors or
labels. The Test result did not cause a model, feature, parameter, or threshold
change.

## Final evidence interpretation

Compared with the selection-stage Validation result, Test PR-AUC increased by
0.024670 and ROC-AUC declined by 0.007369. Recall increased by 0.065381 and F1
by 0.046862, while precision declined by 0.015273 and accuracy by 0.015170.
This is reasonably consistent generalization to the later chronological
period, with a different threshold trade-off rather than uniform improvement.

Test prevalence was 23.7785% Yes, compared with 20.3917% in Validation. The
class remains imbalanced. At threshold 0.5 the model produced 768 false
positives and 2,551 false negatives; the relatively high false-negative count
shows that missed rainy days remain an important limitation.

## Persisted artifact

`models/final_rainfall_model.joblib` contains the fitted estimator,
Train+Validation-fitted preprocessor, representation identifier, ordered
processed schema, expected raw schema, class/threshold definitions, exact
tuned hyperparameters, date/row provenance, and version metadata. It does not
contain Test labels or raw datasets. Loaded labels matched exactly and loaded
probabilities matched within floating-point tolerance.

## Limitations and no-post-Test-change statement

The result comes from one historical Australian weather dataset and one later
chronological holdout. Location coverage, measurement practices, climate, and
weather relationships may drift. The comparison is descriptive; no causal or
statistical-significance claim is made. A future monitoring or retraining
process would require a separately governed evaluation design. The present
Test result must not trigger another search on this holdout.

No post-Test model, representation, hyperparameter, preprocessing, resampling,
or threshold change was made.
