# T10 Hyperparameter Tuning Decisions

## Scope

T10 tunes only the four T09 model families: Logistic Regression, Decision Tree,
Random Forest, and Gradient Boosting. Hyperparameters are selected with
Train-only chronological cross-validation. The selected configuration for each
family is refitted on complete Train and evaluated once on Validation.

Test is not predicted, scored, plotted, compared, or used for selection. T10
does not perform resampling, feature selection, calibration, probability-
threshold optimization, final-model selection, or T11+ work.

## Why tuning follows the baselines

T09 established essentially-default reference behavior. T10 checks whether a
small, interpretable set of complexity, regularization, class-weighting, and
ensemble controls improves each family under later-in-time Train-period data.
The goal is development evidence, not an optimized final project model.

## Date-aware expanding-window CV

The 2,541 unique dates inside the 99,546-row Train period are sorted and passed
to `TimeSeriesSplit(n_splits=3)`. Date positions, rather than raw row
positions, define the expanding windows. Each selected date block is then
mapped back to every location row for those dates. This prevents a calendar
date shared by multiple locations from crossing a fold boundary.

| Fold | Fold Train dates | Fold Validation dates | Train rows | Validation rows |
|---:|---|---|---:|---:|
| 1 | 2007-11-01 to 2009-07-28 | 2009-07-29 to 2011-05-24 | 11,819 | 28,665 |
| 2 | 2007-11-01 to 2011-05-24 | 2011-05-25 to 2013-04-17 | 40,484 | 28,720 |
| 3 | 2007-11-01 to 2013-04-17 | 2013-04-18 to 2015-01-12 | 69,204 | 30,342 |

All folds have zero shared rows, zero shared dates, and strict chronology:
`max(fold Train date) < min(fold Validation date)`. Shuffled K-fold and
StratifiedKFold are inappropriate because they can train on later weather while
scoring earlier observations.

## Fold-local preprocessing

Each fold follows:

`raw fold Train -> default T08 feature engineering -> fit preprocessing on fold Train -> transform fold Train/Validation -> fit candidate -> score fold Validation`

`WeatherFeatureEngineer(output="default")` preserves the T08 schema and is
target-independent. Every `RainfallPreprocessor` learns imputation medians,
categorical vocabulary, and scaling statistics only from its fold Train rows.
Fold-specific matrices are cached and safely reused across candidates because
preprocessing does not depend on model hyperparameters. No preprocessor is
fitted once on the complete Train period before cross-validation.

Logistic Regression uses scaled fold matrices. Decision Tree, Random Forest,
and Gradient Boosting use unscaled fold matrices.

## Primary objective

Average Precision (`PR-AUC`) is the sole candidate-selection metric. The
positive class, `RainTomorrow=Yes`, is moderately imbalanced and operationally
important, so ordinary accuracy is not an adequate optimization objective.
CV ROC-AUC, Yes-class F1, Yes-class recall, and balanced accuracy are retained
for interpretation but do not determine the selected candidate. An exact tie
in mean CV PR-AUC is resolved by original candidate number only, as a neutral
deterministic tie-break rather than another performance criterion. None of the
four selected configurations required this tie-break.

## Search implementation

A custom deterministic candidate loop is used instead of passing a
complete-Train preprocessed matrix into `GridSearchCV` or
`RandomizedSearchCV`. This makes the fold-local preprocessing boundary explicit
and auditable. The compact Logistic Regression space is exhaustively searched;
larger spaces use bounded sampling through `ParameterSampler(random_state=42)`.

| Model | Search | Candidates | Folds | Fits |
|---|---|---:|---:|---:|
| Logistic Regression | Exhaustive grid | 8 | 3 | 24 |
| Decision Tree | Deterministic randomized | 12 | 3 | 36 |
| Random Forest | Deterministic randomized | 8 | 3 | 24 |
| Gradient Boosting | Deterministic randomized | 6 | 3 | 18 |

Total: 34 candidates and 102 Train-CV model fits.

## Search spaces and rationale

### Logistic Regression

- `C`: 0.01, 0.1, 1.0, 10.0
- `class_weight`: `None`, `"balanced"`

This tests regularization strength and a direct class-imbalance adjustment
while retaining the existing compatible default solver and `max_iter=1000`.

### Decision Tree

- `criterion`: `gini`, `entropy`
- `max_depth`: `None`, 5, 10, 20
- `min_samples_split`: 2, 20, 50
- `min_samples_leaf`: 1, 5, 20
- `class_weight`: `None`, `"balanced"`

These parameters control split criterion, tree depth, leaf support, and class
weighting. Twelve candidates are sampled from the 144-combination space.

### Random Forest

- `n_estimators`: 100, 150
- `max_depth`: `None`, 10, 20
- `min_samples_split`: 2, 20
- `min_samples_leaf`: 1, 5
- `max_features`: `"sqrt"`, 0.5
- `class_weight`: `None`, `"balanced"`

These cover ensemble size, tree complexity, feature subsampling, and class
weighting. Eight candidates are sampled from the 96-combination space.

### Gradient Boosting

- `n_estimators`: 50, 100
- `learning_rate`: 0.03, 0.05, 0.1
- `max_depth`: 2, 3
- `min_samples_split`: 2, 20
- `min_samples_leaf`: 1, 5
- `subsample`: 0.8, 1.0

These control the learning-rate/estimator trade-off, weak-tree complexity, leaf
support, and stochastic subsampling. Six candidates are sampled from the
192-combination space because Gradient Boosting is the dominant runtime cost.

## Validation and Test boundary

After Train-CV selection, fresh scaled and unscaled preprocessors are fitted on
the complete 99,546-row Train set. Each selected estimator is fitted on Train
and evaluated once on the 21,342-row Validation set at its default threshold.
The existing Test period remains reserved for later final evaluation.

Threshold optimization is deferred because it requires an explicit operating-
cost policy and must not be mixed into hyperparameter selection. No final model
is selected in T10; baseline-versus-tuned differences are descriptive.

## Limitations

The bounded searches do not exhaust every plausible setting. Three temporal
folds offer a practical robustness check but do not eliminate distribution
shift or establish statistical significance. Large performance changes can be
specific to the selected search space and Validation period. Later work must
keep Test isolated until development choices are complete.
