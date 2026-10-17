// Optional local browser audit; uses the same preinstalled runtime as smoke.cjs.
const { chromium } = require(process.env.PLAYWRIGHT_MODULE || "playwright");
const assert = require("node:assert/strict");
const fs = require("node:fs");
const base = process.env.UI_BASE_URL || "http://127.0.0.1:8772";
const out = process.env.UI_SCREENSHOT_DIR || "data/ui-redesign-audit";

(async () => {
  fs.mkdirSync(out, { recursive: true });
  const browser = await chromium.launch({ headless: true });
  try {
    const page = await browser.newPage({
      viewport: { width: 1440, height: 1000 },
      reducedMotion: "reduce",
    });
    const pageErrors = [];
    page.on("pageerror", (error) => pageErrors.push(error.message));
    let posts = 0;
    page.on("request", (request) => {
      if (request.method() === "POST") posts++;
    });
    let releaseSettings;
    const settingsGate = new Promise((resolve) => {
      releaseSettings = resolve;
    });
    await page.route("**/api/settings", async (route) => {
      await settingsGate;
      await route.continue();
    });
    await page.goto(base, { waitUntil: "domcontentloaded" });
    await page
      .getByText("Loading local fixture workspace…", { exact: true })
      .waitFor();
    await page.screenshot({ path: out + "/loading.png" });
    releaseSettings();
    await page.getByRole("button", { name: "Load demo policy" }).waitFor();
    await page.unroute("**/api/settings");
    await page.keyboard.press("Tab");
    assert.equal(
      await page.evaluate(() => document.activeElement.textContent),
      "Skip to workspace",
    );
    assert.notEqual(
      await page
        .locator(".skip-link")
        .evaluate((el) => getComputedStyle(el).outlineStyle),
      "none",
    );
    await page.keyboard.press("Enter");
    assert.equal(
      await page.evaluate(() => document.activeElement.id),
      "main-content",
    );
    await page.getByRole("button", { name: "Run fixture research" }).click();
    assert.equal(posts, 0, "Invalid form must not dispatch a run");
    assert.equal(
      await page.evaluate(() => document.activeElement.id),
      "field-capital",
    );
    assert.equal(
      await page.locator("#field-capital").getAttribute("aria-invalid"),
      "true",
    );
    assert.equal(
      await page
        .getByText("Selection rules & freshness", { exact: true })
        .evaluate((el) => el.parentElement.open),
      true,
    );
    await page.getByRole("button", { name: "Load demo policy" }).click();
    await page.screenshot({
      path: out + "/configure-desktop.png",
      fullPage: true,
    });

    // A backend policy failure remains a backend failure; presentation provides focus and feedback.
    await page.locator("#field-max_asset_weight").fill("0.01");
    assert.equal(
      await page.evaluate(() => {
        const event = new Event("beforeunload", { cancelable: true });
        window.dispatchEvent(event);
        return event.defaultPrevented;
      }),
      true,
      "Edited policy needs an unsaved-change guard",
    );
    await page.getByRole("button", { name: "Run fixture research" }).click();
    await page.locator("#workspace-error").waitFor();
    assert.equal(
      await page.evaluate(() => document.activeElement.id),
      "workspace-error",
    );
    assert.equal(
      await page.locator("#workspace-error").getAttribute("role"),
      "alert",
    );
    await page.screenshot({ path: out + "/policy-error.png", fullPage: true });
    await page.getByRole("button", { name: "Load demo policy" }).click();
    await page.getByRole("button", { name: "Run fixture research" }).click();
    await page.waitForFunction(
      () => document.querySelector("#status")?.textContent === "SUCCESS",
    );
    const runId = await page.evaluate(() =>
      localStorage.getItem("agent-of-odds-run"),
    );
    await page.locator("#reports summary").first().click();
    await page.getByText("Cited passage ·").first().click();
    await page.screenshot({
      path: out + "/review-desktop.png",
      fullPage: true,
    });
    const submit = page.getByRole("button", {
      name: "Approve paper portfolio",
    });
    await submit.waitFor();
    assert.equal(await submit.isDisabled(), true);
    await page
      .getByLabel(
        "I approve this exact synthetic replay and its stated fill and fee conventions.",
      )
      .check();
    await submit.click();
    await page.getByTestId("paper-approved").waitFor();
    await page.getByRole("button", { name: "Update prices only" }).waitFor();
    await page.getByRole("button", { name: "Update prices only" }).click();
    await page.getByTestId("valuation-result").waitFor();
    await page
      .getByTestId("paper-ledger")
      .screenshot({ path: out + "/paper-desktop.png" });

    const widths = [320, 390, 640, 768, 834, 1024, 1440, 1920];
    for (const width of widths) {
      await page.setViewportSize({ width, height: 1000 });
      assert.equal(
        await page.evaluate(
          () => document.documentElement.scrollWidth <= innerWidth,
        ),
        true,
        `document overflow at ${width}px`,
      );
      const unnamed = await page
        .locator("input,select")
        .evaluateAll((elements) =>
          elements
            .filter(
              (el) =>
                !el.name ||
                (!el.labels?.length && !el.getAttribute("aria-label")),
            )
            .map((el) => el.outerHTML),
        );
      assert.deepEqual(
        unnamed,
        [],
        "Every form control needs a name and accessible label",
      );
      const targets = await page
        .locator(
          "button,.nav-inner a,.company-option,.approval-consent,summary",
        )
        .evaluateAll((elements) =>
          elements
            .filter(
              (el) =>
                el.getClientRects().length &&
                el.getBoundingClientRect().height < 43.9,
            )
            .map((el) => el.textContent),
        );
      assert.deepEqual(targets, [], `touch targets below 44px at ${width}px`);
      for (const anchor of ["#configure", "#review", "#saved-runs"])
        assert.equal(await page.locator(anchor).count(), 1);
      await page
        .getByTestId("monitoring")
        .screenshot({ path: out + `/monitoring-${width}.png` });
    }
    await page.setViewportSize({ width: 320, height: 1000 });
    const originalMetric = await page
      .locator(".metric dd")
      .first()
      .textContent();
    await page
      .locator(".metric dd")
      .first()
      .evaluate((el) => {
        el.textContent = "$1,234,567,890,123.45";
      });
    assert.equal(
      await page.evaluate(
        () => document.documentElement.scrollWidth <= innerWidth,
      ),
      true,
      "Long numeric display must not overflow the page",
    );
    await page
      .locator(".metric dd")
      .first()
      .evaluate((el, value) => {
        el.textContent = value;
      }, originalMetric);
    await page.setViewportSize({ width: 1440, height: 1000 });
    const beforeOpen = posts;
    await page.getByLabel("Saved local run").selectOption(runId);
    await page.getByRole("button", { name: "Open saved run" }).click();
    await page.getByTestId("paper-approved").waitFor();
    assert.equal(
      posts,
      beforeOpen,
      "Opening a saved run must remain read-only",
    );
    await page.getByRole("button", { name: "Load demo policy" }).click();
    await page.locator("[name=scenario]").selectOption("missing_evidence");
    await page.getByRole("button", { name: "Run fixture research" }).click();
    await page.waitForFunction(
      () =>
        document.querySelector("#start") &&
        !document.querySelector("#start").disabled,
    );
    assert.notEqual(await page.locator("#status").textContent(), "SUCCESS");
    assert.equal(await page.locator("#allocation tbody tr").count(), 0);
    assert.equal(await page.getByTestId("paper-ledger").count(), 0);
    await page.screenshot({
      path: out + "/missing-evidence.png",
      fullPage: true,
    });

    // Deliberate local HTTP failure verifies the initial connection error screen.
    const failure = await browser.newPage();
    await failure.route("**/api/settings", (route) =>
      route.fulfill({
        status: 503,
        contentType: "application/json",
        body: JSON.stringify({
          status: "unavailable",
          reason: "Local fixture settings unavailable",
        }),
      }),
    );
    await failure.goto(base);
    await failure.getByRole("button", { name: "Reload workspace" }).waitFor();
    await failure.screenshot({ path: out + "/connection-error.png" });
    assert.equal(
      await failure.locator("#workspace-error").getAttribute("role"),
      "alert",
    );
    assert.deepEqual(pageErrors, []);
    const result = {
      status: "passed",
      base,
      widths,
      checks: [
        "loading/connection error",
        "keyboard skip link/focus",
        "inline native validation/hidden required fields",
        "backend policy error focus",
        "unsaved policy guard",
        "reports/citations",
        "approval/valuation",
        "read-only saved run",
        "missing evidence suppresses proposal",
        "labels/names",
        "44px interaction targets",
        "no document overflow",
        "long numeric display containment",
        "no page errors",
      ],
      limits: [
        "Chromium only; no Lighthouse/axe package installed",
        "Reduced-motion context; no animation performance score claimed",
        "Synthetic fixture approvals only",
      ],
    };
    fs.writeFileSync(
      out + "/results.json",
      JSON.stringify(result, null, 2) + "\n",
    );
    console.log(JSON.stringify(result));
  } finally {
    await browser.close();
  }
})().catch((error) => {
  console.error(error);
  process.exit(1);
});
