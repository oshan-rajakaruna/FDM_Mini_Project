# T11 Controlled Feature / Representation Optimization Decisions

## Scope and purpose

T11 evaluates the two feature choices deferred by T08 before final model
selection: Year and a `log1p` replacement for Rainfall. It reuses the four
fixed T10-tuned model configurations. No model family or hyperparameter is
added, removed, or retuned.

Feature representations are selected independently for each model using
Train-only chronological cross-validation. Outer Validation is evaluated once
after selection. Test remains reserved for T12, which will handle final model
selection and the one-time holdout evaluation.

## Controlled feature variants

| Variant | Definition | Complete-Train processed features |
|---|---|---:|
| V0_DEFAULT | Existing T08 default | 89 |
| V1_ADD_YEAR | V0 plus numeric Year; cyclical Month retained | 90 |
| V2_LOG_RAINFALL_REPLACE | V0 with `Rainfall_log1p` replacing raw Rainfall | 89 |
| V3_YEAR_AND_LOG_RAINFALL | V1 plus the Rainfall replacement | 90 |

`Rainfall_log1p` replaces raw Rainfall in V2/V3 rather than duplicating a
strongly related measurement. This isolates the representational choice and
avoids needless collinearity. `RainToday` remains present.

Year is known on the observation date, but it can proxy temporal drift,
station coverage, or measurement practice. It therefore requires empirical
time-aware evaluation instead of automatic inclusion. Rainfall is highly
right-skewed, while `log1p` compresses its upper tail; whether this helps is
algorithm-dependent.

ClimateZone remains deferred. No authoritative Location-to-climate mapping
with documented provenance is present, so inventing one would introduce an
unsupported external assumption. No additional features were searched after
observing results: a null or negligible improvement is a valid outcome.

## Train-only chronological selection

T11 reuses T10's three expanding folds built over complete unique calendar
dates. All observations on a date remain together, every fold has zero row and
date overlap, and each fold satisfies
`max(fold Train date) < min(fold Validation date)`.

For every variant/fold representation:

`raw fold Train -> feature variant -> fit preprocessing on fold Train -> transform fold Train/Validation -> fit fixed T10 model -> score fold Validation`

Fold matrices can be reused by fixed models with the same scaling route only
after fold-local preprocessing. Numerical medians, Location medians, global
fallbacks, category vocabularies, and scaling parameters never use fold
Validation. Logistic Regression uses scaled matrices; Decision Tree, Random
Forest, and Gradient Boosting use unscaled matrices.

Average Precision (`PR-AUC`) is the sole performance criterion for selecting a
representation. Exact mean PR-AUC ties use the fixed V0, V1, V2, V3 order only.
ROC-AUC, balanced accuracy, precision, recall, and F1 are interpretive and do
not influence selection. Outer Validation is absent from the selection API.

## Fixed experiment size and parameters

The controlled experiment contains 4 models x 4 variants x 3 folds = 48 model
fits. Logistic Regression keeps `C=0.1`; Decision Tree keeps its balanced,
depth-10 configuration; Random Forest keeps 150 depth-20 trees; and Gradient
Boosting keeps 100 depth-3 estimators with learning rate 0.1 and subsample 0.8.
The complete parameter record is saved in
`reports/tables/11_fixed_model_configurations.csv`.

## Train-CV decisions

| Model | Selected variant | Mean CV PR-AUC | Std | Change from V0 |
|---|---|---:|---:|---:|
| Logistic Regression | V2_LOG_RAINFALL_REPLACE | 0.708542 | 0.004509 | +0.001510 |
| Decision Tree | V0_DEFAULT | 0.640795 | 0.015415 | 0.000000 |
| Random Forest | V0_DEFAULT | 0.722824 | 0.008788 | 0.000000 |
| Gradient Boosting | V1_ADD_YEAR | 0.721401 | 0.002877 | +0.000224 |

No tie-break was required. Year reduced CV PR-AUC for Logistic Regression,
Decision Tree, and Random Forest. The log replacement produced a small gain
for Logistic Regression, essentially no change for the two tree ensembles,
and no benefit for Gradient Boosting. Year's Gradient Boosting gain was very
small and nearly identical to V3.

## Validation interpretation and boundary

The Logistic Regression log replacement increased Validation PR-AUC by
0.001339 and ROC-AUC by 0.000819 relative to T10, while its default-threshold
accuracy, balanced accuracy, precision, recall, and F1 declined slightly.
Decision Tree and Random Forest selected V0 and therefore reproduce T10.
Gradient Boosting's Year variant showed tiny default-threshold gains but its
Validation PR-AUC declined by 0.000210. These mixed, small changes are
descriptive and not evidence of material superiority or statistical
significance.

No classification threshold was optimized. No resampling, post-result feature
search, final-model selection, or Test evaluation occurred. T12 must consider
the completed T09-T11 development evidence, select a final approach without
using Test feedback, and only then perform the reserved one-time Test
evaluation.

## Limitations

Only three temporal folds and two pre-declared feature choices were evaluated.
Temporal drift can make Year unstable outside the observed period. A monotonic
Rainfall transform may alter linear behavior while being nearly irrelevant to
tree splits. Small CV or Validation differences may reflect sampling or
implementation-level numerical variation and should not be overinterpreted.
