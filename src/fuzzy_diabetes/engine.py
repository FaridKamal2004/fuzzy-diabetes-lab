"""Stateless Mamdani inference with exact piecewise-linear centroid integration."""

from functools import lru_cache
from importlib.resources import files
import json
import math


class InferenceError(ValueError):
    """Explicit input/coverage failure, never converted into a negative prediction."""

    def __init__(self, code, message):
        super().__init__(message)
        self.code = code


@lru_cache(maxsize=1)
def _model_text():
    return files("fuzzy_diabetes").joinpath("model.json").read_text(encoding="utf-8")


def load_model():
    """Return an independent configuration so callers cannot mutate global state."""
    return json.loads(_model_text())


def membership(value, points):
    """Triangular/trapezoidal set, including vertical shoulder endpoints."""
    if len(points) == 3:
        a, b, c = points
        points = (a, b, b, c)
    a, b, c, d = points
    if value < a or value > d:
        return 0.0
    if b <= value <= c:
        return 1.0
    if a <= value < b:
        return (value - a) / (b - a)
    if c < value <= d:
        return (d - value) / (d - c)
    return 0.0


def validate(values, config, allow_zero=False):
    if not isinstance(values, dict):
        raise InferenceError("invalid_input", "Inputs must be a feature-name mapping.")
    expected = set(config["features"])
    if set(values) != expected:
        missing, extra = sorted(expected - set(values)), sorted(set(values) - expected)
        raise InferenceError(
            "schema", f"Feature mismatch. Missing: {missing}; extra: {extra}."
        )
    clean = {}
    for key, spec in config["features"].items():
        value = values[key]
        if (
            isinstance(value, bool)
            or not isinstance(value, (int, float))
            or not math.isfinite(value)
        ):
            raise InferenceError("invalid_input", f"{key} must be a finite number.")
        if value < spec["min"] or value > spec["max"]:
            raise InferenceError(
                "out_of_range",
                f"{key} must lie in model range {spec['min']}–{spec['max']}.",
            )
        if key in ("Pregnancies", "Age") and not float(value).is_integer():
            raise InferenceError("invalid_input", f"{key} must be a whole number.")
        if value == 0 and spec["zero_missing"] and not allow_zero:
            raise InferenceError(
                "missing_input",
                f"{key}=0 is treated as missing by this lab; no score was produced.",
            )
        clean[key] = float(value)
    return clean


def aggregate_output(strengths, output):
    """Return all vertices of the exact max/min envelope, not a sampled estimate."""
    knots = {0.0, 1.0}
    for term, points in output.items():
        knots.update(float(point) for point in points)
        if len(points) == 3:
            a, b, d = points
            c = b
        else:
            a, b, c, d = points
        alpha = strengths[term]
        if 0 < alpha < 1:
            if b > a:
                knots.add(a + alpha * (b - a))
            if d > c:
                knots.add(d - alpha * (d - c))
    base = sorted(knots)
    terms = list(output)

    def clipped(term, x):
        return min(strengths[term], membership(x, output[term]))

    # Between existing knots each clipped term is linear. Add term crossings.
    for left, right in zip(base, base[1:]):
        for i, first in enumerate(terms):
            for second in terms[i + 1 :]:
                dl = clipped(first, left) - clipped(second, left)
                dr = clipped(first, right) - clipped(second, right)
                if dl * dr < 0:
                    knots.add(left + (right - left) * dl / (dl - dr))
    return [(x, max(clipped(term, x) for term in terms)) for x in sorted(knots)]


def centroid(vertices):
    area = moment = 0.0
    for (x0, y0), (x1, y1) in zip(vertices, vertices[1:]):
        width = x1 - x0
        segment_area = width * (y0 + y1) / 2
        area += segment_area
        moment += x0 * segment_area + width * width * (y0 + 2 * y1) / 6
    if area <= 0:
        raise InferenceError(
            "no_rule_coverage",
            "No rule fired. The model abstains instead of inventing a score.",
        )
    return moment / area


def infer(values, *, allow_zero=False, config=None):
    """Explain the model output. allow_zero is only for labeled legacy comparisons."""
    config = config or load_model()
    clean = validate(values, config, allow_zero)
    memberships = {
        key: {
            term: membership(clean[key], points)
            for term, points in spec["terms"].items()
        }
        for key, spec in config["features"].items()
    }
    activations = []
    strengths = dict.fromkeys(config["output"], 0.0)
    for rule in config["rules"]:
        strength = min(
            memberships[item["feature"]][item["term"]] for item in rule["if"]
        )
        if strength > 0:
            activations.append(
                {"id": rule["id"], "strength": strength, "consequent": rule["then"]}
            )
        strengths[rule["then"]] = max(strengths[rule["then"]], strength)
    envelope = aggregate_output(strengths, config["output"])
    score = centroid(envelope)
    if abs(score - config["threshold"]) <= config["threshold_tolerance"]:
        score = config["threshold"]
    return {
        "score": score,
        "model_class": int(score >= config["threshold"]),
        "band": "Low" if score < 0.4 else "High" if score >= 0.6 else "Medium",
        "memberships": memberships,
        "activations": sorted(
            activations, key=lambda rule: (-rule["strength"], rule["id"])
        ),
        "strengths": strengths,
        "envelope": envelope,
        "legacy_zero_mode": allow_zero,
    }
