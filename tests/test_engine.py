import copy
import math
import unittest
from fuzzy_diabetes.engine import (
    InferenceError,
    aggregate_output,
    centroid,
    infer,
    load_model,
    membership,
)

BASE = {
    "Pregnancies": 4,
    "Glucose": 125,
    "BloodPressure": 75,
    "SkinThickness": 30,
    "Insulin": 200,
    "BMI": 27,
    "DiabetesPedigreeFunction": 0.8,
    "Age": 50,
}


class EngineTests(unittest.TestCase):
    def test_shared_model_retains_forty_rules(self):
        model = load_model()
        self.assertEqual(len(model["rules"]), 40)
        self.assertEqual(len(model["features"]), 8)
        self.assertEqual(len({r["id"] for r in model["rules"]}), 40)

    def test_loading_does_not_expose_shared_mutable_state(self):
        model = load_model()
        model["rules"].clear()
        self.assertEqual(len(load_model()["rules"]), 40)

    def test_triangular_membership(self):
        self.assertEqual(
            [membership(x, [0, 2, 4]) for x in [-1, 0, 1, 2, 3, 4, 5]],
            [0, 0, 0.5, 1, 0.5, 0, 0],
        )

    def test_vertical_shoulder_endpoints(self):
        self.assertEqual(membership(0, [0, 0, 2, 4]), 1)
        self.assertEqual(membership(4, [0, 2, 4, 4]), 1)
        self.assertEqual(membership(4.01, [0, 2, 4, 4]), 0)

    def test_known_low_output_centroid(self):
        self.assertAlmostEqual(
            centroid(
                aggregate_output(
                    {"Low": 1, "Medium": 0, "High": 0}, load_model()["output"]
                )
            ),
            7 / 45,
            places=12,
        )

    def test_known_high_output_centroid(self):
        self.assertAlmostEqual(
            centroid(
                aggregate_output(
                    {"Low": 0, "Medium": 0, "High": 1}, load_model()["output"]
                )
            ),
            38 / 45,
            places=12,
        )

    def test_symmetric_output_centroid_is_half(self):
        self.assertAlmostEqual(
            centroid(
                aggregate_output(
                    {"Low": 0.6, "Medium": 0.8, "High": 0.6}, load_model()["output"]
                )
            ),
            0.5,
            places=12,
        )

    def test_rule_activation_and_envelope_are_explained(self):
        result = infer(BASE)
        self.assertEqual(result["score"], 0.5)
        self.assertEqual(result["model_class"], 1)
        self.assertEqual(result["band"], "Medium")
        self.assertTrue(
            any(
                rule["id"] == "R14" and rule["strength"] == 1
                for rule in result["activations"]
            )
        )
        self.assertGreater(len(result["envelope"]), 4)

    def test_missing_value_abstains(self):
        for key in ["Glucose", "BloodPressure", "SkinThickness", "Insulin", "BMI"]:
            with self.subTest(key=key), self.assertRaises(InferenceError) as error:
                infer({**BASE, key: 0})
            self.assertEqual(error.exception.code, "missing_input")

    def test_legacy_zero_mode_is_explicit(self):
        result = infer({**BASE, "Insulin": 0}, allow_zero=True)
        self.assertTrue(result["legacy_zero_mode"])

    def test_no_coverage_abstains_instead_of_defaulting(self):
        values = {key: spec["max"] for key, spec in load_model()["features"].items()}
        values["Pregnancies"] = 0
        with self.assertRaises(InferenceError) as error:
            infer(values)
        self.assertEqual(error.exception.code, "no_rule_coverage")

    def test_rejects_non_finite_bool_and_text(self):
        for value in [math.nan, math.inf, -math.inf, True, "125", None]:
            with self.subTest(value=value), self.assertRaises(InferenceError):
                infer({**BASE, "Glucose": value})

    def test_rejects_out_of_range_without_clipping(self):
        for key, value in [("Age", 101), ("Age", 19), ("BMI", -1), ("Pregnancies", 18)]:
            with self.subTest(key=key), self.assertRaises(InferenceError) as error:
                infer({**BASE, key: value})
            self.assertEqual(error.exception.code, "out_of_range")

    def test_rejects_fractional_count_and_age(self):
        for key in ["Age", "Pregnancies"]:
            with self.subTest(key=key), self.assertRaises(InferenceError):
                infer({**BASE, key: 2.5})

    def test_outcome_cannot_leak_into_inference(self):
        with self.assertRaises(InferenceError) as error:
            infer({**BASE, "Outcome": 1})
        self.assertEqual(error.exception.code, "schema")

    def test_missing_feature_is_not_silently_assumed(self):
        values = copy.deepcopy(BASE)
        del values["Age"]
        with self.assertRaises(InferenceError):
            infer(values)

    def test_repeated_calls_are_stateless(self):
        first = infer(BASE)
        infer({**BASE, "Glucose": 180, "BMI": 40})
        self.assertEqual(first, infer(BASE))

    def test_memberships_and_scores_are_bounded(self):
        import json
        from pathlib import Path

        cases = json.loads((Path(__file__).parent / "golden.json").read_text())
        for case in cases:
            if "error" in case["expected"]:
                continue
            result = infer(case["input"])
            self.assertTrue(0 <= result["score"] <= 1)
            self.assertTrue(
                all(
                    0 <= value <= 1
                    for terms in result["memberships"].values()
                    for value in terms.values()
                )
            )
