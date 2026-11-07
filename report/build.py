# Field report: PCB Gold-Master Eval (Rauchwerk Research, 10 Letter pages). Data-driven: reads ../data and ../forecast.
import glob, json, os, statistics, tomllib
D = os.path.dirname(os.path.abspath(__file__))
R = os.path.dirname(D)
DOC, DATE = "Field Report · PCB Gold-Master Eval", "November 2026"
TOT = 10
exec(open(os.path.join(D, "helpers.py")).read())
PAGES = []


def page(chap, body):
    PAGES.append((chap, body))


def render_pages():
    out = []
    for i, (chap, body) in enumerate(PAGES, 2):
        out.append(f'''<section class="page">
<div class="topline"><span>{chap}</span><span>{DOC}</span></div>
<div class="foot"><span class="bug"><img src="assets/mark-black.png">Rauchwerk Research</span><span>Dave Rauchwerk · {DATE}</span><span>{i:02d} / {TOT:02d}</span></div>
<div class="body">{body}</div></section>''')
    return "".join(out)


def fig(src, cap="", h=None, fit="cover", pos="center", dark=False):
    st = f"height:{h};" if h else ""
    return f'<figure class="f{" fd" if dark else ""}"><img src="m/{src}" style="{st}object-fit:{fit};object-position:{pos}">{f"<figcaption>{cap}</figcaption>" if cap else ""}</figure>'


def ex(n, title):
    return f'<div class="exk"><span>Exhibit {n}</span>{title}</div>'


def side(kicker, title, body):
    return f'<div class="side"><span class="kicker">{kicker}</span><h3>{title}</h3>{body}</div>'


# ------------------------------------------------------------------ data
BOARDS = tomllib.load(open(os.path.join(R, "boards.toml"), "rb"))
META = {b: json.load(open(os.path.join(R, f"data/meta/{b}.json"))) for b in BOARDS}
BASE = [json.load(open(f)) for f in glob.glob(os.path.join(R, "data/baselines/*.json"))]
FC = json.load(open(os.path.join(R, "forecast/forecast.json")))
ORACLE = [json.load(open(f)) for f in glob.glob(os.path.join(R, "jobs/oracle-all/*/verifier/reward.json"))]
best = {}
for r in BASE:
    if r.get("reward") is not None and (r["board"] not in best or r["reward"] > best[r["board"]]["reward"]):
        best[r["board"]] = r
SHORT = {"signal-integrity-test-board": "SI test board", "m2-pcie-adapter": "M.2 PCIe adapter", "hdmi-mipi-bridge": "HDMI–MIPI bridge",
         "gmsl-deserializer": "GMSL deserializer", "jetson-orin-baseboard": "Jetson Orin baseboard", "rdimm-ddr4-tester": "RDIMM DDR4 tester",
         "sodimm-ddr5-tester": "SO-DIMM DDR5 tester", "rdimm-ddr5-tester": "RDIMM DDR5 tester"}
HS = {"signal-integrity-test-board": "50 Ω test lines", "m2-pcie-adapter": "PCIe x4", "hdmi-mipi-bridge": "HDMI, CSI-2", "gmsl-deserializer": "GMSL2, CSI-2",
      "jetson-orin-baseboard": "PCIe, USB 3, CSI-2, HDMI, GbE", "rdimm-ddr4-tester": "DDR4 RDIMM", "sodimm-ddr5-tester": "DDR5 SO-DIMM", "rdimm-ddr5-tester": "DDR5 RDIMM"}
FAB = {"measured-VNA-data": "VNA data shipped", "unknown": "not documented", "photo": "photo in repo", "sold": "sold (CircuitHub)",
       "published-use": "Rowhammer research", "VNA-comparison": "VNA vs simulation"}
n_base = len(BASE)
m2 = best.get("m2-pcie-adapter", {})
si = best.get("signal-integrity-test-board", {})
mean_base = statistics.mean(r["reward"] for r in best.values()) if best else 0

# ------------------------------------------------------------------ cover
cover = f'''<section class="page dark">
<img src="assets/rauchwerk-white.png" style="position:absolute;left:.6in;top:.6in;height:1.15in">
<div style="position:absolute;right:.6in;top:.62in;text-align:right" class="kicker">Field report · {DATE}<br>Literature review · Eval · Forecast</div>
<img src="m/orin-exploded.png" style="position:absolute;left:0;right:0;top:1.9in;width:8.5in;height:4.6in;object-fit:cover;object-position:center 52%">
<div class="cover-text" style="bottom:1.45in">
  <span class="kicker">PCB Gold-Master Eval</span>
  <h1 style="font-size:40pt">Routed is not the same as right</h1>
  <p class="lead" style="color:#d6d6d2;max-width:6.9in">Self-improving machine learning for high-frequency PCB placement and routing: what the literature proves, which open-source tools can carry it, a new eval that scores machine routing against eight fabricated Antmicro boards, and what an outcome costs in dollars and hours.</p>
  <span class="kicker" style="color:#a4a4a2">Dave Rauchwerk · Rauchwerk Research</span>
</div>
<div class="cover-chaps"><div><b>1</b>The evidence</div><div><b>2</b>The tools</div><div><b>3</b>The eval</div><div><b>4</b>The forecast</div></div>
</section>'''

# ------------------------------------------------------------------ 02 executive summary
page("00 · At a glance", f'''
<div class="kicker">At a glance · The answer, in one line</div>
<h2>Machines can connect a board. Nothing open yet routes it the way its engineers did, and the eval to prove it did not exist.</h2>
<p class="lead">The literature has no learned PCB method that optimises impedance, skew or length matching; only vendors claim it. So the work started with the measuring stick: a Harbor eval that strips the copper from eight fabricated, Apache-licensed Antmicro boards and scores machine routing against the human original.</p>
<div class="tiles">
 <div class="tile"><b>8</b><span>gold-master boards, 4–12 copper layers, 20–797 parts, pinned by commit and sha256</span></div>
 <div class="tile"><b>{m2.get("reward", 0):.2f}</b><span>Freerouting on the M.2 PCIe adapter: {m2.get("completion", 0)*100:.0f}% routed, {m2.get("pair_skew", 0)*9:.0f} of 9 pairs in skew tolerance</span></div>
 <div class="tile"><b>1.00</b><span>oracle score: the human copper scores itself perfectly through Harbor</span></div>
 <div class="tile"><b>21×</b><span>CPU-hours RL used over simulated annealing in the only independent chip-placement rerun, for equal or worse results</span></div>
 <div class="tile"><b>$250</b><span>to $300 per LLM-evolved placer run (HELIX, ICCAD 2026) for a 4.5–5.6% wirelength gain</span></div>
 <div class="tile"><b>0</b><span>open PCB benchmarks with a signal-integrity metric before this one</span></div>
</div>
<h3 style="margin-top:4pt">Five findings</h3>
<ol class="recs">
 <li><div><b>Search beats reinforcement learning per dollar, so far.</b><span>Evolutionary and tree search won at hour scale in chip placement; RL’s headline result has no independent reproduction.</span></div></li>
 <li><div><b>Completion hides the high-frequency failure.</b><span>The open router finishes 72–96% of simpler boards, stalls at 18% on a BGA board, and misses the skew, length and width targets everywhere.</span></div></li>
 <li><div><b>The evaluator is the bottleneck, not the optimiser.</b><span>Proxy metrics barely predict final quality (Kendall τ 0.05–0.40); full-wave checks cost minutes per structure.</span></div></li>
 <li><div><b>Compute is cheap; wall clock and fidelity are not.</b><span>A medium board’s routing candidate costs about one cent on CPU. Budgets matter only for RL, LLM evolution and full-wave EM on DDR-class boards.</span></div></li>
 <li><div><b>Gold masters turn opinion into a number.</b><span>Antmicro’s length and skew targets exist only in their copper; the eval extracts them and makes every claim testable.</span></div></li>
</ol>''')

# ------------------------------------------------------------------ 03 the question
v3 = '''<img src="m/v3curve.png" style="width:100%;display:block;border-bottom:1pt solid var(--rule);padding-bottom:3pt">'''
page("Context · The question", f'''
<div class="kicker">The question</div>
<h2>Can self-improving machine learning route a high-frequency board as well as the engineers who shipped it?</h2>
<p class="lead">The claim under review: reinforcement learning, evolutionary algorithms and deep networks that learn to place and route boards for high-frequency constraints, without hand-coded heuristics. Testing it needs three things the field lacks: graded evidence, an open tool stack, and a benchmark with physics in the score.</p>
{ex(1, "The starting point: Zine Machine v3, routed by an agent with open tools")}
{v3}
<p class="cap">Best-so-far unconnected items on the v3 main board, 6 Nov 2026, from the Backplane transcripts. Ninety-two per cent of connections were made in 22 minutes; the last one took 2.5 hours. The 499 ceiling is an artefact: <code>kicad-cli</code>’s DRC report stops listing unconnected items at 499, a cap found while building this eval.</p>
<div class="grid3" style="margin-top:10pt;align-items:start">
{side("Why a new base case", "The project board is a weak test", "<p>v3’s fastest interface is USB 2.0 and its parallel display bus runs near 30 MHz. It has no DDR, no PCIe and one routed history. A credible test needs boards with real high-speed interfaces, routed by professionals, built and used.</p>")}
{side("Scope", "Open source only", "<p>Every tool, solver and dataset here is open source and runs headless in a pinned container. Commercial routers (Quilter, DeepPCB, Allegro X AI) appear only as context, graded as vendor claims.</p>")}
{side("Method", "Four parallel workstreams", "<p>A graded literature review (30 sources), an inventory of 40 open tools with live repo data, an eval built and validated in Harbor, and a compute forecast with every parameter tagged by source.</p>")}
</div></div>''')

# ------------------------------------------------------------------ 04 ch1 literature
LIT = [
    ("Chip RL placement (Google CT / AlphaChip)", "Nature 2021, 2024", "B, disputed", "Rerun: 19,068 CPU-h vs 896 for SA; SA best proxy in 6 of 9; no published successful reproduction"),
    ("Independent reassessment (Cheng, Kahng et al.)", "ISPD 2023, TCAD", "B", "Proxy cost vs routed WL Kendall τ 0.40; vs WNS 0.05"),
    ("WireMask-BBO (evolutionary)", "NeurIPS 2023", "A−", "73% of gain in first 300 of 2,000 evals; CPU only"),
    ("EfficientPlace (tree search + RL)", "ICML 2024", "B", "0.5k→1k steps doubles time for 0.3–6.6% more"),
    ("DREAMPlace (GPU analytical)", "DAC 2019", "A", ">30× faster than RePlAce at equal quality"),
    ("RL PCB placement (Vassallo, Bajada)", "DATE 2024", "B", "−17 to −21% routed WL vs SA; compute not reported"),
    ("PCBWorld (RL routing, 679 boards)", "KDD wkshp 2026", "C", "PPO 0.45 vs Freerouting 0.78 clean-pass on harder boards; no SI metric"),
    ("FunSearch (LLM program search)", "Nature 2024", "B", "~10⁶ samples; 4 of 140 runs hit the best result"),
    ("HELIX (LLM-evolved placer)", "ICCAD 2026", "B", "$250–300, ~120 candidates per run; −4.5% HPWL, −5.6% routed WL"),
    ("SI surrogates (eye, PDN, EM)", "preprints 2021–26", "C", "R² >0.99; 10³–10⁵× faster; NRMSE 10.2→6.6% from 10k→100k samples"),
    ("Quilter, DeepPCB", "vendor", "D", "Claims of DDR/diff-pair handling; no peer-reviewed results"),
]
page("01 · The evidence", f'''
{chead(1, "Chapter 1 of 4 · What the literature proves", "The evidence favours search, surrogates and honest evaluators over end-to-end RL")}
{ex(2, "Thirty sources graded; the eleven that decide the question")}
<table class="sm"><tr><th>Line of work</th><th>Venue</th><th>Grade</th><th>Decisive number</th></tr>
{"".join(f"<tr><td>{a}</td><td>{b}</td><td>{c}</td><td>{d}</td></tr>" for a, b, c, d in LIT)}</table>
<p class="cap">Grades: A peer-reviewed and independently reproduced · B peer-reviewed · C preprint or non-archival · D vendor claim. Every citation was checked against arXiv, a DOI or the publisher; full bibliography in the companion paper.</p>
<div class="grid2" style="margin-top:6pt;gap:10pt">
 <div class="card"><h3>Proven</h3>GPU analytical placement is fast and good. Evolutionary and tree search beat pure RL at hour scale. LLM-evolved heuristics give single-digit gains at a known price. Surrogates reproduce SI metrics in narrow parameter spaces.</div>
 <div class="card"><h3>Not proven, and the gap</h3>“Superhuman” RL placement; any learned PCB router that beats rule-based routers on real boards; any method that optimises high-frequency SI end to end. No PCB benchmark scores signal integrity, so none of it can yet be shown.</div>
</div>
<div class="exk" style="margin-top:8pt"><span>Five numbers</span>that carry the forecast in Chapter 4</div>
<div class="five">
 <div><b>21×</b>more CPU-hours for RL than simulated annealing, for equal or worse placements</div>
 <div><b>73%</b>of WireMask-EA’s gain inside its first 300 of 2,000 evaluations</div>
 <div><b>0.4 vs 2.8%</b>best-of-120 single shots vs an evolutionary loop, same budget (HELIX)</div>
 <div><b>τ 0.05</b>rank correlation between proxy cost and timing slack: proxies mislead</div>
 <div><b>10³–10⁵×</b>surrogate speedup over SI simulation once trained on 10k–100k samples</div>
</div>
</div>''')

# ------------------------------------------------------------------ 06 ch2 tools
TOOLS = [
    ("Routing", "KiCadRoutingTools", "MIT", "4", "1", "5", "5", "Rust A*; diff pairs, length/time matching; 0.65 s small boards"),
    ("Routing", "Freerouting 2.5", "GPL-3", "3", "1", "4", "5", "Reference autorouter; single-threaded router; varies by run"),
    ("Routing", "KiCad 10 IPC API / kicad-cli", "GPL-3", "3", "1", "3", "5", "DRC, export; headless API arrives in KiCad 11"),
    ("Placement", "DREAMPlace", "BSD-3", "5", "5", "3", "1", "GPU analytical placer; needs a PCB adapter"),
    ("EM / SI", "openEMS + gerber2ems", "GPL / Apache", "3", "3", "4", "5", "Gerbers to S-parameters; GPU engine unreleased"),
    ("EM / SI", "Palace (AWS)", "Apache-2", "5", "4", "2", "1", "FEM, multi-GPU; needs a gmsh pipeline"),
    ("EM / SI", "gprMax / FDTDX", "GPL / MIT", "5", "5", "4", "1", "Fast GPU FDTD; no PCB ports or import"),
    ("EM / SI", "scikit-rf, PyBERT", "BSD-3", "4", "1", "5", "2", "S-parameter cascade; eye and BER"),
    ("Optimiser", "evosax / EvoTorch", "Apache-2", "5", "5", "5", "1", "Batched CMA-ES and NES on GPU"),
    ("Optimiser", "pymoo, Optuna, BoTorch", "Apache / MIT", "4", "1–4", "5", "1", "Multi-objective and multi-fidelity search"),
    ("Learning", "PufferLib, SB3, PyG", "MIT", "4", "4", "5", "1", "PPO and graph encoders"),
    ("Self-improving", "OpenEvolve, ShinkaEvolve", "Apache-2", "3", "–", "4", "1", "LLM rewrites router cost functions"),
]
page("02 · The tools", f'''
{chead(2, "Chapter 2 of 4 · The open-source stack, scored", "The open stack is complete except for one piece: fast physics")}
{ex(3, "Open-source tools scored 1–5 on performance, GPU acceleration, scriptability and PCB integration (repo data 7 Nov 2026)")}
<table class="sm score"><tr><th>Layer</th><th>Tool</th><th>Licence</th><th>Perf</th><th>GPU</th><th>Script</th><th>PCB</th><th>Note</th></tr>
{"".join(f"<tr><td>{a}</td><td><b>{b}</b></td><td>{c}</td><td class=c>{d}</td><td class=c>{e}</td><td class=c>{f}</td><td class=c>{g}</td><td>{h}</td></tr>" for a, b, c, d, e, f, g, h in TOOLS)}</table>
<p class="cap">Scores from primary sources (READMEs, papers, release notes). GPL tools are called as separate processes so the rest of the stack stays permissive. 28 further tools were reviewed and left out: inactive, chip-only or no PCB path.</p>
<div class="grid3" style="margin-top:8pt">
 <div class="card"><h3>Fast loop</h3>KiCadRoutingTools as the inner router, Freerouting as the reference, analytic impedance tables and skew/length checks as the cheap score. Many single-threaded processes, not one big machine.</div>
 <div class="card"><h3>Physics</h3>openEMS through gerber2ems is the only open path from a PCB to S-parameters. Its GPU engine landed on master in October 2026 with no published speedups: benchmark it before budgeting GPUs.</div>
 <div class="card"><h3>Self-improvement</h3>evosax or pymoo for routing recipes; OpenEvolve for router code; BoTorch to decide when a candidate earns a full-wave check. RL last, if at all.</div>
</div>''')

# ------------------------------------------------------------------ 07 ch3 eval
rows = "".join(
    f"<tr><td>{SHORT[b]}</td><td>{BOARDS[b]['tier']}</td><td class=c>{META[b]['stats']['copper_layers']}</td><td class=c>{META[b]['stats']['footprints']}</td>"
    f"<td class=c>{META[b]['stats']['pair_nets']}</td><td class=c>{META[b]['stripped_unconnected']:,}</td><td>{HS[b]}</td><td>{FAB[BOARDS[b]['fab_evidence']]}</td></tr>"
    for b in BOARDS)
page("03 · The eval", f'''
{chead(3, "Chapter 3 of 4 · A benchmark with physics in the score", "Eight boards that were built and used become the answer key")}
<div class="grid2" style="align-items:start">
<div>{ex(4, "The gold-master set: Antmicro open hardware, Apache-2.0")}
<table class="sm"><tr><th>Board</th><th>Tier</th><th>Cu</th><th>Parts</th><th>Pair nets</th><th>To route</th><th>High speed</th><th>Built</th></tr>{rows}</table>
<p class="cap">“To route”: connections left after the copper is stripped, from KiCad’s connectivity engine. Antmicro’s rule files set widths and gaps but contain no length or skew limits: those targets live only in the human copper, which is why the eval scores against the copper itself.</p></div>
<div>{fig("ddr5-highspeed.png", "RDIMM DDR5 tester, data nets only: the length-matching meanders an engineer drew by hand are the answer key.", "1.9in", dark=True)}
<div style="height:6pt"></div>{fig("hdmi-assembled.png", "HDMI–MIPI bridge, four layers, 121 parts: the easy tier.", "1.55in", dark=True)}</div>
</div>
{ex(5, "How a task runs (Harbor 0.25 format, one task per board)")}
<div class="steps4">
 <div><b>1 · Strip</b>The image build fetches the gold board at a pinned commit, checks its sha256, removes tracks, vias, tuning patterns and fills, and deletes the original in the same layer.</div>
 <div><b>2 · Route</b>The agent gets the stripped board, KiCad 10.0.7, Freerouting 2.5 and Java 25, and must save a routed board in place without moving a part.</div>
 <div><b>3 · Verify</b>A separate verifier re-fetches the gold, refills zones and compares, net by net and layer by layer.</div>
 <div><b>4 · Score</b><code>placement × completion² × (0.30 DRC + 0.25 pair skew + 0.15 length groups + 0.15 impedance width + 0.15 efficiency)</code></div>
</div>''')

# ------------------------------------------------------------------ 08 results
if best:
    res_rows = "".join(
        f"<tr><td>{SHORT[b]}</td><td class=c>{r['router_seconds']:.0f} s</td><td class=c>{r['completion']*100:.0f}%</td><td class=c>{r['drc']:.2f}</td>"
        f"<td class=c>{r['pair_skew']:.2f}</td><td class=c>{r['length_groups']:.2f}</td><td class=c>{r['impedance_width']:.2f}</td><td class=c>{r['efficiency']:.2f}</td><td class=c><b>{r['reward']:.2f}</b></td></tr>"
        for b, r in sorted(best.items(), key=lambda kv: list(BOARDS).index(kv[0])))
else:
    res_rows = "<tr><td colspan=9>baselines pending</td></tr>"
n_oracle = sum(1 for o in ORACLE if o.get("reward") == 1.0)
page("03 · The eval", f'''
<div class="kicker">First results</div>
<h2>The open router connects the board and misses the physics.</h2>
<p class="lead">Freerouting 2.5, run with no agent on the stripped boards, is the floor every method must beat. On boards without dense BGAs it completes 72–96% of connections, then fails exactly where high-frequency design lives: pair skew, length groups and impedance-correct widths. On the BGA-heavy HDMI bridge it stalls at 18%.</p>
{ex(6, f"Freerouting baseline against the gold masters (best of {n_base} runs; 1.00 = the human original)")}
<table class="sm res"><tr><th>Board</th><th>Router time</th><th>Routed</th><th>DRC</th><th>Pair skew</th><th>Length groups</th><th>Imp. width</th><th>Efficiency</th><th>Reward</th></tr>{res_rows}</table>
<p class="cap">Each column is the share of the human result achieved (DRC: penalty for errors beyond the gold board’s own). Runs on 1 CPU core under x86 emulation on an Apple M-series laptop; pass limits 1, 3 and 10, two seeds. Runs vary: on the PCIe adapter, reward ranged 0.21–0.27 across seeds and pass limits. Independent runs overlap the gold copper by about 1% (<code>gold_copy_fraction</code> 0.008–0.012). Oracle: {n_oracle} of {len(ORACLE) or 8} tasks score 1.00 through Harbor.</p>
<div class="grid3" style="margin-top:8pt">
 <div class="card"><h3>What works {tag("ok")}</h3>The pipeline end to end: pinned inputs, strip, separate verifier, oracle at 1.00, and a gold-copy check that flags any run reproducing the human copper.</div>
 <div class="card"><h3>What the floor shows {tag("grow")}</h3>On the PCIe adapter the router made {m2.get("completion", 0)*100:.0f}% of connections but only {m2.get("pair_skew", 0)*9:.0f} of 9 pairs met the skew tolerance and {m2.get("impedance_width", 0)*100:.0f}% of high-speed copper used an impedance-correct width.</div>
 <div class="card"><h3>Next runs {tag("next")}</h3>Agent runs through Harbor (Claude Code, Codex, OpenHands), KiCadRoutingTools with length matching, the Jetson Orin baseline on native hardware (it exceeded 90 min under emulation) and the hard DDR tier.</div>
</div>
<div class="note" style="margin-top:8pt"><b>Integrity.</b> Agents have network access, so a run could download the gold board. The verifier reports <code>gold_copy_fraction</code>, the share of segments that coincide with the human copper on a 10 µm grid; leaderboards disqualify runs above 0.5. Public boards may also sit in model training data, a contamination risk shared by every open benchmark.</div>''')

# ------------------------------------------------------------------ 09 ch4 forecast
page("04 · The forecast", f'''
{chead(4, "Chapter 4 of 4 · Outcome against dollars and hours", "Below a few hundred dollars per board, time and the evaluator decide the outcome")}
<div class="grid2" style="align-items:start;grid-template-columns:1.25fr 1fr;gap:12pt">
<div>{ex(7, "Best achievable reward, hard tier (DDR5-class board)")}
<img src="m/fc_surface3d_hard.png" style="width:100%;display:block">
<p class="cap">Envelope over seven strategies; floor contours at 0.3, 0.5, 0.7 and 0.8. The step near $300 is the surrogate’s data bill; the ridge near one day is its training time.</p></div>
<div><div class="methods" style="margin-top:0"><span class="kicker">How the forecast works</span>
<p>Each strategy has a fixed cost (training data, GPU fit), a cost and duration per candidate, a parallelism limit and a saturating return, G = g₀ + (g_max − g₀)(1 − (1 + N/n₀)<sup>−α</sup>), where N is the number of candidates the budget and the clock both allow. α = 0.6 and n₀ = 60 reproduce WireMask-EA’s diminishing returns. Starting points come from the measured baselines; ceilings for untested strategies are labelled assumptions. Prices: Modal CPU $0.047 per core-hour, A100 $2.50 per hour (7 Nov 2026). All parameters live in <code>forecast/forecast.toml</code>; <code>make forecast</code> redraws every chart.</p></div>
<img src="m/fc_winner_hard.png" style="width:100%;display:block;margin-top:8pt">
<p class="cap">Which strategy is best where (hard tier). Black: EM-trained surrogate; dark grey: deterministic SI tooling.</p>
</div>
</div>
{ex(8, "Reward against budget at 24 hours, hard tier")}
<img src="m/fc_budget_hard.png" style="width:100%;display:block">
''')

# ------------------------------------------------------------------ 10 budgeting + plan
fr = {(r["budget"], r["hours"]): r for r in FC["hard"]["rows"]}
fm = {(r["budget"], r["hours"]): r for r in FC["medium"]["rows"]}
page("04 · Recommendations", f'''
<div class="kicker">Budgeting recommendations</div>
<h2>Spend on parallel CPU and on the evaluator. Buy GPUs only after the solver earns them.</h2>
{ex(9, "Forecast reward by budget and wall clock (medium · hard tier)")}
<table class="sm fc"><tr><th>Budget per board</th><th>4 hours</th><th>1 day</th><th>1 week</th><th>Strategy that wins</th></tr>
{"".join(f"<tr><td>${b:,}</td>" + "".join(f"<td class=c>{fm[(b,t)]['reward']:.2f} · {fr[(b,t)]['reward']:.2f}</td>" for t in (4, 24, 168)) + f"<td>{fr[(b,168)]['best']}</td></tr>" for b in (100, 1000, 10000))}</table>
<ol class="recs" style="margin-top:6pt">
 <li><div><b>Cap routing compute at about $100 per board.</b><span>A medium-board candidate costs about one cent of CPU; $100 buys some 9,000 candidates, far past the point where search flattens.</span></div></li>
 <li><div><b>Put the next $1,000 into the evaluator.</b><span>Build the SI tooling and an openEMS-trained surrogate for the hard tier; it is the only strategy whose ceiling rises with spend.</span></div></li>
 <li><div><b>Buy wall clock with cores, not GPUs.</b><span>256 spot cores at about $4 an hour turn a one-week search into an overnight one. Benchmark openEMS’s new GPU engine before any GPU spend.</span></div></li>
 <li><div><b>Fund RL only as a research line.</b><span>At about $3,000 and three days of fixed cost, it reaches less than search does today.</span></div></li>
</ol>
{ex(10, "Reward against wall clock at $1,000, hard tier: the clock, not the budget, separates the strategies")}
<img src="m/fc_time_hard.png" style="width:78%;display:block">
{ex(11, "Phased plan")}
<div class="steps4">
 <div><b>P0 · this week</b>Publish the eval; run three coding agents and KiCadRoutingTools through Harbor on the easy and medium tiers. Exit: a public leaderboard.</div>
 <div><b>P1 · 2–3 weeks</b>Evolved routing recipes (pymoo) with deterministic SI fix-ups. Exit: beat Freerouting by 0.2 on the medium tier.</div>
 <div><b>P2 · 1–2 months</b>gerber2ems sampling and an SI surrogate; full-wave checks on the top 5%. Exit: hard-tier pair and length scores above 0.8.</div>
 <div><b>P3 · quarter</b>Placement tasks (unplaced boards), LLM-evolved router heuristics, then RL if the data supports it.</div>
</div>''')

# ------------------------------------------------------------------ end card
end = f'''<section class="page dark">
<div class="body" style="top:.9in">
<div class="kicker" style="color:#9a9a98">Thanks</div>
<h2 style="color:#fff;font-size:32pt;max-width:6.8in;margin-top:8pt">Measure the physics. Search before you learn. Keep the human copper as the answer key.</h2>
<p class="lead" style="color:#d6d6d2;margin-top:14pt">Gold-master boards by Antmicro (Apache-2.0), fetched at pinned commits. Built with KiCad 10, Freerouting, Harbor, three.js and matplotlib. Research assisted by AI agents; every figure is reproducible with <code style="background:#1b1b1b;color:#fff">make all</code>.</p>
{fig("orin-exploded.png", "", "3.1in", dark=True)}
<div class="grid3" style="margin-top:14pt;color:#c9c9c7;font-size:8.6pt">
 <div class="thanks"><span class="kicker">Repo</span>github.com/elevenarms/pcb-gold-eval</div>
 <div class="thanks"><span class="kicker">Project page</span>pcb-gold-eval.vercel.app</div>
 <div class="thanks"><span class="kicker">Series</span>Field Report 01 · build loop<br>Field Report 02 · agentic hardware<br>Case Study · PLM with agents<br>Field Report 03 · gold-master eval</div>
</div></div>
<div class="foot"><span class="bug"><img src="assets/mark-white.png">Rauchwerk Research</span><span>dbrauchwerk@gmail.com</span><span>{TOT:02d} / {TOT:02d}</span></div>
</section>'''

css = open(os.path.join(D, "extra_css.txt")).read().split("'''", 1)[1].rsplit("'''", 1)[0] + '''<style>
figure.fd img { background: #000; border-color: #0a0a0a; }
.steps4 { display: grid; grid-template-columns: repeat(4, 1fr); gap: 8pt; font-size: 7.9pt; line-height: 1.35; }
.steps4 > div { border-top: 1.5pt solid var(--ink); padding-top: 4pt; } .steps4 b { display: block; font-size: 9pt; margin-bottom: 2pt; }
table.score td.c, table.res td.c, table.fc td.c, table.sm td.c { text-align: center; }
table.sm td:first-child { white-space: normal; }
.five { display: grid; grid-template-columns: repeat(5, 1fr); gap: 7pt; font-size: 7.4pt; line-height: 1.3; color: var(--mid); }
.five > div { border-top: 1.5pt solid var(--ink); padding-top: 4pt; } .five b { display: block; font: 800 15pt var(--sans); color: var(--ink); letter-spacing: -.3pt; margin-bottom: 2pt; }
.note { background: #fff; border-top: 1.5pt solid var(--ink); padding: 6pt 9pt; font-size: 8pt; line-height: 1.38; }
code { font: 500 7.4pt var(--mono); }
</style>'''
head = f'''<!DOCTYPE html><html lang="en"><head><meta charset="utf-8"><title>Rauchwerk Research · PCB Gold-Master Eval</title>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;700;800&family=DM+Mono:wght@400;500&display=swap">
<link rel="stylesheet" href="rr.css">{css}</head><body>'''
assert len(PAGES) + 2 == TOT, len(PAGES) + 2
open(os.path.join(D, "report.html"), "w").write(head + cover + render_pages() + end + "</body></html>")
print("pages:", len(PAGES) + 2, "baselines:", n_base, "oracle:", len(ORACLE))
