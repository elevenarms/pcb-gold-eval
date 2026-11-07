#!/usr/bin/env python3
"""Fill the data-driven sections of site/index.html (between <!--X--> markers) and copy figures and PDFs. Stdlib only."""
import glob, json, os, re, shutil, tomllib
R = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
S = f"{R}/site"
B = tomllib.load(open(f"{R}/boards.toml", "rb"))
NAME = {"signal-integrity-test-board": "SI test board", "m2-pcie-adapter": "M.2 PCIe adapter", "hdmi-mipi-bridge": "HDMI–MIPI bridge",
        "gmsl-deserializer": "GMSL deserializer", "jetson-orin-baseboard": "Jetson Orin baseboard", "rdimm-ddr4-tester": "RDIMM DDR4 tester",
        "sodimm-ddr5-tester": "SO-DIMM DDR5 tester", "rdimm-ddr5-tester": "RDIMM DDR5 tester"}
runs = [json.load(open(f)) for f in glob.glob(f"{R}/data/baselines/*.json")]
best = {}
for r in runs:
    if r.get("reward") is not None and (r["board"] not in best or r["reward"] > best[r["board"]]["reward"]):
        best[r["board"]] = r
oracle = [json.load(open(f)) for f in glob.glob(f"{R}/jobs/oracle-all/*/verifier/reward.json")]
rows = "".join(f"<tr><td>{NAME[b]}</td><td>{B[b]['tier']}</td><td>1.00</td>" + (
    f"<td>{best[b]['completion']*100:.0f}%</td><td>{best[b]['pair_skew']:.2f}</td><td>{best[b]['impedance_width']:.2f}</td><td><b>{best[b]['reward']:.2f}</b></td>"
    if b in best else "<td colspan=4 class=pend>running</td>") + "</tr>" for b in B)
results = (f'<span class="kicker">Baseline table · Freerouting 2.5, best of {len(runs)} runs · oracle {sum(o.get("reward")==1.0 for o in oracle)}/{len(oracle) or 8}</span>'
           f'<table class="tbl"><tr><th>Board</th><th>Tier</th><th>Oracle</th><th>Routed</th><th>Pair skew</th><th>Imp. width</th><th>Reward</th></tr>{rows}</table>')
fc = json.load(open(f"{R}/forecast/forecast.json"))
os.makedirs(f"{S}/assets/fig", exist_ok=True)
frows = "".join(f"<tr><td>${b:,}</td>" + "".join(
    f"<td>{next(x for x in fc['medium']['rows'] if x['budget']==b and x['hours']==t)['reward']:.2f} · {next(x for x in fc['hard']['rows'] if x['budget']==b and x['hours']==t)['reward']:.2f}</td>"
    for t in (4, 24, 168)) + "</tr>" for b in (100, 1000, 10000))
forecast = ('<figure class="fig"><img src="assets/fig/fc_surface3d_hard.png" alt="Forecast surface: best achievable reward against budget and wall clock, hard tier">'
            '<figcaption>Best achievable reward over seven strategies, DDR5-class board. Parameters with sources: forecast/forecast.toml.</figcaption></figure>'
            '<figure class="fig"><img src="assets/fig/fc_budget_hard.png" alt="Reward against budget at 24 hours"></figure>'
            f'<span class="kicker">Forecast reward, medium · hard tier</span><table class="tbl"><tr><th>Budget per board</th><th>4 hours</th><th>1 day</th><th>1 week</th></tr>{frows}</table>'
            '<p class="lede">Spend on parallel CPU and on the evaluator. Buy GPUs only after the solver earns them.</p>')
os.makedirs(f"{S}/assets/docs", exist_ok=True)
docs = []
for src, dst, kick, title in ((f"{R}/report/Rauchwerk-Research_PCB-Gold-Master-Eval_Field-Report.pdf", "field-report.pdf", "Field report · 10 pages",
                               "Routed is not the same as right: review, tools, eval and forecast"),
                              (f"{R}/paper/main.pdf", "paper.pdf", "Paper · arXiv draft", "Routed Is Not Right: a gold-master benchmark for machine routing of high-frequency PCBs")):
    if os.path.exists(src):
        shutil.copy(src, f"{S}/assets/docs/{dst}")
        docs.append(f'<a class="doc" href="assets/docs/{dst}"><span class="kicker">{kick}</span><h3>{title}</h3><p>PDF ↓</p></a>')
html = open(f"{S}/index.html").read()
for key, val in (("RESULTS", results), ("FORECAST", forecast), ("DOCS", "".join(docs))):
    html = re.sub(rf"<!--{key}-->.*?<!--/{key}-->", f"<!--{key}-->{val}<!--/{key}-->", html, flags=re.S)
open(f"{S}/index.html", "w").write(html)
print("site filled:", len(best), "boards,", len(docs), "docs")
