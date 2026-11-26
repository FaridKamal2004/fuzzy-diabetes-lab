"""Reproducible benchmark evaluation; never silently discards failed records."""

from collections import Counter
import csv
import hashlib
import json
import math
from pathlib import Path
import random
import statistics

from .engine import InferenceError, infer, load_model, validate


def read_dataset(path):
    config = load_model()
    with Path(path).open(encoding="utf-8-sig", newline="") as stream:
        reader = csv.DictReader(stream)
        fields = list(config["features"])
        if (
            reader.fieldnames is None
            or len(reader.fieldnames) != len(fields) + 1
            or set(reader.fieldnames) != set(fields + ["Outcome"])
        ):
            raise ValueError(
                "Expected exactly the eight model features and Outcome columns."
            )
        rows = []
        for line, raw in enumerate(reader, 2):
            try:
                values = {key: float(raw[key]) for key in fields}
                outcome = float(raw["Outcome"])
                if outcome not in (0, 1) or any(
                    not math.isfinite(v) for v in values.values()
                ):
                    raise ValueError(
                        "Values must be finite and Outcome must be 0 or 1."
                    )
                validate(values, config, allow_zero=True)
                rows.append({"features": values, "outcome": int(outcome)})
            except (ValueError, TypeError, KeyError) as error:
                raise ValueError(f"Invalid CSV row {line}: {error}") from error
    if not rows:
        raise ValueError("The dataset is empty.")
    return rows


def split_indices(rows, seed=42, test_fraction=0.2):
    if not 0 < test_fraction < 1:
        raise ValueError("Test fraction must be between 0 and 1.")
    rng = random.Random(seed)
    train, test = [], []
    for label in (0, 1):
        group = [i for i, row in enumerate(rows) if row["outcome"] == label]
        if len(group) < 2:
            raise ValueError(
                "Each class needs at least two records for a stratified split."
            )
        rng.shuffle(group)
        count = min(len(group) - 1, max(1, round(len(group) * test_fraction)))
        test.extend(group[:count])
        train.extend(group[count:])
    return sorted(train), sorted(test)


def fit_medians(rows, indices):
    model = load_model()
    medians = {}
    for key, spec in model["features"].items():
        if spec["zero_missing"]:
            observed = [
                rows[i]["features"][key]
                for i in indices
                if rows[i]["features"][key] != 0
            ]
            if not observed:
                raise ValueError(
                    f"Cannot fit {key} median: no nonzero values in the training partition."
                )
            medians[key] = statistics.median(observed)
    return medians


def preprocess(features, medians):
    return {
        key: medians[key] if value == 0 and key in medians else value
        for key, value in features.items()
    }


def metrics(pairs, attempted):
    if not attempted:
        raise ValueError("Evaluation needs at least one attempted record.")
    tn = sum(y == 0 and p == 0 for y, p in pairs)
    fp = sum(y == 0 and p == 1 for y, p in pairs)
    fn = sum(y == 1 and p == 0 for y, p in pairs)
    tp = sum(y == 1 and p == 1 for y, p in pairs)
    ratio = lambda a, b: a / b if b else None
    return {
        "attempted": attempted,
        "scored": len(pairs),
        "abstained": attempted - len(pairs),
        "coverage": len(pairs) / attempted,
        "accuracy_on_scored": ratio(tn + tp, len(pairs)),
        "correct_over_attempted": (tn + tp) / attempted,
        "precision": ratio(tp, tp + fp),
        "recall": ratio(tp, tp + fn),
        "specificity": ratio(tn, tn + fp),
        "f1": ratio(2 * tp, 2 * tp + fp + fn),
        "confusion_matrix": {"tn": tn, "fp": fp, "fn": fn, "tp": tp},
    }


def evaluate_rows(rows, indices, *, medians=None, allow_zero=False):
    pairs, failures = [], Counter()
    for i in indices:
        row = rows[i]
        try:
            result = infer(
                preprocess(row["features"], medians or {}), allow_zero=allow_zero
            )
            pairs.append((row["outcome"], result["model_class"]))
        except InferenceError as error:
            failures[error.code] += 1
    return {**metrics(pairs, len(indices)), "failures": dict(failures)}


def evaluate_dataset(path):
    rows = read_dataset(path)
    train, test = split_indices(rows)
    medians = fit_medians(rows, train)
    majority = int(sum(rows[i]["outcome"] for i in train) > len(train) / 2)
    config = load_model()
    return {
        "schema_version": 1,
        "model_version": config["version"],
        "dataset_sha256": hashlib.sha256(Path(path).read_bytes()).hexdigest(),
        "rows": len(rows),
        "class_counts": dict(Counter(str(r["outcome"]) for r in rows)),
        "zero_counts": {
            key: sum(row["features"][key] == 0 for row in rows)
            for key in config["features"]
        },
        "split": {
            "method": "seeded stratified split; class-wise shuffle; round(n*0.2)",
            "seed": 42,
            "train": len(train),
            "test": len(test),
            "test_index_sha256": hashlib.sha256(json.dumps(test).encode()).hexdigest(),
        },
        "train_fitted_medians": medians,
        "holdout_imputed": evaluate_rows(rows, test, medians=medians),
        "holdout_strict": evaluate_rows(rows, test),
        "holdout_majority_baseline": metrics(
            [(rows[i]["outcome"], majority) for i in test], len(test)
        ),
        "descriptive_full_data_legacy_zero_mode": evaluate_rows(
            rows, list(range(len(rows))), allow_zero=True
        ),
        "limitations": [
            "Educational rule system, not a diagnosis or calibrated probability.",
            "Rules were authored using the original project and dataset; this holdout is not untouched independent or clinical validation.",
            "Only imputation medians are fitted on the training partition; rules and threshold are fixed.",
            "Scores within 1e-12 of 0.5 use an explicit positive-class tie convention.",
            "Raw dataset and row-level predictions are not published in the website.",
        ],
    }
