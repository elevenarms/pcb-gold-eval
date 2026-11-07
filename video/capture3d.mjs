// Capture the 3D board clips from the project page (site/) via its URL API -> video/clips/<name>.mp4 (1920x1080, 30 fps).
// Deterministic: Playwright's fake clock drives requestAnimationFrame, so every run gives the same frames.
// Usage: node video/capture3d.mjs [name ...]   (serves site/ itself; needs Chrome + playwright-core >= 1.45, ffmpeg)
import { createRequire } from "node:module";
import { readFileSync, mkdirSync, rmSync, writeFileSync } from "node:fs";
import { resolve, dirname } from "node:path";
import { fileURLToPath } from "node:url";
import { spawn, execFileSync } from "node:child_process";
import { homedir } from "node:os";

const HERE = dirname(fileURLToPath(import.meta.url));
const ROOT = resolve(HERE, "..");
const require = createRequire(import.meta.url);
const { chromium } = require(process.env.RR_PLAYWRIGHT || resolve(dirname(fileURLToPath(import.meta.url)), "../node_modules/playwright-core"));
const S = JSON.parse(readFileSync(resolve(HERE, "script.json")));
const want = process.argv.slice(2), FPS = 30;
const PORT = 8000 + Math.floor(Math.random() * 900);
const srv = spawn("python3", ["-m", "http.server", String(PORT), "--bind", "127.0.0.1"], { cwd: resolve(ROOT, "site"), stdio: "ignore" });
await new Promise(r => setTimeout(r, 900));
const out = resolve(HERE, "clips"); mkdirSync(out, { recursive: true });
const browser = await chromium.launch({ channel: "chrome", headless: true, args: ["--enable-gpu", "--use-angle=metal", "--ignore-gpu-blocklist"] });
try {
  for (const [name, c] of Object.entries(S.clips)) {
    if (want.length && !want.includes(name)) continue;
    const page = await browser.newPage({ viewport: { width: 1920, height: 1080 }, deviceScaleFactor: 1.5 });
    await page.clock.install({ time: new Date("2026-11-07T12:00:00Z") });
    const q = new URLSearchParams({ board: c.board, mode: c.mode, autorotate: "1", ui: "0", ...(c.explode != null ? { explode: String(c.explode) } : {}) });
    await page.goto(`http://127.0.0.1:${PORT}/index.html?${q}`);
    for (let i = 0; i < 600 && !(await page.evaluate(() => window.__ready === true)); i++) {
      await page.clock.runFor(100); await page.waitForTimeout(50);
    }
    await page.clock.runFor(1500);                    // settle: framing, explode animation, tone mapping
    const fr = resolve(out, "f_" + name); rmSync(fr, { recursive: true, force: true }); mkdirSync(fr);
    const n = Math.round(c.seconds * FPS);
    for (let i = 0; i < n; i++) {
      await page.clock.runFor(1000 / FPS);
      await page.screenshot({ path: resolve(fr, `f${String(i).padStart(4, "0")}.jpg`), type: "jpeg", quality: 93 });
    }
    await page.close();
    const z = c.zoom ?? 1.35;   // supersampled crop-zoom: 2880x1620 capture -> centre crop -> 1920x1080
    execFileSync("ffmpeg", ["-v", "error", "-y", "-framerate", String(FPS), "-i", resolve(fr, "f%04d.jpg"),
      "-vf", `crop=iw/${z}:ih/${z},scale=1920:1080:flags=lanczos`, "-c:v", "libx264", "-crf", "16",
      "-preset", "medium", "-pix_fmt", "yuv420p", resolve(out, name + ".mp4")]);
    rmSync(fr, { recursive: true, force: true });
    console.log(name, n, "frames");
  }
} finally { await browser.close(); srv.kill(); }
