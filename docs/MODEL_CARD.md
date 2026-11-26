# Model card

## Intended use

An educational, explainable AI portfolio project. Intended users are students, developers and interviewers inspecting fuzzy inference, missing-data handling and evaluation methodology. Browser examples are synthetic. It must not be used to diagnose, screen, triage, recommend treatment, or make individual health decisions.

## Model and outputs

- Eight scalar inputs and 40 manually authored AND rules retained from the supplied project.
- Triangular/trapezoidal membership functions, minimum AND, maximum accumulation, minimum output clipping, and centroid defuzzification.
- Exact piecewise-linear envelope integration includes term intersections. This can differ slightly from the original coarse 0.01 output grid. A dense independent scikit-fuzzy control system checks scores within 1e-8.
- Model score is in [0,1], but is not a probability, confidence or clinical risk estimate.
- Demonstration class is 1 for score >=0.5 and 0 otherwise. Scores within 1e-12 of 0.5 are set to exactly 0.5 before classification, to avoid platform-dependent tie flips.
- Display bands are Low below 0.4, Medium from 0.4 to below 0.6, and High at or above 0.6. They are descriptive output bands, independent of the binary threshold, not medically defined categories.

## Input contract

| Input | Model range | Unit | Zero policy |
| --- | --- | --- | --- |
| Pregnancies | 0–17, integer | count | Zero is allowed |
| Glucose | 0–210 | mg/dL | Zero treated as missing |
| BloodPressure | 0–140 | diastolic mm Hg | Zero treated as missing |
| SkinThickness | 0–110 | mm | Zero treated as missing |
| Insulin | 0–900 | µU/mL | Zero treated as missing |
| BMI | 0–75 | kg/m² | Zero treated as missing |
| DiabetesPedigreeFunction | 0–2.6 | source dataset index | Zero allowed by model range |
| Age | 20–100, integer | years | Zero outside model range |

These are computational bounds copied/extended to include the declared endpoints of the original universes. They are not normal ranges or diagnostic cutoffs. Nonfinite values, bools, strings, missing features, extra features and out-of-range numbers fail explicitly. No automatic clipping is performed. Some membership shapes fall to zero at their upper endpoint; even valid model-range inputs can be uncovered.

## Missing values and abstention

The explorer and default Python inference reject zero values in the five flagged measurement columns. Invalid inputs and no-rule-coverage scenarios yield an explicit error with no score or threshold class. There is no silent low-risk fallback.

The benchmark's imputation policy replaces these zeros with medians fitted using training rows only. A completely missing training column fails rather than inventing a median. The separate legacy-zero evaluation treats zero as an ordinary input only for comparison with the source approach; it is not the explorer default.

## Evaluation and data limitations

The local benchmark contains 768 rows with 500 Outcome=0 and 268 Outcome=1 labels. Source metadata describes a restricted Pima diabetes benchmark cohort, not a representative general population. This project does not establish validity across demographic groups, measurement settings, pregnancy status, or contemporary clinical practice.

The deterministic split has 614 training and 154 holdout rows (100 class 0, 54 class 1). No learned classifier is fitted. Only imputation uses the training partition. Rules were originally authored with access to this dataset, so this is a reproducible partitioned benchmark, not pristine external validation.

| Imputed holdout metric | Value |
| --- | --- |
| Accuracy | 104/154 = 67.53% |
| Precision | 52.86% |
| Recall | 68.52% |
| Specificity | 67.00% |
| F1 | 0.597 |
| Coverage | 154/154 = 100% |
| Confusion counts | TN 67, FP 33, FN 17, TP 37 |

Strict missing-data handling scores 76/154, abstains on 78, and has 68.42% accuracy on the scored subset. The majority baseline reaches 64.94% accuracy on all holdout rows. Point estimates do not establish statistical superiority; no intervals, calibration study, subgroup evaluation or clinical validation are provided.

## Historical result audit

The source report's 72.66% is backed by 558 correct labels in its supplied full-data export. It is not a holdout metric. There are 147 near-threshold scores; 115 exported labels differ under the documented new tie convention. Separately, the stateless exact engine abstains on four full-data scenarios in legacy zero mode. Original exported labels and new results are therefore not claimed to be interchangeable.

## Privacy and deployment

Raw benchmark files and per-row results are not published. The site loads only model parameters and aggregate evaluation JSON, then computes locally in JavaScript. It does not retain input values in cookies, localStorage, URLs or analytics, and does not call a model API. The hosting provider still receives ordinary asset requests; following a GitHub link leaves the site. Use synthetic values.

## Changes needed for any real deployment

Independent datasets, clinical review, calibrated endpoints, representative cohorts, subgroup assessment, uncertainty analysis, robust missing-data studies, appropriate privacy/security controls and regulatory analysis would be separate work. Better software engineering alone does not validate a medical model.
