"""Export shared configuration and synthetic parity fixtures, without patient rows."""

import argparse
import json
from pathlib import Path
import random
from fuzzy_diabetes import InferenceError, infer, load_model

ROOT = Path(__file__).resolve().parents[1]


def fixtures():
    model = load_model()
    rng = random.Random(2026)
    cases = []
    for i in range(120):
        values = {}
        for key, spec in model["features"].items():
            lo = 1 if spec["zero_missing"] else spec["min"]
            value = rng.uniform(lo, spec["max"])
            values[key] = (
                round(value) if key in ("Age", "Pregnancies") else round(value, 3)
            )
        if i == 0:
            values["Glucose"] = 0
        if i == 1:
            values["Age"] = 101
        if i == 2:
            values = {key: spec["max"] for key, spec in model["features"].items()}
            values["Pregnancies"] = 0
        try:
            result = infer(values)
            expected = {
                key: result[key]
                for key in ("score", "model_class", "band", "strengths")
            }
        except InferenceError as error:
            expected = {"error": error.code}
        cases.append(
            {"id": f"synthetic-{i:03d}", "input": values, "expected": expected}
        )
    return cases


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    assets = {
        "site/model.json": load_model(),
        "tests/golden.json": fixtures(),
        "site/evaluation.json": json.loads(
            (ROOT / "reports/evaluation.json").read_text(encoding="utf-8")
        ),
    }
    for relative, value in assets.items():
        path = ROOT / relative
        text = json.dumps(value, indent=2, ensure_ascii=False, allow_nan=False) + "\n"
        if args.check:
            if not path.exists() or path.read_text(encoding="utf-8") != text:
                raise SystemExit(
                    f"Stale generated file: {relative}. Run python scripts/build_site.py"
                )
        else:
            path.write_text(text, encoding="utf-8")
    print(
        "Shared model and 120 synthetic parity cases verified."
        if args.check
        else "Shared model and synthetic cases exported."
    )


if __name__ == "__main__":
    main()
