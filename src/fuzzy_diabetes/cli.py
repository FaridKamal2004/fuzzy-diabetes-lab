"""JSON/CSV command line interface; no package installation or networking at import."""

import argparse
import json
from pathlib import Path
import sys

from .engine import InferenceError, infer
from .evaluation import evaluate_dataset


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="Educational fuzzy model lab; not for medical decisions."
    )
    commands = parser.add_subparsers(dest="command", required=True)
    predict = commands.add_parser(
        "explain", help="Explain eight feature values from a JSON file."
    )
    predict.add_argument("input", type=Path)
    evaluate = commands.add_parser(
        "evaluate", help="Evaluate a local benchmark CSV and report all abstentions."
    )
    evaluate.add_argument("csv", type=Path)
    evaluate.add_argument("--output", type=Path)
    args = parser.parse_args(argv)
    try:
        result = (
            infer(json.loads(args.input.read_text(encoding="utf-8")))
            if args.command == "explain"
            else evaluate_dataset(args.csv)
        )
        text = json.dumps(result, indent=2, allow_nan=False) + "\n"
        if args.command == "evaluate" and args.output:
            args.output.parent.mkdir(parents=True, exist_ok=True)
            args.output.write_text(text, encoding="utf-8")
        else:
            print(text, end="")
        return 0
    except (InferenceError, ValueError, OSError) as error:
        print(
            json.dumps(
                {"error": getattr(error, "code", "invalid_data"), "message": str(error)}
            ),
            file=sys.stderr,
        )
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
