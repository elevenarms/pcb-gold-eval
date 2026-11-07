#!/usr/bin/env python3
"""Gold-master PCB routing eval: strip, stats and score. Runs inside kicad/kicad:10.0.7 (needs pcbnew + kicad-cli).

  pcbeval.py strip  GOLD.kicad_pcb OUT.kicad_pcb     remove routed copper (tracks, arcs, vias, tuning patterns, zone fills)
  pcbeval.py stats  BOARD.kicad_pcb                  routing statistics as JSON
  pcbeval.py drc    BOARD.kicad_pcb                  DRC summary (zones refilled) as JSON
  pcbeval.py score  GOLD.kicad_pcb CAND.kicad_pcb META.json OUT_reward.json

Every target is derived from the human-routed gold board, because Antmicro's rule files hold widths and gaps
but no length or skew limits: the matching the designers did lives only in their copper.
"""
import json, os, re, subprocess, sys, tempfile
from collections import Counter, defaultdict

import pcbnew

MM = 1e6  # KiCad internal units: nm


def load(p):
    return pcbnew.LoadBoard(p)


# ------------------------------------------------------------------ strip
REMOVE_TOP = ("segment", "arc", "via", "generated")


def normalise(src, out):
    """Load and save through KiCad 10 so every board has the same text layout (tabs, one block per item)."""
    pcbnew.SaveBoard(out, load(src))


def strip(gold, out):
    """Remove routed copper as text. (pcbnew Board.Remove() on tracks crashes in 10.0.7's SWIG bindings.)"""
    with tempfile.TemporaryDirectory() as d:
        norm = os.path.join(d, "n.kicad_pcb")
        normalise(gold, norm)
        lines = open(norm).read().split("\n")
    keep, skip_until = [], None
    for ln in lines:
        if skip_until is not None:
            if ln == skip_until:
                skip_until = None
            continue
        m = re.match(r"^(\t{1,2})\((\w+)", ln)
        if m and ((len(m.group(1)) == 1 and m.group(2) in REMOVE_TOP) or (len(m.group(1)) == 2 and m.group(2) == "filled_polygon")):
            if ln.count("(") != ln.count(")"):
                skip_until = m.group(1) + ")"
            continue
        keep.append(ln)
    open(out, "w").write("\n".join(keep))


# ------------------------------------------------------------------ stats
PAIR = re.compile(r"^(.*?)(_P|_N|\+|-|P|N)$")


def pair_key(name):
    """Return (base, polarity) for diff-pair nets named *_P/_N, *+/-, or *P/*N (last only if both exist)."""
    m = PAIR.match(name)
    if not m:
        return None
    base, suf = m.groups()
    pol = "P" if suf in ("_P", "+", "P") else "N"
    return base + ("_" if suf.startswith("_") else "~" if suf in "+-" else "#"), pol


def stats(path):
    b = load(path)
    length = defaultdict(float)            # net -> mm
    widths = defaultdict(float)            # (netclass, layer, width_um) -> mm of copper
    vias = Counter()
    netclass = {}
    total = 0.0
    segs = set()
    for t in b.GetTracks():
        n = t.GetNetname()
        if t.Type() != pcbnew.PCB_VIA_T:
            a, e = t.GetStart(), t.GetEnd()
            segs.add((t.GetLayer(),) + tuple(sorted(((round(a.x, -4), round(a.y, -4)), (round(e.x, -4), round(e.y, -4))))))
        if t.Type() == pcbnew.PCB_VIA_T:
            vias[n] += 1
            continue
        L = t.GetLength() / MM
        length[n] += L
        total += L
        nc = t.GetNetClassName()
        netclass[n] = nc
        widths[(nc, t.GetLayerName(), round(t.GetWidth() / 1000))] += L
    fps = {f.GetReference() + "@" + str(f.GetFPIDAsString()): (f.GetPosition().x, f.GetPosition().y, f.GetOrientationDegrees(), f.GetLayer())
           for f in b.GetFootprints()}
    nets = [n for n in b.GetNetsByName().keys() if str(n)]
    return dict(segs=segs, length=dict(length), vias=dict(vias), via_total=sum(vias.values()), length_total=total,
                widths={"|".join(map(str, k)): v for k, v in widths.items()}, netclass=netclass,
                footprints=fps, nets=[str(n) for n in nets])


# ------------------------------------------------------------------ drc
def drc(path):
    with tempfile.TemporaryDirectory() as d:
        # run on a copy: kicad-cli may rewrite sidecar files next to the board
        cp = os.path.join(d, "b.kicad_pcb")
        subprocess.run(["cp", path, cp], check=True)
        for ext in ("kicad_pro", "kicad_dru"):
            side = path.rsplit(".", 1)[0] + "." + ext
            if os.path.exists(side):
                subprocess.run(["cp", side, os.path.join(d, "b." + ext)], check=True)
        out = os.path.join(d, "drc.json")
        subprocess.run(["kicad-cli", "pcb", "drc", "--refill-zones", "--format", "json", "--severity-error",
                        "-o", out, cp], capture_output=True, text=True)
        r = json.load(open(out))
    errs = Counter(v["type"] for v in r.get("violations", []))
    return dict(unconnected=unconnected(path), errors=dict(errs))


def unconnected(path):
    """True unconnected count from the connectivity engine after a zone refill.
    (kicad-cli's DRC JSON stops listing unconnected items at 499, so it cannot be used for completion.)"""
    b = load(path)
    pcbnew.ZONE_FILLER(b).Fill(b.Zones())
    b.BuildConnectivity()
    c = b.GetConnectivity()
    c.RecalculateRatsnest()
    return c.GetUnconnectedCount(False)


# ------------------------------------------------------------------ score
def pairs_of(st):
    by = defaultdict(dict)
    for n in st["length"]:
        k = pair_key(n.split("/")[-1])
        if k:
            by[(n.rsplit("/", 1)[0] if "/" in n else "") + k[0]][k[1]] = n
    return {k: (v["P"], v["N"]) for k, v in by.items() if "P" in v and "N" in v}


def score(gold_p, cand_p, meta_p, out_p):
    meta = json.load(open(meta_p))
    g, c = stats(gold_p), stats(cand_p)
    gd, cd = meta["gold_drc"], drc(cand_p)
    parts = {}

    # 0. integrity gate: placement and netlist must be untouched (routing task)
    moved = [k for k, v in g["footprints"].items()
             if k not in c["footprints"] or any(abs(a - b) > 10_000 for a, b in zip(v[:2], c["footprints"][k][:2]))
             or abs(v[2] - c["footprints"][k][2]) > 0.01 or v[3] != c["footprints"][k][3]]
    parts["placement_intact"] = 0.0 if moved else 1.0

    # 1. completion, normalised between the stripped board and the gold board
    u0, ug, uc = meta["stripped_unconnected"], gd["unconnected"], cd["unconnected"]
    parts["completion"] = max(0.0, min(1.0, 1 - (uc - ug) / max(1, u0 - ug)))

    # 2. DRC: errors beyond what the gold board itself reports, by type
    excess = sum(max(0, n - gd["errors"].get(k, 0)) for k, n in cd["errors"].items())
    parts["drc"] = 1 / (1 + excess / 10)

    # 3. diff-pair skew vs the skew the human achieved (tolerance 0.15 mm or 1.5x gold)
    gp = pairs_of(g)
    ok = tot = 0
    for k, (p, n) in gp.items():
        gs = abs(g["length"][p] - g["length"][n])
        tot += 1
        if p in c["length"] and n in c["length"]:
            ok += abs(c["length"][p] - c["length"][n]) <= max(0.15, 1.5 * gs)
    parts["pair_skew"] = ok / tot if tot else 1.0

    # 4. length-matching groups: per netclass (non-Default), spread must not exceed the human's by much
    groups = defaultdict(list)
    for n, nc in g["netclass"].items():
        if nc and nc != "Default":
            groups[nc].append(n)
    ok = tot = 0
    for nc, nets in groups.items():
        if len(nets) < 2:
            continue
        gl = [g["length"][n] for n in nets]
        cl = [c["length"].get(n, 0.0) for n in nets]
        tot += 1
        routed = all(n in c["length"] for n in nets)
        ok += routed and (max(cl) - min(cl)) <= max(1.25 * (max(gl) - min(gl)), (max(gl) - min(gl)) + 1.0)
    parts["length_groups"] = ok / tot if tot else 1.0

    # 5. impedance-width conformance: controlled-impedance copper must use a width the human used on that layer
    gw = defaultdict(set)
    for k in g["widths"]:
        nc, layer, w = k.split("|")
        gw[(nc, layer)].add(int(w))
    good = allw = 0.0
    for k, L in c["widths"].items():
        nc, layer, w = k.split("|")
        if nc in ("", "Default"):
            continue
        allw += L
        good += L if any(abs(int(w) - x) <= 5 for x in gw.get((nc, layer), ())) else 0
    parts["impedance_width"] = good / allw if allw else (1.0 if not any(k.split("|")[0] not in ("", "Default") for k in g["widths"]) else 0.0)

    # 6. efficiency vs gold: total length and vias (capped at 1)
    le = min(1.0, g["length_total"] / c["length_total"]) if c["length_total"] else 0.0
    ve = min(1.0, (g["via_total"] + 1) / (c["via_total"] + 1))
    parts["efficiency"] = (le + ve) / 2

    quality = (0.30 * parts["drc"] + 0.25 * parts["pair_skew"] + 0.15 * parts["length_groups"]
               + 0.15 * parts["impedance_width"] + 0.15 * parts["efficiency"])
    reward = parts["placement_intact"] * parts["completion"] ** 2 * quality
    # integrity signal: fraction of the candidate's segments that coincide with the gold's (10 um grid).
    # Independent routing essentially never reproduces human copper; leaderboards disqualify runs above 0.5.
    copy = len(c["segs"] & g["segs"]) / len(c["segs"]) if c["segs"] else 0.0
    res = dict(reward=round(reward, 4), **{k: round(v, 4) for k, v in parts.items()}, gold_copy_fraction=round(copy, 4))
    detail = dict(res, unconnected=dict(stripped=u0, gold=ug, cand=uc), drc_cand=cd, moved=moved[:20],
                  pairs=len(gp), groups=len(groups))
    json.dump(res, open(out_p, "w"))
    print(json.dumps(detail, indent=1))
    return res


if __name__ == "__main__":
    cmd, *a = sys.argv[1:]
    if cmd == "strip":
        strip(*a)
    elif cmd == "stats":
        s = stats(a[0]); s.pop("segs"); s.pop("footprints"); s.pop("widths"); s.pop("length"); s.pop("netclass"); s.pop("vias")
        print(json.dumps(s, indent=1, default=str)[:2000])
    elif cmd == "drc":
        print(json.dumps(drc(a[0])))
    elif cmd == "score":
        score(*a)
