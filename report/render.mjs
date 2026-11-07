// Render a Rauchwerk Research HTML document to a Letter PDF with system Chrome, and report .body overflow per page.
// Usage: node render.mjs <file.html> [out.pdf] [--png]
// Needs playwright-core: resolved from the cwd's node_modules, $RR_PLAYWRIGHT, or ~/Code/crusoe/video/node_modules.
import { resolve, dirname, basename } from "node:path";
import { existsSync } from "node:fs";
import { homedir } from "node:os";
import { pathToFileURL } from "node:url";

const [, , input, outArg, ...flags] = process.argv;
if (!input) { console.error("usage: node render.mjs <file.html> [out.pdf] [--png]"); process.exit(1); }
const html = resolve(input);
const out = outArg && !outArg.startsWith("--") ? resolve(outArg) : html.replace(/\.html?$/, ".pdf");
const png = [outArg, ...flags].includes("--png");

const candidates = [
  process.env.RR_PLAYWRIGHT,
  resolve(process.cwd(), "node_modules/playwright-core/index.mjs"),
  resolve(homedir(), "Code/crusoe/video/node_modules/playwright-core/index.mjs"),
].filter(Boolean);
let chromium;
for (const c of candidates) if (existsSync(c)) { ({ chromium } = await import(pathToFileURL(c).href)); break; }
if (!chromium) { try { ({ chromium } = await import("playwright-core")); } catch {
  console.error("playwright-core not found. Run `npm i playwright-core` here or set RR_PLAYWRIGHT=/path/to/playwright-core/index.mjs"); process.exit(1); } }

const browser = await chromium.launch({ channel: "chrome", headless: true });
const page = await browser.newPage({ viewport: { width: 816, height: 1056 }, deviceScaleFactor: 2 });
await page.goto(pathToFileURL(html).href, { waitUntil: "networkidle" });
await page.evaluate(() => document.fonts.ready);
const over = await page.evaluate(() => [...document.querySelectorAll(".body")]
  .map((b, i) => [i + 1, b.scrollHeight - b.clientHeight]).filter(([, d]) => d > 0));
if (over.length) console.log("OVERFLOW (body #, px):", JSON.stringify(over));
await page.pdf({ path: out, format: "Letter", printBackground: true, preferCSSPageSize: true, margin: { top: 0, right: 0, bottom: 0, left: 0 } });
if (png) {
  const prev = resolve(dirname(out), basename(out).replace(/\.pdf$/, "") + "-preview.png");
  await page.screenshot({ path: prev, fullPage: true });
  console.log("preview:", prev);
}
await browser.close();
console.log("PDF:", out);

// Archive: every rendered report is copied to ~/Code/fieldreports (override with RR_ARCHIVE; RR_ARCHIVE=off disables).
const archive = process.env.RR_ARCHIVE ?? resolve(homedir(), "Code/fieldreports");
if (archive !== "off" && dirname(out) !== resolve(archive)) {
  const { mkdirSync, copyFileSync } = await import("node:fs");
  mkdirSync(archive, { recursive: true });
  const dest = resolve(archive, basename(out));
  copyFileSync(out, dest);
  console.log("archived:", dest);
}
