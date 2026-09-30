# T09 Baseline Model Decisions

## Scope and evaluation boundary

T09 establishes four untuned reference classifiers using the default T08
engineered representation. Every estimator fits on the chronological Train
subset and is evaluated on Validation only. The Test subset remains reserved
for later final unbiased evaluation: T09 generates no Test predictions,
probabilities, metrics, figures, comparisons, or decisions.

No hyperparameter search, class resampling, result-based feature selection,
probability-threshold optimization, final-model selection, or T10+ work occurs
in this task.

## Algorithms and purposes

| Algorithm | Project-specific baseline purpose |
|---|---|
| Logistic Regression | Simple interpretable linear reference against which nonlinear models can be compared. |
| Decision Tree Classifier | Single-tree baseline able to represent nonlinear relations and feature interactions. |
| Random Forest Classifier | Bagging ensemble baseline that reduces single-tree instability and combines mixed engineered weather signals. |
| Gradient Boosting Classifier | Boosting ensemble baseline that sequentially improves weak learners and contrasts with Random Forest's bagging strategy. |

These roles justify inclusion; they do not imply that any algorithm is the
final project model.

## Exact baseline configurations

- `LogisticRegression(max_iter=1000, random_state=42)`
- `DecisionTreeClassifier(random_state=42)`
- `RandomForestClassifier(random_state=42, n_jobs=-1)`
- `GradientBoostingClassifier(random_state=42)`

All omitted parameters retain scikit-learn defaults. `random_state=42` is for
repeatability. `max_iter=1000` is a convergence safeguard, not a searched
value. `n_jobs=-1` changes execution parallelism, not the fitted statistical
model. No configuration was chosen by comparing alternative hyperparameters.

## Representation and scaling

All four models use the 89-column default T08 engineered schema. Logistic
Regression uses the existing scaled engineered preprocessing path because its
optimization and coefficient geometry are sensitive to numerical scale.
Decision Tree, Random Forest, and Gradient Boosting use the existing unscaled
engineered path because their split rules do not require standardization.

Scaling is not implemented inside an estimator. Both preprocessing variants
preserve the same feature names and use the established sequence:

`raw labelled data -> chronological split -> feature engineering -> fit preprocessing on Train -> transform Validation`

The established helper may also transform Test as part of the standard split
workflow, but no model-facing T09 function accepts Test arguments.

## Why chronological Validation is used

The existing whole-date split represents later observations than Train and is
the development evidence source for baseline comparison. Fitting on Train and
evaluating on later Validation provides a time-aware estimate without leaking
future preprocessing or labels into fitting. Test remains untouched by model
evaluation so it can support one final unbiased assessment after all later
development decisions are complete.

## Positive class and metrics

`RainTomorrow=Yes` is the positive class and `No` is the negative class. The
probability for `Yes` is located from each fitted estimator's `classes_`
attribute rather than assuming it is probability column 1.

Accuracy is insufficient by itself because only 20.3917% of Validation rows
are positive. The comparison therefore includes accuracy, balanced accuracy,
Yes-class precision, Yes-class recall, Yes-class F1, ROC-AUC, PR-AUC, and the
ordered confusion counts TN, FP, FN, TP. Balanced accuracy weights class
recalls equally; the Yes-class measures expose minority-class behavior;
ROC-AUC evaluates ranking across false-positive rates; and PR-AUC focuses on
the precision/recall trade-off for the minority positive class.

## Baseline-only interpretation rules

Metric leaders may be reported descriptively, but T09 does not call them
optimized or select a final model. Precision/recall differences are treated as
trade-offs, not causal effects. The observed results are limited to the fixed
default decision thresholds and this one chronological Validation period.

Resampling, class weighting, tuning, calibration, threshold choice, feature
alternatives, and final selection remain possible T10+ questions. They are not
performed or decided in T09.
