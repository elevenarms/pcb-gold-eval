// Render every frame of video/frames.html to video/stills/<name>.png (1920x1080; caption overlays transparent).
// Usage: node video/stills.mjs
import { createRequire } from "node:module";
import { readFileSync, mkdirSync } from "node:fs";
import { resolve, dirname } from "node:path";
import { fileURLToPath, pathToFileURL } from "node:url";
import { homedir } from "node:os";

const HERE = dirname(fileURLToPath(import.meta.url));
const require = createRequire(import.meta.url);
const { chromium } = require(process.env.RR_PLAYWRIGHT || resolve(dirname(fileURLToPath(import.meta.url)), "../node_modules/playwright-core"));
const rows = JSON.parse(readFileSync(resolve(HERE, "../forecast/forecast.json"))).hard.rows;
const FR = ["intro", "chapter1", "chapter2", "chapter3", "chapter4", "evidence", "tools", "result", "surface", "budget", "end",
            "cap_ddr5", "cap_si", "cap_m2", "cap_hdmi", "cap_orin"];
const out = resolve(HERE, "stills"); mkdirSync(out, { recursive: true });
const browser = await chromium.launch({ channel: "chrome", headless: true, args: ["--allow-file-access-from-files"] });
const page = await browser.newPage({ viewport: { width: 1920, height: 1080 } });
for (const f of FR) {
  const q = new URLSearchParams({ f, ...(f === "budget" ? { rows: JSON.stringify(rows) } : {}) });
  await page.goto(pathToFileURL(resolve(HERE, "frames.html")).href + "?" + q);
  await page.evaluate(() => document.fonts.ready);
  await page.waitForTimeout(250);
  await page.screenshot({ path: resolve(out, f + ".png"), omitBackground: f.startsWith("cap_") });
  console.log(f);
}
await browser.close();
