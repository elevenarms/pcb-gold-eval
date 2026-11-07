// PCB Gold-Master Eval: 3D views of the Antmicro gold boards (KiCad 10 GLB exports, meshopt-compressed).
// URL API for headless capture: ?board=<id>&mode=<assembled|exploded|hs>&autorotate=1&ui=0[&explode=0..1]
import * as THREE from "three";
import { OrbitControls } from "three/addons/controls/OrbitControls.js";
import { GLTFLoader } from "three/addons/loaders/GLTFLoader.js";
import { MeshoptDecoder } from "three/addons/libs/meshopt_decoder.module.js";
import { RoomEnvironment } from "three/addons/environments/RoomEnvironment.js";

// Facts from data/meta/*.json (gold DRC/stats run in kicad/kicad:10.0.7) and the Antmicro inventory, 2026-11-07.
const BOARDS = {
  "signal-integrity-test-board": { name: "Signal-integrity test board", tier: "Easy", layers: 4, fps: 28, pairs: 2, vias: 252, len: "491 mm",
    fab: "Measured VNA data ships with gerber2ems", full: true },
  "m2-pcie-adapter": { name: "M.2 PCIe adapter", tier: "Easy", layers: 4, fps: 20, pairs: 18, vias: 92, len: "1,186 mm",
    fab: "Not established (render only)", full: true },
  "hdmi-mipi-bridge": { name: "HDMI to MIPI CSI-2 bridge", tier: "Easy", layers: 4, fps: 121, pairs: 36, vias: 312, len: "1,545 mm",
    fab: "Photographed (2018)", full: true },
  "jetson-orin-baseboard": { name: "Jetson Orin baseboard", tier: "Medium", layers: 8, fps: 680, pairs: 208, vias: 1345, len: "19,572 mm",
    fab: "Sold (CircuitHub 2024, System Designer 2026)", full: true },
  "rdimm-ddr5-tester": { name: "RDIMM DDR5 tester", tier: "Hard", layers: 12, fps: 797, pairs: 178, vias: 2665, len: "n/a",
    fab: "Clock trace compared with VNA (2025)", full: false },
};
const HS_LABEL = {
  "signal-integrity-test-board": "all nets", "m2-pcie-adapter": "PCIe data pairs", "hdmi-mipi-bridge": "HDMI pairs",
  "jetson-orin-baseboard": "PCIe nets", "rdimm-ddr5-tester": "DDR5 DQ / DQS nets",
};

const q = new URLSearchParams(location.search);
const state = {
  board: BOARDS[q.get("board")] ? q.get("board") : "hdmi-mipi-bridge",
  mode: ["assembled", "exploded", "hs"].includes(q.get("mode")) ? q.get("mode") : "assembled",
  explode: q.has("explode") ? +q.get("explode") : 0.6,
  rotate: q.has("autorotate") ? q.get("autorotate") === "1" : true,
};
if (q.get("ui") === "0") document.body.classList.add("noui");

// ---------------------------------------------------------------- renderer
const canvas = document.getElementById("c");
const stage = document.getElementById("stage");
// Touch screens (iOS Safari above all) get a lower pixel ratio and no preserveDrawingBuffer: both cost GPU memory,
// and iOS kills the WebGL context (or the tab) when a page uses too much. Capture mode (?ui=0) keeps the buffer.
const coarse = matchMedia("(pointer: coarse)").matches;
const capture = q.get("ui") === "0";
const renderer = new THREE.WebGLRenderer({ canvas, antialias: true, preserveDrawingBuffer: capture });
renderer.setPixelRatio(Math.min(devicePixelRatio, coarse ? 1.5 : 2));
renderer.toneMapping = THREE.ACESFilmicToneMapping;
renderer.toneMappingExposure = 0.95;
renderer.outputColorSpace = THREE.SRGBColorSpace;
const scene = new THREE.Scene();
scene.background = new THREE.Color(0x000000);
const pmrem = new THREE.PMREMGenerator(renderer);
scene.environment = pmrem.fromScene(new RoomEnvironment(), 0.04).texture;
scene.environmentIntensity = 0.55;
scene.add(new THREE.HemisphereLight(0xffffff, 0x1a1a1a, 0.9));
const key = new THREE.DirectionalLight(0xffffff, 1.6);
key.position.set(1, 2.2, 1.4);
scene.add(key);
const rim = new THREE.DirectionalLight(0xffffff, 0.5);
rim.position.set(-1.5, 0.8, -1.2);
scene.add(rim);

const camera = new THREE.PerspectiveCamera(32, 1, 0.1, 5000);
const controls = new OrbitControls(camera, canvas);
controls.enableDamping = true;
controls.dampingFactor = 0.08;
controls.autoRotateSpeed = 0.6;

// ---------------------------------------------------------------- scroll-safe interaction
// OrbitControls sets touch-action:none on the canvas and eats wheel events, so a viewer this tall traps page
// scrolling (one-finger swipes rotate instead of scroll on iOS; trackpad scroll zooms on desktop Safari).
// The viewer therefore starts passive: touch devices tap to explore (and tap Done to give scrolling back);
// desktop drags to orbit at any time but only zooms after a click inside the viewer, until the pointer leaves.
const hint = document.getElementById("hint");
const done = document.getElementById("done");
function setActive(on) {
  stage.classList.toggle("active", on);
  if (coarse) {
    controls.enabled = on;
    canvas.style.touchAction = on ? "none" : "auto";
    hint.textContent = on ? "Drag to orbit · pinch to zoom" : "Tap to explore the board";
  } else {
    controls.enableZoom = on;
    hint.textContent = on ? "Drag to orbit · scroll to zoom" : "Drag to orbit · click to zoom";
  }
}
if (coarse) {
  stage.addEventListener("click", (e) => { if (!stage.classList.contains("active") && e.target !== done) setActive(true); });
  done.addEventListener("click", (e) => { e.stopPropagation(); setActive(false); });
} else {
  canvas.addEventListener("click", () => setActive(true));
  stage.addEventListener("pointerleave", () => setActive(false));
}
setActive(capture);

const loader = new GLTFLoader().setMeshoptDecoder(MeshoptDecoder);
const cache = new Map();
const load = (url) => {
  if (!cache.has(url)) cache.set(url, loader.loadAsync(url).then((g) => g.scene));
  return cache.get(url).then((s) => s.clone(true));
};

// ---------------------------------------------------------------- materials (copper keeps its own tone; frame stays monochrome)
const MAT = {
  copper: new THREE.MeshStandardMaterial({ color: 0xc8793c, metalness: 0.9, roughness: 0.32 }),
  copperHot: new THREE.MeshStandardMaterial({ color: 0xd9894a, metalness: 0.6, roughness: 0.3, emissive: 0xff8a3a, emissiveIntensity: 0.9, transparent: true, opacity: 1 }),
  mask: new THREE.MeshStandardMaterial({ color: 0x0c0c0c, metalness: 0, roughness: 0.55, transparent: true, opacity: 0.5, depthWrite: false }),
  silk: new THREE.MeshStandardMaterial({ color: 0xe9e9e5, metalness: 0, roughness: 0.8 }),
  body: new THREE.MeshStandardMaterial({ color: 0x2a2620, metalness: 0, roughness: 0.85 }),
  ghost: new THREE.MeshStandardMaterial({ color: 0x3a3a3a, metalness: 0, roughness: 1, transparent: true, opacity: 0.1, depthWrite: false }),
};
function role(m) {
  const c = m.color, a = m.opacity;
  if (c.r > 0.5 && c.b < 0.15) return "copper";
  if (c.r > 0.9 && c.g > 0.9 && c.b > 0.9) return "silk";
  if (c.r < 0.1 && c.g < 0.1 && a < 0.95) return "mask";
  return "body";
}

// ---------------------------------------------------------------- scene assembly
let root = null, layers = [], token = 0, unit = 1;
async function show() {
  const my = ++token;
  const id = state.board, b = BOARDS[id];
  document.getElementById("loading").style.display = "block";
  const parts = [];
  if (state.mode === "hs") {
    parts.push(load(`assets/glb/${id}-hs.glb`).then((s) => style(s, "hot")));
    parts.push(load(`assets/glb/${b.full ? id : id + "-body"}.glb`).then((s) => style(s, "ghost")));
  } else if (b.full) {
    parts.push(load(`assets/glb/${id}.glb`).then((s) => style(s, "real")));
  } else {
    parts.push(load(`assets/glb/${id}-hs.glb`).then((s) => style(s, "real")));
    parts.push(load(`assets/glb/${id}-body.glb`).then((s) => style(s, "ghost")));
  }
  const groups = await Promise.all(parts);
  if (my !== token) return;
  if (root) {
    scene.remove(root);
    // On phones, free the previous board's GPU buffers instead of keeping every board resident.
    if (coarse) {
      root.traverse((o) => o.isMesh && o.geometry.dispose());
      for (const u of cache.keys()) if (!u.includes(`/${id}`)) cache.delete(u);
    }
  }
  root = new THREE.Group();
  groups.forEach((g) => root.add(g));
  root.scale.setScalar(1000); // metres -> millimetres
  scene.add(root);
  root.updateMatrixWorld(true);
  // layers: every mesh ranked by its world-space height (board normal = +y)
  const meshes = [];
  root.traverse((o) => o.isMesh && meshes.push(o));
  const centres = meshes.map((m) => new THREE.Box3().setFromObject(m).getCenter(new THREE.Vector3()).y);
  const uniq = [...new Set(centres.map((y) => y.toFixed(3)))].sort((a, b) => a - b);
  const mid = (uniq.length - 1) / 2;
  layers = meshes.map((m, i) => ({ m, base: m.position.y, rank: uniq.indexOf(centres[i].toFixed(3)) - mid, s: m.parent.scale.y * 1000 }));
  fit(state.mode === "hs" ? groups[0] : root);
  applyExplode();
  facts();
  document.getElementById("loading").style.display = "none";
}
function style(s, kind) {
  s.traverse((o) => {
    if (!o.isMesh) return;
    const r = role(o.material);
    if (kind === "ghost") o.material = r === "body" ? MAT.ghost : MAT.ghost;
    else if (kind === "hot") o.material = MAT.copperHot;
    else o.material = MAT[r];
    o.renderOrder = kind === "ghost" ? 0 : kind === "hot" ? 3 : r === "mask" ? 2 : 1;
  });
  return s;
}
function fit(target) {
  const all = new THREE.Box3().setFromObject(root).getSize(new THREE.Vector3());
  unit = Math.max(all.x, all.z);
  const box = new THREE.Box3().setFromObject(target);
  const size = box.getSize(new THREE.Vector3()), c = box.getCenter(new THREE.Vector3());
  root.position.sub(c);
  const d = Math.max(size.x, size.z) * (state.mode === "hs" ? 1.35 : 1.95);
  camera.position.set(d * 0.55, d * 0.62, d * 0.72);
  camera.near = unit / 100; camera.far = unit * 50; camera.updateProjectionMatrix();
  controls.target.set(0, 0, 0);
  controls.update();
}
function applyExplode() {
  const k = state.mode === "exploded" ? state.explode : 0;
  for (const L of layers) L.m.position.y = L.base + (L.rank * k * unit * 0.16) / L.s;
}

// ---------------------------------------------------------------- UI
const sel = document.getElementById("board");
for (const [id, b] of Object.entries(BOARDS)) sel.add(new Option(`${b.name} · ${b.tier}`, id));
sel.value = state.board;
sel.onchange = () => { state.board = sel.value; show(); sync(); };
const modeBtns = [...document.querySelectorAll(".modes button")];
modeBtns.forEach((btn) => (btn.onclick = () => { state.mode = btn.dataset.mode; show(); sync(); }));
const ex = document.getElementById("explode");
ex.value = state.explode;
ex.oninput = () => { state.explode = +ex.value; applyExplode(); };
const rot = document.getElementById("rotate");
rot.checked = state.rotate;
rot.onchange = () => { state.rotate = rot.checked; };
function sync() {
  modeBtns.forEach((b) => b.classList.toggle("on", b.dataset.mode === state.mode));
  document.getElementById("explodeWrap").classList.toggle("off", state.mode !== "exploded");
  const notes = {
    assembled: "Human-routed copper as fabricated. Copper keeps its own tone; solder mask is drawn translucent so the routing shows through.",
    exploded: "Each exported mesh separated by height: outer copper, mask, silkscreen and the board body pulled apart.",
    hs: `Only the high-speed nets (${HS_LABEL[state.board]}), lit, over a ghost of the board. This is the copper the eval scores for skew, matching and impedance width.`,
  };
  document.getElementById("modeNote").textContent = notes[state.mode];
}
function facts() {
  const id = state.board, b = BOARDS[id];
  const rows = [
    ["Repo", `<a href="https://github.com/antmicro/${id}" target="_blank" rel="noopener">antmicro/${id}</a>`],
    ["Tier", b.tier], ["Copper layers", b.layers], ["Footprints", b.fps.toLocaleString()],
    ["Diff-pair nets", b.pairs], ["Gold vias", b.vias.toLocaleString()], ["Gold copper", b.len], ["Built", b.fab],
  ];
  document.getElementById("facts").innerHTML = rows.map(([k, v]) => `<dt>${k}</dt><dd>${v}</dd>`).join("");
}

function resize() {
  const w = stage.clientWidth, h = stage.clientHeight;
  renderer.setSize(w, h, false);
  camera.aspect = w / h;
  camera.updateProjectionMatrix();
}
new ResizeObserver(resize).observe(stage);
resize();
const loop = () => {
  controls.autoRotate = state.rotate;
  controls.update();
  renderer.render(scene, camera);
};
renderer.setAnimationLoop(loop);
// Stop rendering while the viewer is off screen (keeps scrolling smooth on phones) and hand scrolling back.
new IntersectionObserver(([e]) => {
  renderer.setAnimationLoop(e.isIntersecting ? loop : null);
  if (!e.isIntersecting && !capture) setActive(false);
}).observe(stage);
// iOS drops the WebGL context under memory pressure; say so instead of leaving a black box.
canvas.addEventListener("webglcontextlost", (e) => {
  e.preventDefault();
  const l = document.getElementById("loading");
  l.textContent = "3D view paused: the browser ran out of graphics memory. Reload, or pick a smaller board.";
  l.style.display = "block";
});
canvas.addEventListener("webglcontextrestored", () => { document.getElementById("loading").textContent = "Loading board…"; cache.clear(); show(); });
sync();
show().then(() => { window.__ready = true; });
