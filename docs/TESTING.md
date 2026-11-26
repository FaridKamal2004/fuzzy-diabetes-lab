# Test report

Validation date: **26 November 2026**, Asia/Kuala_Lumpur.

| Check | Result | What it verifies |
| --- | --- | --- |
| Python unittest suite | 33 passed | Analytical centroids, input/schema validation, explicit abstention, statelessness, metrics, denominator accounting, training-only imputation, CSV handling and CLI behavior |
| Independent numerical reference | Included in Python suite | Membership curves checked against scikit-fuzzy; 40 synthetic scenarios checked against a separate 10,001-point Mamdani control system with 1e-8 score tolerance |
| Python/JavaScript parity | 120 passed | Deterministic synthetic fixtures compare score, class, band, aggregate strengths and error codes; score tolerance 1e-12 |
| Playwright desktop | 7 passed | Presets, input editing, membership plots, missing/uncovered cases, rule filters, evaluation policies, privacy/layout and accessibility |
| Playwright mobile | 7 passed | Same behavior under Pixel 7 Chromium emulation |
| axe-core scan | No detected violations | WCAG 2/2.1 A/AA checks across Explorer, Rule book and Evaluation, desktop and mobile; included in browser tests |
| Generated asset verification | Passed | Browser model/report and synthetic fixtures match their Python sources |
| Python distribution build | Passed | Installable wheel and source archive include the model configuration |

Total automated test cases: **167** (33 Python + 120 parity + 14 browser), with no failed or skipped cases in the final local run. Reference scenario loops and accessibility scans are included within those tests, not added again to inflate the total. CI repeats Python verification on 3.11 and 3.12 and runs the browser suite on Ubuntu 24.04.

## Bugs and issues found during enhancement

- The original source contained notebook-only installation syntax and coupled import/execution to a network dataset download. Package imports are now local and side-effect-free.
- Inference errors were silently swallowed and failed rows excluded. Named errors and coverage counts now preserve the attempted denominator.
- The historical export has 147 near-threshold scores, with 115 class disagreements under an explicit positive tie rule. The tie convention and historical/new result distinction are documented.
- The original 101-point output grid and exact envelope differ slightly around some intersections. An independent 10,001-point control system confirmed the exact method within the stated tolerance.
- Two output-card labels initially failed contrast checks; colors were darkened.
- The horizontally scrolling rule table initially could not receive keyboard focus on mobile; it is now a named, focusable region.
- Duplicate CSV columns and all-missing training columns are rejected explicitly.

## Reproduce

```sh
python -m pip install -e ".[test]"
python scripts/build_site.py --check
python -m unittest discover -s tests -v
npm ci
npm test
npx playwright install chromium
npm run test:e2e
```

For Linux system dependencies use `npx playwright install --with-deps chromium`. The test server is started automatically, or an existing local server on port 4175 can be reused outside CI. Browser failure traces are retained under ignored `test-results/`.

Screenshots were captured and visually reviewed for the [desktop explorer](explorer.png), [mobile explorer](mobile.png) and [evaluation view](evaluation.png). To regenerate with a running preview server: `node scripts/capture.mjs`. Set `DEMO_URL` to capture a deployed site.

## Benchmark evaluation is separate from software tests

The aggregate benchmark uses a local CSV with the checksum in [DATA.md](DATA.md). It is not downloaded by CI. The report has 154 holdout records, 67.53% imputed accuracy and 100% coverage; strict handling scores 76 and abstains on 78. The training-majority baseline has 64.94% accuracy. Rules were originally designed using the dataset, so these results are not untouched external or clinical validation.

## Limits of verification

Mobile tests are browser emulation, not a physical-device certification. Firefox, Safari, full screen-reader usability, complete accessibility conformance, model calibration, subgroup fairness, clinical validity, external population performance and uncertainty intervals are not established. No model API or real-patient storage workflow exists to test. No medical benefit is claimed.
