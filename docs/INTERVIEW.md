# Interview walkthrough

## A truthful opening

“This began as university group coursework: a notebook-style diabetes fuzzy classifier with 40 handwritten rules. I enhanced its engineering into an installable Python package and interactive browser lab. I focused on traceable inference, explicit abstention, reproducible evaluation and tests, rather than claiming clinical readiness or artificially higher accuracy.”

The enhancement was developed with AI assistance. Read the source, run it yourself, credit the original group, and explain only what you understand.

## Three-minute demonstration

1. **Show a synthetic scenario.** Pick Middle and point out score 0.5, class 1 and Medium band. Explain why class and band are different labels and why the score is not a probability.
2. **Trace a rule.** R14 combines medium glucose and medium BMI. Each membership has a degree; AND takes the minimum. Multiple rules combine by maximum for each output term.
3. **Explain the plot.** Output sets are clipped by their activation, aggregated with maximum, and integrated to obtain the centroid. Change one input and inspect the new trace.
4. **Demonstrate failure behavior.** Load Missing value and Coverage gap. Both abstain explicitly instead of returning a deceptively confident result.
5. **Open Evaluation.** Compare 154/154 coverage under train-fitted imputation with 76/154 under strict handling. Discuss the majority baseline and why the old 72.66% full-data figure is not this holdout result.
6. **Show the tests and delivery.** The Python engine is checked against scikit-fuzzy. The JavaScript engine is checked against 120 synthetic Python fixtures. CI gates publication.

## Questions to practice

**Why rewrite the engine?** To separate inference from notebooks, network downloads, plots and evaluation, and to make its inputs, errors and outputs explicit. The core runs on the Python standard library and has no inference service to configure.

**How do you know the numerical code is correct?** Analytical centroid tests cover known low/high and symmetric shapes. Membership functions are compared against scikit-fuzzy. Full rule-system outputs are checked against an independent 10,001-point control system, within 1e-8. Separate parity cases enforce Python/JavaScript agreement within 1e-12.

**Why didn't you advertise 72.66%?** That was a full-data result from the source export. Evaluation design, missing-data policy, numerical ties and coverage differ. This version reports its own measured denominator, confusion counts and baseline.

**What is leakage here?** Fitting imputation on all records would let holdout data influence preprocessing. Medians use training rows only. However, the rules were already designed using the original dataset, so the split is not independent validation of rule design.

**Why abstain?** No rule support is different from a low output. Turning an inference failure into class 0 would hide incomplete coverage. Similarly, zero-coded missing measurements should not automatically activate low-value rules.

**What happens at 0.5?** A documented tolerance canonicalizes scores within 1e-12 to exactly 0.5, and the fixed >= threshold produces class 1. The original export had many near-ties and inconsistent results under that convention; the change is disclosed.

**What would be needed for medical use?** Substantially different work: independent clinical data, population suitability, calibration, subgroup and uncertainty studies, clinical review, and appropriate privacy/security/regulatory design. This project makes no diagnostic claim.

## Preparation

Practice changing one feature, tracing a rule by hand, explaining an abstention, interpreting the confusion matrix, and running the Python CLI offline. Have screenshots ready if the interview network is unavailable. Be clear about group provenance and AI assistance.
