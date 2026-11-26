// Browser implementation of the shared model contract. Python parity is tested.
export class InferenceError extends Error {
  constructor(code, message) {
    super(message);
    this.code = code;
  }
}
export function membership(value, raw) {
  const [a, b, c, d] =
    raw.length === 3 ? [raw[0], raw[1], raw[1], raw[2]] : raw;
  if (value < a || value > d) return 0;
  if (b <= value && value <= c) return 1;
  if (a <= value && value < b) return (value - a) / (b - a);
  if (c < value && value <= d) return (d - value) / (d - c);
  return 0;
}
export function infer(values, config) {
  const expected = Object.keys(config.features);
  if (
    !values ||
    typeof values !== "object" ||
    Array.isArray(values) ||
    Object.keys(values).length !== expected.length ||
    expected.some((key) => !Object.hasOwn(values, key))
  )
    throw new InferenceError(
      "schema",
      "Provide exactly the eight model inputs.",
    );
  const memberships = {};
  for (const [key, spec] of Object.entries(config.features)) {
    const value = values[key];
    if (typeof value !== "number" || !Number.isFinite(value))
      throw new InferenceError(
        "invalid_input",
        `${spec.label} must be a finite number.`,
      );
    if (value < spec.min || value > spec.max)
      throw new InferenceError(
        "out_of_range",
        `${spec.label} is outside the model range ${spec.min}–${spec.max}.`,
      );
    if (["Pregnancies", "Age"].includes(key) && !Number.isInteger(value))
      throw new InferenceError(
        "invalid_input",
        `${spec.label} must be a whole number.`,
      );
    if (value === 0 && spec.zero_missing)
      throw new InferenceError(
        "missing_input",
        `${spec.label}=0 is treated as missing. No model score was produced.`,
      );
    memberships[key] = Object.fromEntries(
      Object.entries(spec.terms).map(([term, points]) => [
        term,
        membership(value, points),
      ]),
    );
  }
  const strengths = Object.fromEntries(
    Object.keys(config.output).map((term) => [term, 0]),
  );
  const activations = [];
  for (const rule of config.rules) {
    const strength = Math.min(
      ...rule.if.map((item) => memberships[item.feature][item.term]),
    );
    if (strength > 0)
      activations.push({ id: rule.id, strength, consequent: rule.then });
    strengths[rule.then] = Math.max(strengths[rule.then], strength);
  }
  const knots = new Set([0, 1]);
  for (const [term, raw] of Object.entries(config.output)) {
    raw.forEach((point) => knots.add(point));
    const [a, b, c, d] =
      raw.length === 3 ? [raw[0], raw[1], raw[1], raw[2]] : raw;
    const alpha = strengths[term];
    if (alpha > 0 && alpha < 1) {
      if (b > a) knots.add(a + alpha * (b - a));
      if (d > c) knots.add(d - alpha * (d - c));
    }
  }
  const base = [...knots].sort((a, b) => a - b);
  const terms = Object.keys(config.output);
  const clipped = (term, x) =>
    Math.min(strengths[term], membership(x, config.output[term]));
  for (let k = 0; k < base.length - 1; k++) {
    const left = base[k],
      right = base[k + 1];
    for (let i = 0; i < terms.length; i++)
      for (let j = i + 1; j < terms.length; j++) {
        const dl = clipped(terms[i], left) - clipped(terms[j], left);
        const dr = clipped(terms[i], right) - clipped(terms[j], right);
        if (dl * dr < 0) knots.add(left + ((right - left) * dl) / (dl - dr));
      }
  }
  const envelope = [...knots]
    .sort((a, b) => a - b)
    .map((x) => [x, Math.max(...terms.map((term) => clipped(term, x)))]);
  let area = 0,
    moment = 0;
  for (let i = 0; i < envelope.length - 1; i++) {
    const [x0, y0] = envelope[i],
      [x1, y1] = envelope[i + 1],
      width = x1 - x0;
    const segmentArea = (width * (y0 + y1)) / 2;
    area += segmentArea;
    moment += x0 * segmentArea + (width * width * (y0 + 2 * y1)) / 6;
  }
  if (area <= 0)
    throw new InferenceError(
      "no_rule_coverage",
      "No rule fired for these values. The model abstains instead of inventing a score.",
    );
  let score = moment / area;
  if (Math.abs(score - config.threshold) <= config.threshold_tolerance)
    score = config.threshold;
  return {
    score,
    model_class: Number(score >= config.threshold),
    band: score < 0.4 ? "Low" : score >= 0.6 ? "High" : "Medium",
    memberships,
    strengths,
    envelope,
    activations: activations.sort(
      (a, b) => b.strength - a.strength || a.id.localeCompare(b.id),
    ),
  };
}
