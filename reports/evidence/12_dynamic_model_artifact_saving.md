# T12 Dynamic Model Selection and Artifact Saving Evidence

## Outcome

`notebooks/11_final_model_selection.ipynb` is the single end-to-end execution
point. Its saved run has eight executed code cells and zero error outputs. It
loads the four saved T11 Validation results, selects the winner
programmatically, fits all four frozen candidates on Train+Validation, routes
one winner to the official final path, routes three non-winners to comparison
paths, and evaluates only the selected final bundle on Test.

No model-building script was added.

## Dynamic selection

`select_and_freeze_final_configuration` validates exactly the four established
model families and rejects Test-labelled columns. It sorts by full-precision
Validation PR-AUC descending. The established model order is a deterministic
secondary key used only for an exact PR-AUC tie. Artifact roles and paths are
derived from the selected model family rather than from a hard-coded Random
Forest assignment.

| Rank | Model | Validation PR-AUC | Selected role |
|---:|---|---:|---|
| 1 | Random Forest | 0.7046788070582175 | final |
| 2 | Gradient Boosting | 0.6923304007737022 | comparison |
| 3 | Logistic Regression | 0.6785227087285604 | comparison |
| 4 | Decision Tree | 0.6352892997641237 | comparison |

The current evidence therefore selects Random Forest. A focused synthetic
test gives Logistic Regression the highest PR-AUC and verifies that Logistic
Regression is then routed to the final path while Random Forest is routed to
`models/comparison/random_forest.joblib`.

## Persisted models

| Model | Role | Representation | Scaling | Processed features | Artifact |
|---|---|---|---|---:|---|
| Random Forest | final | V0_DEFAULT | unscaled | 89 | `models/final_rainfall_model.joblib` |
| Logistic Regression | comparison | V2_LOG_RAINFALL_REPLACE | scaled | 89 | `models/comparison/logistic_regression.joblib` |
| Decision Tree | comparison | V0_DEFAULT | unscaled | 89 | `models/comparison/decision_tree.joblib` |
| Gradient Boosting | comparison | V1_ADD_YEAR | unscaled | 90 | `models/comparison/gradient_boosting.joblib` |

All four artifacts load as `FinalRainfallModelBundle` instances. Each contains
its own fitted estimator, fitted `FeatureVariantPreprocessor`, configuration,
ordered processed feature names, expected raw schema, positive class `Yes`,
threshold 0.5, development provenance, and artifact role. All four saved
label/probability round trips passed on a Train+Validation sample.

## Fitting population and Test isolation

Every persisted model fitted preprocessing and its estimator on exactly
120,888 rows: 99,546 Train plus 21,342 Validation, spanning 2007-11-01 through
2016-04-08. The development-fitting API does not accept a Test argument.

After all four models were fitted, only the bundle with role `final` was
passed to the Test-evaluation API. The API rejects a comparison bundle. The
three comparison artifacts have no Test row count and record false for Test
use and Test-content flags. The selected Random Forest alone evaluated the
21,305 Test rows.

## Regression results

- Final Random Forest Test metrics remain byte-identical, including PR-AUC
  0.7293491092285072 and ROC-AUC 0.8758649512620976.
- The notebook's internal SHA-256 assertions passed for the saved T09, T10,
  T11, and T12 metric outputs that it refreshes.
- Focused final-model and verifier tests: 30/30 passed.
- Full test suite: 130/130 passed in 5.674 seconds.
- T00-T08 stage verifier: passed.
- Raw `weatherAUS.csv` SHA-256:
  `573FD715CD69FCACC4DF32024D823B450AE3EDAAE7E8FF2EEB623ADBED424014`.

The official artifact was intentionally reserialized by the notebook to add
the dynamic artifact role and shared four-model persistence metadata. Its new
SHA-256 is
`E6EC23E86F7966FBFDEB5B247E314F37C31183BC55B4BDE2EE2E801C6F5526E2`;
the estimator configuration and final Test results did not change.

## Resolved execution notes

The installed Jupyter launcher did not expose the `jupyter-nbconvert`
subcommand, so execution used the installed module entry point
`python -m nbconvert`. The first module execution exposed one stale notebook
reference (`NameError: name 'prepared' is not defined`) in the figure cell.
That reference was replaced with the selected evaluation's aligned Test
target. The final complete run succeeded with no saved errors.
