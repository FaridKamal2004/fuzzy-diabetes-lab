import test from "node:test";
import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import { infer } from "../site/engine.js";
const model = JSON.parse(
  await readFile(new URL("../site/model.json", import.meta.url), "utf8"),
);
const cases = JSON.parse(
  await readFile(new URL("./golden.json", import.meta.url), "utf8"),
);
for (const fixture of cases)
  test(`Python/browser parity: ${fixture.id}`, () => {
    if (fixture.expected.error) {
      assert.throws(
        () => infer(fixture.input, model),
        (error) => error.code === fixture.expected.error,
      );
      return;
    }
    const actual = infer(fixture.input, model);
    assert.ok(Math.abs(actual.score - fixture.expected.score) < 1e-12);
    assert.equal(actual.model_class, fixture.expected.model_class);
    assert.equal(actual.band, fixture.expected.band);
    for (const key of Object.keys(fixture.expected.strengths))
      assert.ok(
        Math.abs(actual.strengths[key] - fixture.expected.strengths[key]) <
          1e-12,
      );
  });
