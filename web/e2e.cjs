"use strict";
const assert = require("node:assert/strict");
const fs = require("node:fs");
const http = require("node:http");
const { chromium } = require("playwright");

const routes = {
  "/": ["index.html", "text/html"],
  "/web/": ["web/index.html", "text/html"],
  "/web/app.js": ["web/app.js", "text/javascript"],
  "/myco_sentinel.py": ["myco_sentinel.py", "text/plain"]
};
const server = http.createServer((req, res) => {
  const route = routes[req.url];
  if (!route) { res.writeHead(404); res.end(); return; }
  res.setHeader("Content-Type", route[1] + "; charset=utf-8");
  fs.createReadStream(route[0]).pipe(res);
});

(async () => {
  await new Promise(resolve => server.listen(0, "127.0.0.1", resolve));
  const port = server.address().port;
  const browser = await chromium.launch({ headless: true });
  try {
    const page = await browser.newPage({ acceptDownloads: true });
    const errors = [];
    page.on("pageerror", error => errors.push(error.message));
    await page.goto("http://127.0.0.1:" + port + "/web/", { waitUntil: "domcontentloaded" });
    await page.waitForFunction(() => document.querySelector("#run") && !document.querySelector("#run").disabled, null, {
      timeout: 120000
    });
    await page.click("#run");
    await page.waitForFunction(() => document.querySelector("#output").textContent.includes('"combined_severity"'));
    let result = JSON.parse(await page.locator("#output").textContent());
    assert.equal(result.combined_severity, "HIGH");
    assert.deepEqual(result.tests_performed, ["BDG", "GM"]);

    await page.selectOption("#mode", "bdg");
    await page.fill("#bdg", "30");
    await page.click("#run");
    await page.waitForFunction(() => {
      const t = document.querySelector("#output").textContent;
      return t.includes('"category": "NEGATIVE"');
    });
    result = JSON.parse(await page.locator("#output").textContent());
    assert.equal(result.category, "NEGATIVE");

    const downloadPromise = page.waitForEvent("download");
    await page.click("#download");
    const download = await downloadPromise;
    assert.equal(download.suggestedFilename(), "fungal-antigen-interpretation.json");

    await page.fill("#bdg", "-1");
    assert.equal(await page.locator("#bdg").evaluate(input => input.checkValidity()), false);
    assert.equal(errors.length, 0, errors.join("; "));
    console.log("Browser Pyodide and triage/export smoke tests passed");
  } finally {
    await browser.close();
  }
})().catch(error => { console.error(error); process.exitCode = 1; })
  .finally(() => server.close());
