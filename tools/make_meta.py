#!/usr/bin/env python3
"""Per-board metadata for the verifier (run inside the KiCad image): gold DRC, stripped unconnected count, stats.
Usage: python3 tools/make_meta.py <board-id>...  -> data/meta/<id>.json"""
import json, os, shutil, sys, tempfile, time
sys.path.insert(0, os.path.dirname(__file__))
import pcbeval as p, pcbnew

for bid in sys.argv[1:]:
    t0 = time.time()
    src = f"boards/{bid}"
    with tempfile.TemporaryDirectory() as d:
        for k in ("pro", "dru"):
            if os.path.exists(f"{src}/board.kicad_{k}"):
                for n in ("g", "s"):
                    shutil.copy(f"{src}/board.kicad_{k}", f"{d}/{n}.kicad_{k}")
        shutil.copy(f"{src}/board.kicad_pcb", f"{d}/g.kicad_pcb")
        p.strip(f"{d}/g.kicad_pcb", f"{d}/s.kicad_pcb")
        gd, sd = p.drc(f"{d}/g.kicad_pcb"), p.drc(f"{d}/s.kicad_pcb")
        st = p.stats(f"{d}/g.kicad_pcb")
        b = pcbnew.LoadBoard(f"{d}/g.kicad_pcb")
        pairs = p.pairs_of(st)
        meta = dict(gold_drc=gd, stripped_unconnected=sd["unconnected"], stripped_errors=sd["errors"],
                    stats=dict(copper_layers=b.GetCopperLayerCount(), footprints=len(st["footprints"]), nets=len(st["nets"]),
                               pair_nets=2 * len(pairs), via_total=st["via_total"], length_total_mm=round(st["length_total"], 1)),
                    seconds=round(time.time() - t0, 1))
    os.makedirs("data/meta", exist_ok=True)
    json.dump(meta, open(f"data/meta/{bid}.json", "w"), indent=1)
    print(bid, json.dumps(meta), flush=True)
