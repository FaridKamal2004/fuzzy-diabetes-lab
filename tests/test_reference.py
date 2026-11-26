"""Independent numerical cross-check using scikit-fuzzy, a test-only dependency."""

import json
from pathlib import Path
import unittest
import numpy as np
import skfuzzy as fuzz
from skfuzzy import control as ctrl
from fuzzy_diabetes import InferenceError, infer, load_model, membership


class ReferenceTests(unittest.TestCase):
    def test_membership_functions_match_scikit_fuzzy(self):
        model = load_model()
        for spec in model["features"].values():
            xs = np.linspace(spec["min"], spec["max"], 301)
            for points in spec["terms"].values():
                reference = (
                    fuzz.trimf(xs, points)
                    if len(points) == 3
                    else fuzz.trapmf(xs, points)
                )
                np.testing.assert_allclose(
                    [membership(float(x), points) for x in xs], reference, atol=1e-12
                )

    def test_mamdani_scores_match_independent_control_system(self):
        model = load_model()
        inputs = {}
        for key, spec in model["features"].items():
            step = 0.01 if key == "DiabetesPedigreeFunction" else 1
            variable = ctrl.Antecedent(
                np.linspace(
                    spec["min"],
                    spec["max"],
                    round((spec["max"] - spec["min"]) / step) + 1,
                ),
                key,
            )
            for term, points in spec["terms"].items():
                variable[term] = (
                    fuzz.trimf(variable.universe, points)
                    if len(points) == 3
                    else fuzz.trapmf(variable.universe, points)
                )
            inputs[key] = variable
        # A fine grid independently checks the exact envelope. The original
        # 101-point grid misses some intersections and differs by about 1e-5.
        output = ctrl.Consequent(np.linspace(0, 1, 10001), "score")
        for term, points in model["output"].items():
            output[term] = (
                fuzz.trimf(output.universe, points)
                if len(points) == 3
                else fuzz.trapmf(output.universe, points)
            )
        rules = []
        for rule in model["rules"]:
            terms = [inputs[item["feature"]][item["term"]] for item in rule["if"]]
            antecedent = terms[0]
            for term in terms[1:]:
                antecedent = antecedent & term
            rules.append(ctrl.Rule(antecedent, output[rule["then"]]))
        simulation = ctrl.ControlSystemSimulation(
            ctrl.ControlSystem(rules), clip_to_bounds=False
        )
        cases = json.loads((Path(__file__).parent / "golden.json").read_text())
        for case in cases[3:43]:
            with self.subTest(case=case["id"]):
                for key, value in case["input"].items():
                    simulation.input[key] = value
                simulation.compute()
                if "error" in case["expected"]:
                    self.assertNotIn("score", simulation.output)
                else:
                    self.assertAlmostEqual(
                        infer(case["input"])["score"],
                        simulation.output["score"],
                        delta=1e-8,
                    )
                simulation.reset()
