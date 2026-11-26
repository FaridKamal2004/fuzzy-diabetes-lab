import { test, expect } from "@playwright/test";
import AxeBuilder from "@axe-core/playwright";
test("presets update score, plotted centroid and rule trace", async ({
  page,
}) => {
  await page.goto("/");
  await expect(page.locator("#score")).toHaveText("0.500");
  await page.getByRole("button", { name: "Higher", exact: true }).click();
  await expect(page.locator("#result-band")).toHaveText("High model band");
  await expect(page.locator("#score")).not.toHaveText("0.500");
  await expect(page.locator("#output-chart svg")).toHaveAttribute(
    "aria-label",
    /centroid/,
  );
  await expect(page.locator("#activations .rule-trace")).toHaveCount(5);
  await page.getByRole("button", { name: "Lower", exact: true }).click();
  await expect(page.locator("#result-band")).toHaveText("Low model band");
});
test("manual input updates inference and feature memberships", async ({
  page,
}) => {
  await page.goto("/");
  await page.getByLabel("Glucose", { exact: true }).fill("180");
  await page.getByLabel("BMI", { exact: true }).fill("40");
  await page.getByRole("button", { name: /Explore the reasoning/ }).click();
  await expect(page.locator("#result-band")).toHaveText("High model band");
  await page.getByLabel("Inspect a feature").selectOption("BMI");
  await expect(page.locator("#membership-chart svg")).toHaveAttribute(
    "aria-label",
    /BMI.*40/,
  );
});
test("missing inputs and uncovered rules abstain without stale scores", async ({
  page,
}) => {
  await page.goto("/");
  await page.getByRole("button", { name: /Missing value/ }).click();
  await expect(page.locator("#score")).toHaveText("—");
  await expect(page.getByRole("alert")).toContainText("treated as missing");
  await expect(page.locator("#activations")).toContainText("No rule trace");
  await page.getByRole("button", { name: /Coverage gap/ }).click();
  await expect(page.getByRole("alert")).toContainText("No rule fired");
  await page.getByRole("button", { name: "Middle", exact: true }).click();
  await expect(page.getByRole("alert")).not.toBeVisible();
  await expect(page.locator("#score")).toHaveText("0.500");
});
test("rule book searches and filters current activations", async ({ page }) => {
  await page.goto("/");
  await page.getByRole("button", { name: /Rule book/ }).click();
  await expect(page.locator("#rule-table tr")).toHaveCount(40);
  await page.getByRole("searchbox", { name: "Search rules" }).fill("R01");
  await expect(page.locator("#rule-table tr")).toHaveCount(1);
  await expect(page.locator("#rule-table")).toContainText("Glucose is High");
  await page.getByRole("searchbox").fill("");
  await page.getByLabel("Show active rules only").check();
  expect(await page.locator("#rule-table tr").count()).toBeLessThan(40);
});
test("evaluation policies show denominators and match published report", async ({
  page,
}) => {
  await page.goto("/");
  await page.getByRole("button", { name: "Evaluation", exact: true }).click();
  await expect(page.locator("#evaluation-meta")).toContainText("154 holdout");
  await expect(page.locator("#metric-cards")).toContainText("67.5%");
  await page
    .getByRole("button", { name: "Strict / abstain on missing", exact: true })
    .click();
  await expect(page.locator("#coverage-detail")).toContainText("78 abstained");
  await expect(page.locator("#metric-cards")).toContainText("49.4%");
});
test("no inputs persist, no external requests, and layout fits the viewport", async ({
  page,
}) => {
  const external = [],
    errors = [];
  page.on("request", (request) => {
    if (!request.url().startsWith("http://127.0.0.1:4175/"))
      external.push(request.url());
  });
  page.on("pageerror", (error) => errors.push(error.message));
  await page.goto("/");
  await expect(page.locator("#score")).toHaveText("0.500");
  expect(
    await page.evaluate(
      () => document.documentElement.scrollWidth <= innerWidth,
    ),
  ).toBe(true);
  expect(await page.evaluate(() => localStorage.length)).toBe(0);
  expect(external).toEqual([]);
  expect(errors).toEqual([]);
});
test("explorer, rule book and evaluation have no detectable WCAG A/AA violations", async ({
  page,
}) => {
  await page.goto("/");
  await expect(page.locator("#score")).toHaveText("0.500");
  for (const name of [null, /Rule book/, "Evaluation"]) {
    if (name) await page.getByRole("button", { name }).click();
    const scan = await new AxeBuilder({ page })
      .withTags(["wcag2a", "wcag2aa", "wcag21a", "wcag21aa"])
      .analyze();
    expect(scan.violations).toEqual([]);
  }
});
