import csv
import io
import json
from pathlib import Path
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout

from fuzzy_diabetes.cli import main
from fuzzy_diabetes.evaluation import (
    evaluate_rows,
    fit_medians,
    metrics,
    preprocess,
    read_dataset,
    split_indices,
)
from test_engine import BASE


class EvaluationTests(unittest.TestCase):
    def test_csv_rejects_duplicate_columns(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "input.csv"
            path.write_text(
                ",".join([*BASE, "Outcome", "Glucose"]) + "\n" + ",".join(["1"] * 10)
            )
            with self.assertRaises(ValueError):
                read_dataset(path)

    def test_confusion_matrix_metrics(self):
        result = metrics([(0, 0), (0, 1), (1, 0), (1, 1), (1, 1)], 6)
        self.assertEqual(
            result["confusion_matrix"], {"tn": 1, "fp": 1, "fn": 1, "tp": 2}
        )
        self.assertEqual(result["accuracy_on_scored"], 0.6)
        self.assertEqual(result["correct_over_attempted"], 0.5)
        self.assertEqual(result["abstained"], 1)

    def test_undefined_metrics_are_null_not_perfect(self):
        result = metrics([], 2)
        self.assertIsNone(result["accuracy_on_scored"])
        self.assertIsNone(result["recall"])
        self.assertEqual(result["coverage"], 0)

    def test_failed_rows_stay_in_denominator(self):
        rows = [
            {"features": BASE, "outcome": 1},
            {"features": {**BASE, "Glucose": 0}, "outcome": 0},
        ]
        result = evaluate_rows(rows, [0, 1])
        self.assertEqual(result["attempted"], 2)
        self.assertEqual(result["scored"], 1)
        self.assertEqual(result["failures"], {"missing_input": 1})

    def test_imputation_uses_training_partition_only(self):
        rows = [
            {"features": {**BASE, "Glucose": x}, "outcome": i % 2}
            for i, x in enumerate([80, 100, 200])
        ]
        medians = fit_medians(rows, [0, 1])
        self.assertEqual(medians["Glucose"], 90)
        rows[2]["features"]["Glucose"] = 1000
        self.assertEqual(fit_medians(rows, [0, 1]), medians)

    def test_imputation_preserves_zero_pregnancies_and_does_not_mutate(self):
        original = {**BASE, "Pregnancies": 0, "Insulin": 0}
        result = preprocess(original, {"Insulin": 200})
        self.assertEqual(result["Insulin"], 200)
        self.assertEqual(result["Pregnancies"], 0)
        self.assertEqual(original["Insulin"], 0)

    def test_imputation_cannot_invent_an_all_missing_training_column(self):
        with self.assertRaisesRegex(ValueError, "no nonzero values"):
            fit_medians([{"features": {**BASE, "Insulin": 0}, "outcome": 0}], [0])

    def test_versioned_report_denominators_are_consistent(self):
        report = json.loads(
            (Path(__file__).parents[1] / "reports/evaluation.json").read_text()
        )
        for name in [
            "holdout_imputed",
            "holdout_strict",
            "descriptive_full_data_legacy_zero_mode",
        ]:
            item = report[name]
            self.assertEqual(sum(item["confusion_matrix"].values()), item["scored"])
            self.assertEqual(item["scored"] + item["abstained"], item["attempted"])

    def test_stratified_split_is_repeatable_disjoint_and_exhaustive(self):
        rows = [{"outcome": i % 2} for i in range(20)]
        train, test = split_indices(rows)
        self.assertEqual((train, test), split_indices(rows))
        self.assertFalse(set(train) & set(test))
        self.assertEqual(set(train + test), set(range(20)))
        self.assertEqual(sum(rows[i]["outcome"] for i in test), 2)

    def test_split_rejects_insufficient_class_support(self):
        with self.assertRaises(ValueError):
            split_indices([{"outcome": 0}, {"outcome": 1}])

    def test_csv_rejects_schema_and_bad_values(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "input.csv"
            for text in [
                "Glucose,Outcome\n100,1",
                ",".join([*BASE, "Outcome"]) + "\n" + ",".join(["nan"] * 8 + ["1"]),
            ]:
                path.write_text(text)
                with self.assertRaises(ValueError):
                    read_dataset(path)

    def test_cli_returns_structured_failure(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "input.json"
            path.write_text(json.dumps({**BASE, "Insulin": 0}))
            stream = io.StringIO()
            with redirect_stderr(stream):
                self.assertEqual(main(["explain", str(path)]), 2)
            self.assertEqual(json.loads(stream.getvalue())["error"], "missing_input")

    def test_cli_success_returns_explanation(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "input.json"
            path.write_text(json.dumps(BASE))
            stream = io.StringIO()
            with redirect_stdout(stream):
                self.assertEqual(main(["explain", str(path)]), 0)
            self.assertEqual(json.loads(stream.getvalue())["score"], 0.5)
