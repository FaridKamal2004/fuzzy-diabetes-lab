# Data and reproduction

The original code names the Kaggle dataset `akshaydattatraykhare/diabetes-dataset` and file `diabetes.csv`: [source page](https://www.kaggle.com/datasets/akshaydattatraykhare/diabetes-dataset). This repository does not redistribute the supplied CSV or claim a dataset redistribution license. Use a locally obtained copy under its applicable terms.

The user-supplied `Diabetes Dataset.csv` used for the aggregate evaluation has SHA-256:

```text
d765aa828a47e8d3ba2f4de925891be77803fd0e9568d7c213cdf10c8e83d0b2
```

It has 768 rows, eight input columns and the Outcome target. The source code and export identify it as the Pima diabetes benchmark. Raw records, row identifiers, student documents and per-record predictions are excluded from the public repo and site.

Observed zero counts: Glucose 5; BloodPressure 35; SkinThickness 227; Insulin 374; BMI 11; Pregnancies 111; DiabetesPedigreeFunction 0; Age 0. Pregnancies=0 is a permitted count and is not imputed. The five designated measurement columns use an explicit zero-as-missing policy. For context, see the original research discussion of [Pima zero-valued measurements](https://pmc.ncbi.nlm.nih.gov/articles/PMC11438170/); this implementation's policy is an analytical choice, not medical guidance.

Reproduce the aggregate report:

```sh
python -m pip install -e .
python -m fuzzy_diabetes evaluate "path/to/Diabetes Dataset.csv" --output reports/evaluation.json
python scripts/build_site.py
```

Seed 42 is used with Python's seeded class-wise shuffle. Each class's test count is `round(n*0.2)`, bounded so train and test both have support. The test-index-list SHA-256 is `c60f9373c51fcda8027751252e5e10bf15193f4f0f8bba400b0524e510f2bd68`. Median replacements from training rows are Glucose 116, BloodPressure 72, SkinThickness 29, Insulin 125, BMI 32. There is no outcome-specific imputation and no tuning against holdout labels.

CI does not download raw data. It verifies report arithmetic, shared assets, synthetic behavior and independent numerical correctness. Re-running the benchmark itself requires the local CSV. A different file checksum or preprocessing policy should produce a separately labeled report rather than silently replacing the published benchmark claim.
