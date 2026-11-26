import { infer, membership } from "./engine.js";
const $ = (selector) => document.querySelector(selector);
const escape = (text) =>
  String(text).replace(
    /[&<>"']/g,
    (c) =>
      ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" })[
        c
      ],
  );
const presets = {
  low: {
    Pregnancies: 0,
    Glucose: 85,
    BloodPressure: 75,
    SkinThickness: 15,
    Insulin: 60,
    BMI: 21,
    DiabetesPedigreeFunction: 0.25,
    Age: 25,
  },
  middle: {
    Pregnancies: 4,
    Glucose: 125,
    BloodPressure: 75,
    SkinThickness: 30,
    Insulin: 200,
    BMI: 27,
    DiabetesPedigreeFunction: 0.8,
    Age: 50,
  },
  high: {
    Pregnancies: 8,
    Glucose: 180,
    BloodPressure: 100,
    SkinThickness: 55,
    Insulin: 550,
    BMI: 38,
    DiabetesPedigreeFunction: 1.6,
    Age: 70,
  },
};
let model,
  report,
  current = { ...presets.middle },
  result = null,
  policy = "holdout_imputed";
const colors = ["#4c8996", "#b78d36", "#88629c"];
const ruleText = (rule) =>
  rule.if
    .map((item) => `${model.features[item.feature].label} is ${item.term}`)
    .join(" AND ");
function chart(
  series,
  { min = 0, max = 1, line = null, label = "Membership functions" } = {},
) {
  const w = 680,
    h = 220,
    left = 35,
    right = 15,
    top = 15,
    bottom = 35,
    px = (x) => left + ((x - min) / (max - min)) * (w - left - right),
    py = (y) => h - bottom - y * (h - top - bottom);
  const ticks = Array.from(
    { length: 6 },
    (_, i) => min + ((max - min) * i) / 5,
  );
  let svg = `<svg viewBox="0 0 ${w} ${h}" role="img" aria-label="${escape(label)}"><title>${escape(label)}</title>`;
  for (const y of [0, 0.5, 1])
    svg += `<path d="M${left},${py(y)}H${w - right}" class="gridline"/><text x="${left - 9}" y="${py(y) + 3}" text-anchor="end">${y}</text>`;
  for (const x of ticks)
    svg += `<text x="${px(x)}" y="${h - 13}" text-anchor="middle">${Number(x.toFixed(2))}</text>`;
  for (const item of series) {
    const path = item.points
      .map(
        ([x, y], i) =>
          `${i ? "L" : "M"}${px(x).toFixed(3)},${py(y).toFixed(3)}`,
      )
      .join(" ");
    if (item.fill)
      svg += `<path d="${path}L${px(max)},${py(0)}L${px(min)},${py(0)}Z" fill="${item.color}" opacity=".19"/>`;
    svg += `<path d="${path}" fill="none" stroke="${item.color}" stroke-width="${item.fill ? 2.5 : 1.6}" ${item.dash ? 'stroke-dasharray="5 5"' : ""}/>`;
  }
  if (line !== null)
    svg += `<path d="M${px(line)},${top}V${h - bottom}" stroke="#163f44" stroke-width="1.6" stroke-dasharray="4 4"/><circle cx="${px(line)}" cy="${h - bottom}" r="4" fill="#163f44"/>`;
  return svg + "</svg>";
}
function points(shape, min, max) {
  const xs = new Set([min, max, ...shape]);
  for (let i = 0; i <= 150; i++) xs.add(min + ((max - min) * i) / 150);
  return [...xs].sort((a, b) => a - b).map((x) => [x, membership(x, shape)]);
}
function switchTab(tab) {
  for (const name of ["explorer", "rules", "evaluation"])
    $(`#${name}`).hidden = name !== tab;
  for (const button of document.querySelectorAll("[data-tab]")) {
    button.classList.toggle("active", button.dataset.tab === tab);
    if (button.dataset.tab === tab) button.setAttribute("aria-current", "page");
    else button.removeAttribute("aria-current");
  }
}
function run() {
  result = null;
  let failure = null;
  try {
    result = infer(current, model);
  } catch (error) {
    failure = error;
  }
  $("#inference-error").hidden = !failure;
  $("#error-message").textContent = failure?.message || "";
  $("#score").textContent = result ? result.score.toFixed(3) : "—";
  $("#result-band").textContent = result
    ? `${result.band} model band`
    : "Model abstained";
  $("#result-class").textContent = result
    ? `Threshold class ${result.model_class}`
    : "No threshold class";
  $("#score-description").textContent = result
    ? "Centroid of the aggregated output."
    : "Inputs need attention, or the rules do not cover this scenario.";
  const series = Object.entries(model.output).map(([term, shape], i) => ({
    points: points(shape, 0, 1),
    color: colors[i],
    dash: true,
  }));
  if (result)
    series.push({ points: result.envelope, color: "#267b70", fill: true });
  $("#output-chart").innerHTML = chart(series, {
    line: result?.score ?? null,
    label: result
      ? `Output membership functions and aggregate; centroid ${result.score.toFixed(3)}`
      : "Output membership functions; no inferred aggregate",
  });
  $("#activation-count").textContent =
    `${result?.activations.length || 0} / 40 ACTIVE`;
  $("#activations").innerHTML = result?.activations.length
    ? result.activations
        .slice(0, 5)
        .map((active) => {
          const rule = model.rules.find((r) => r.id === active.id);
          return `<div class="rule-trace"><span class="rule-id">${rule.id}</span><div><p>${escape(ruleText(rule))}</p><span>THEN ${rule.then.toUpperCase()} OUTPUT</span></div><div class="strength"><span>${Math.round(active.strength * 100)}%</span><i style="--strength:${active.strength * 100}%"></i></div></div>`;
        })
        .join("")
    : '<p class="empty-trace">No rule trace is available for an abstained scenario.</p>';
  renderMembership();
  renderRules();
}
function renderMembership() {
  const key = $("#feature-select").value,
    spec = model.features[key];
  if (!spec) return;
  $("#membership-chart").innerHTML =
    chart(
      Object.entries(spec.terms).map(([term, shape], i) => ({
        points: points(shape, spec.min, spec.max),
        color: colors[i],
      })),
      {
        min: spec.min,
        max: spec.max,
        line: Number.isFinite(current[key]) ? current[key] : null,
        label: `${spec.label} membership functions; current synthetic input ${current[key]} ${spec.unit}`,
      },
    ) +
    `<div class="membership-values">${Object.entries(spec.terms)
      .map(
        ([term, shape], i) =>
          `<span><i style="background:${colors[i]}"></i>${term} <strong>${Number.isFinite(current[key]) ? membership(current[key], shape).toFixed(3) : "—"}</strong></span>`,
      )
      .join("")}</div>`;
}
function renderRules() {
  const query = $("#rule-search").value.trim().toLowerCase(),
    activeOnly = $("#active-only").checked;
  const active = new Map(
    (result?.activations || []).map((rule) => [rule.id, rule.strength]),
  );
  const rules = model.rules.filter(
    (rule) =>
      (!activeOnly || active.has(rule.id)) &&
      `${rule.id} ${ruleText(rule)} ${rule.then}`.toLowerCase().includes(query),
  );
  $("#rule-summary").textContent =
    `${rules.length} of 40 rules shown · Current synthetic scenario`;
  $("#rule-table").innerHTML =
    rules
      .map(
        (rule) =>
          `<tr><td>${rule.id}</td><td>${escape(ruleText(rule))}</td><td><span class="output-term">${rule.then}</span></td><td>${(active.get(rule.id) || 0).toFixed(3)}</td></tr>`,
      )
      .join("") ||
    '<tr><td colspan="4">No rules match the current filter.</td></tr>';
}
const percent = (value) =>
  value === null ? "Undefined" : `${(value * 100).toFixed(1)}%`;
function renderEvaluation() {
  if (!report) return;
  const metrics = report[policy],
    matrix = metrics.confusion_matrix;
  $("#evaluation-meta").textContent =
    `${report.rows} benchmark rows · ${report.split.train} training / ${report.split.test} holdout · Seed ${report.split.seed} · Fixed 0.5 threshold`;
  $("#metric-cards").innerHTML = [
    ["Accuracy on scored", percent(metrics.accuracy_on_scored)],
    ["Coverage", percent(metrics.coverage)],
    ["Recall", percent(metrics.recall)],
    ["F1 score", metrics.f1 === null ? "Undefined" : metrics.f1.toFixed(3)],
  ]
    .map(
      ([label, value]) =>
        `<article><span>${label}</span><strong>${value}</strong></article>`,
    )
    .join("");
  $("#confusion-matrix").innerHTML = [
    ["True negatives", matrix.tn],
    ["False positives", matrix.fp],
    ["False negatives", matrix.fn],
    ["True positives", matrix.tp],
  ]
    .map(
      ([label, value]) =>
        `<div><span>${label}</span><strong>${value}</strong></div>`,
    )
    .join("");
  $("#coverage-detail").innerHTML =
    `<div class="coverage-count"><strong>${metrics.scored}<small> / ${metrics.attempted}</small></strong><span>records scored</span></div><p><strong>${metrics.abstained}</strong> abstained. Correct predictions over all attempted records: <strong>${percent(metrics.correct_over_attempted)}</strong>.</p><p>Failure counts: ${
      Object.entries(metrics.failures)
        .map(([key, value]) => `${escape(key)}: ${value}`)
        .join(", ") || "none"
    }.</p>`;
  $("#evaluation-note").textContent =
    `The training-majority baseline scores ${percent(report.holdout_majority_baseline.accuracy_on_scored)} accuracy on the same holdout. This split is reproducible, but the rules were originally designed using this dataset, so it is not independent validation. A score near 0.5 uses a documented numerical tie convention. The original report’s accuracy is not substituted for this evaluation.`;
}
function loadPreset(name) {
  current = { ...presets[name] };
  for (const key of Object.keys(model.features))
    $(`#input-${key}`).value = current[key];
  for (const button of document.querySelectorAll("[data-preset]"))
    button.classList.toggle("selected", button.dataset.preset === name);
  run();
}
async function start() {
  try {
    const response = await fetch("./model.json");
    if (!response.ok) throw Error("Model configuration could not load.");
    model = await response.json();
    $("#fields").innerHTML = Object.entries(model.features)
      .map(
        ([key, spec]) =>
          `<div class="field"><label for="input-${key}">${escape(spec.label)}</label><div class="number-wrap"><input type="number" id="input-${key}" name="${key}" min="${spec.min}" max="${spec.max}" step="${spec.step}" required value="${current[key]}" aria-describedby="unit-${key}"><span id="unit-${key}">${escape(spec.unit)}</span></div></div>`,
      )
      .join("");
    $("#feature-select").innerHTML = Object.entries(model.features)
      .map(
        ([key, spec]) =>
          `<option value="${key}" ${key === "Glucose" ? "selected" : ""}>${escape(spec.label)}</option>`,
      )
      .join("");
    $("#input-form").addEventListener("submit", (event) => {
      event.preventDefault();
      current = Object.fromEntries(
        Object.keys(model.features).map((key) => [
          key,
          $(`#input-${key}`).valueAsNumber,
        ]),
      );
      for (const button of document.querySelectorAll("[data-preset]"))
        button.classList.remove("selected");
      run();
    });
    document.addEventListener("click", (event) => {
      const button = event.target.closest("button");
      if (!button) return;
      if (button.dataset.tab) switchTab(button.dataset.tab);
      if (button.dataset.preset) loadPreset(button.dataset.preset);
      if (button.dataset.policy) {
        policy = button.dataset.policy;
        for (const item of document.querySelectorAll("[data-policy]"))
          item.classList.toggle("selected", item.dataset.policy === policy);
        renderEvaluation();
      }
    });
    $("#feature-select").addEventListener("change", renderMembership);
    $("#rule-search").addEventListener("input", renderRules);
    $("#active-only").addEventListener("change", renderRules);
    $("#inspect-rules").addEventListener("click", () => switchTab("rules"));
    const setEdge = (values) => {
      current = values;
      for (const key of Object.keys(model.features))
        $(`#input-${key}`).value = current[key];
      for (const button of document.querySelectorAll("[data-preset]"))
        button.classList.remove("selected");
      run();
    };
    $("#missing-example").addEventListener("click", () =>
      setEdge({ ...presets.middle, Insulin: 0 }),
    );
    $("#gap-example").addEventListener("click", () =>
      setEdge({
        ...Object.fromEntries(
          Object.entries(model.features).map(([key, spec]) => [key, spec.max]),
        ),
        Pregnancies: 0,
      }),
    );
    run();
    try {
      const r = await fetch("./evaluation.json");
      if (!r.ok) throw Error("Evaluation report unavailable.");
      report = await r.json();
      renderEvaluation();
    } catch (error) {
      $("#evaluation-meta").textContent =
        "Evaluation report could not load. Open the versioned report on GitHub.";
    }
  } catch (error) {
    $("#inference-error").hidden = false;
    $("#error-message").textContent =
      `${error.message} Reload the page to retry.`;
    $("#score").textContent = "—";
    $("#result-band").textContent = "Model unavailable";
    $("#result-class").textContent = "No threshold class";
  }
}
start();
