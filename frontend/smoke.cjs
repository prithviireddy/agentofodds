// Run with PLAYWRIGHT_MODULE pointing at an installed playwright module; start the UI first.
const { chromium } = require(process.env.PLAYWRIGHT_MODULE || "playwright");
const assert = require("node:assert/strict");
const fs = require("node:fs");
(async () => {
  const browser = await chromium.launch({ headless: true });
  const page = await browser.newPage({
    viewport: { width: 1400, height: 1000 },
  });
  const errors = [];
  page.on("pageerror", (e) => errors.push(e.message));
  const companyCount = Number(process.env.EXPECTED_COMPANIES || 5);
  const out = process.env.UI_SCREENSHOT_DIR || "data/ui-verification";
  fs.mkdirSync(out, { recursive: true });
  await page.goto(process.env.UI_BASE_URL || "http://127.0.0.1:8765");
  await page.getByRole("button", { name: "Load demo policy" }).click();
  await page.screenshot({ path: out + "/configure.png", fullPage: true });
  await page.getByRole("button", { name: "Run fixture research" }).click();
  await page.waitForFunction(
    () => document.querySelector("#status")?.textContent === "SUCCESS",
  );
  assert.equal(
    await page.locator("#allocation tbody tr").count(),
    companyCount + 1,
  );
  await page.locator("#reports summary").first().click();
  await page.getByText("Cited passage ·").first().click();
  await page.screenshot({ path: out + "/reviewed.png", fullPage: true });
  const run = await page.evaluate(() =>
    localStorage.getItem("agent-of-odds-run"),
  );
  const approve = page.getByRole("button", { name: "Approve paper portfolio" });
  await approve.waitFor();
  assert.equal(await approve.isDisabled(), true);
  await page
    .getByLabel(
      "I approve this exact synthetic replay and its stated fill and fee conventions.",
    )
    .check();
  await approve.click();
  await page.getByTestId("paper-approved").waitFor();
  await page
    .getByTestId("paper-ledger")
    .screenshot({ path: out + "/paper-approved.png" });
  const receipt = await page.evaluate(
    async (id) => (await fetch(`/api/runs/${id}/paper`)).json(),
    run,
  );
  assert.equal(receipt.status, "approved");
  assert.equal(receipt.summary.journal_entries, companyCount + 1);
  assert.equal(receipt.summary.reconciliation_difference, "0");
  const beforeValuation = await page.evaluate(
    async (id) => (await fetch(`/api/runs/${id}`)).json(),
    run,
  );
  await page.getByLabel("Fixture valuation date", { exact: true }).waitFor();
  await page.getByRole("button", { name: "Update prices only" }).click();
  await page.getByTestId("valuation-result").waitFor();
  const firstDate = await page
    .getByLabel("Fixture valuation date", { exact: true })
    .inputValue();
  await page
    .getByLabel("Fixture valuation date", { exact: true })
    .selectOption({ index: 1 });
  await page.getByRole("button", { name: "Update prices only" }).click();
  await page.getByText("2 saved valuations.", { exact: false }).waitFor();
  await page
    .getByLabel("Replay saved valuation", { exact: true })
    .selectOption(firstDate);
  assert.equal(
    await page
      .getByTestId("valuation-result")
      .locator("h4 time")
      .getAttribute("datetime"),
    firstDate,
  );
  const valuations = await page.evaluate(
    async (id) => (await fetch(`/api/runs/${id}/valuations`)).json(),
    run,
  );
  assert.equal(valuations.history.length, 2);
  assert.equal(valuations.mode, "synthetic_historical_replay");
  assert.deepEqual(
    await page.evaluate(
      async (id) => (await fetch(`/api/runs/${id}`)).json(),
      run,
    ),
    beforeValuation,
  );
  await page.setViewportSize({ width: 390, height: 844 });
  assert.equal(
    await page.evaluate(
      () => document.documentElement.scrollWidth <= innerWidth,
    ),
    true,
  );
  await page
    .getByTestId("monitoring")
    .screenshot({ path: out + "/monitoring-mobile.png" });
  await page.setViewportSize({ width: 1400, height: 1000 });
  await page.reload();
  await page.waitForFunction(
    () => document.querySelector("#status")?.textContent === "SUCCESS",
  );
  await page.getByTestId("paper-approved").waitFor();
  assert.equal(await approve.count(), 0);
  assert.deepEqual(
    await page.evaluate(
      async (id) => (await fetch(`/api/runs/${id}/paper`)).json(),
      run,
    ),
    receipt,
  );
  await page.getByTestId("valuation-result").waitFor();
  assert.deepEqual(
    await page.evaluate(
      async (id) => (await fetch(`/api/runs/${id}/valuations`)).json(),
      run,
    ),
    valuations,
  );
  assert.equal(
    await page.evaluate(() => localStorage.getItem("agent-of-odds-run")),
    run,
  );
  await page.locator("[name=scenario]").selectOption("review_rejected");
  await page.getByRole("button", { name: "Load demo policy" }).click();
  await page.locator("[name=scenario]").selectOption("review_rejected");
  await page.getByRole("button", { name: "Run fixture research" }).click();
  await page.waitForFunction(
    () => document.querySelector("#status")?.textContent === "REVIEW REJECTED",
  );
  assert.equal(await page.locator("#allocation tbody tr").count(), 0);
  assert.equal(await page.getByTestId("paper-ledger").count(), 0);
  await page.getByRole("button", { name: "Load demo policy" }).click();
  await page.locator("[name=scenario]").selectOption("quota");
  await page.getByRole("button", { name: "Run fixture research" }).click();
  await page.waitForFunction(
    () => document.querySelector("#status")?.textContent === "AWAITING QUOTA",
  );
  await page.getByRole("button", { name: "Retry failed stage" }).click();
  await page.waitForFunction(
    () => document.querySelector("#status")?.textContent === "SUCCESS",
  );
  // Keep a stage in flight long enough to exercise pause; fixtures can otherwise finish before the click.
  await page.route("**/api/runs/*/advance", async (route) => {
    const response = await route.fetch();
    await new Promise((resolve) => setTimeout(resolve, 150));
    await route.fulfill({ response });
  });
  await page.getByRole("button", { name: "Load demo policy" }).click();
  await page.getByRole("button", { name: "Run fixture research" }).click();
  await page.getByRole("button", { name: "Pause after this stage" }).click();
  await page
    .getByRole("button", { name: "Continue saved run" })
    .waitFor({ state: "visible" });
  await page.reload();
  await page.getByRole("button", { name: "Continue saved run" }).click();
  await page.waitForFunction(
    () => document.querySelector("#status")?.textContent === "SUCCESS",
  );
  await page.setViewportSize({ width: 390, height: 844 });
  await page.getByRole("button", { name: "Approve paper portfolio" }).waitFor();
  assert.equal(
    await page.evaluate(
      () => document.documentElement.scrollWidth <= innerWidth,
    ),
    true,
  );
  await page.screenshot({ path: out + "/mobile.png", fullPage: true });
  assert.deepEqual(errors, []);
  console.log(
    "Browser smoke passed: research, explicit approval, price-only updates, two saved replays and reload, rejection, quota retry, pause/resume, 390px monitoring layout, no page errors.",
  );
  await browser.close();
})().catch((e) => {
  console.error(e);
  process.exit(1);
});
