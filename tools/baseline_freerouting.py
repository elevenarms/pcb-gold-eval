#!/usr/bin/env python3
"""Freerouting baseline (no agent): stripped board -> DSN -> Freerouting -> SES -> scored against gold.
Runs inside the task image (needs pcbnew, kicad-cli, java, /opt/freerouting.jar).
Usage: baseline_freerouting.py BOARD_ID MAX_PASSES SEED OUT.json"""
import json, os, re, shutil, subprocess, sys, tempfile, time
sys.path.insert(0, os.path.dirname(__file__))
import pcbeval as p, pcbnew

bid, passes, seed, out = sys.argv[1], int(sys.argv[2]), int(sys.argv[3]), sys.argv[4]
src = f"boards/{bid}"
meta = f"data/meta/{bid}.json"
with tempfile.TemporaryDirectory() as d:
    for k in ("pro", "dru"):
        if os.path.exists(f"{src}/board.kicad_{k}"):
            for n in ("g", "s"):
                shutil.copy(f"{src}/board.kicad_{k}", f"{d}/{n}.kicad_{k}")
    shutil.copy(f"{src}/board.kicad_pcb", f"{d}/g.kicad_pcb")
    p.strip(f"{d}/g.kicad_pcb", f"{d}/s.kicad_pcb")
    b = pcbnew.LoadBoard(f"{d}/s.kicad_pcb")
    pcbnew.ExportSpecctraDSN(b, f"{d}/s.dsn")
    t0 = time.time()
    r = subprocess.run(["java", "-jar", "/opt/freerouting.jar", "-de", f"{d}/s.dsn", "-do", f"{d}/s.ses",
                        "-mp", str(passes), "-mt", "1", "--gui.enabled=false", f"--router.random_seed={seed}"],
                       capture_output=True, text=True, timeout=6 * 3600)
    wall = time.time() - t0
    log = r.stdout + r.stderr
    unrouted = [int(x) for x in re.findall(r"\((\d+) unrouted", log)]
    res = dict(board=bid, passes=passes, seed=seed, router_seconds=round(wall, 1), freerouting_unrouted=unrouted[-1:] or None)
    if os.path.exists(f"{d}/s.ses"):
        b = pcbnew.LoadBoard(f"{d}/s.kicad_pcb")
        pcbnew.ImportSpecctraSES(b, f"{d}/s.ses")
        pcbnew.SaveBoard(f"{d}/c.kicad_pcb", b)
        for k in ("pro", "dru"):
            if os.path.exists(f"{d}/s.kicad_{k}"):
                shutil.copy(f"{d}/s.kicad_{k}", f"{d}/c.kicad_{k}")
        res.update(p.score(f"{d}/g.kicad_pcb", f"{d}/c.kicad_pcb", meta, f"{d}/r.json"))
    else:
        res.update(reward=0.0, error=log[-600:])
json.dump(res, open(out, "w"))
print(json.dumps(res), flush=True)
