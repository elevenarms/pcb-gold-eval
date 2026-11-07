#!/usr/bin/env python3
"""Generate one Harbor task per gold-master board (tasks/route-<id>/). Stdlib only; deterministic.
Inputs: boards.toml, data/meta/<id>.json (from tools/make_meta.sh). Usage: python3 tools/make_tasks.py"""
import json, pathlib, shutil, tomllib

ROOT = pathlib.Path(__file__).resolve().parent.parent
BOARDS = tomllib.loads((ROOT / "boards.toml").read_text())
PINS = tomllib.loads((ROOT / "pins.toml").read_text())
LIMITS = {"easy": (3600, 4, 8192), "medium": (7200, 8, 16384), "hard": (14400, 8, 32768)}

DOCKERFILE = """# syntax=docker/dockerfile:1
# Environment for route-{id}. Every input is pinned (image digest, file sha256s, board commit).
FROM --platform=linux/amd64 {kicad_image}
USER root
RUN apt-get update && apt-get install -y --no-install-recommends curl ca-certificates python3-pip git build-essential \\
    && rm -rf /var/lib/apt/lists/*
# Java 25 (Freerouting 2.5 needs >= 25) and Freerouting, both sha256-pinned
RUN curl -fsSL -o /tmp/jdk.tgz "{jdk_url}" && echo "{jdk_sha256}  /tmp/jdk.tgz" | sha256sum -c - \\
    && mkdir -p /opt/jdk && tar -xzf /tmp/jdk.tgz -C /opt/jdk --strip-components=1 && rm /tmp/jdk.tgz \\
    && curl -fsSL -o /opt/freerouting.jar "{freerouting_url}" && echo "{freerouting_sha256}  /opt/freerouting.jar" | sha256sum -c -
ENV PATH=/opt/jdk/bin:$PATH
COPY pcbeval.py /opt/pcbeval/pcbeval.py
# Fetch the human-routed gold board, strip its copper and delete it in ONE layer: the agent never sees the gold.
WORKDIR /app
RUN set -e; base="https://raw.githubusercontent.com/{repo}/{commit}"; \\
{fetch_lines}    python3 /opt/pcbeval/pcbeval.py strip /tmp/gold.kicad_pcb /app/board.kicad_pcb 2>/dev/null; \\
    rm -f /tmp/gold.kicad_pcb; chown -R kicad:kicad /app
USER kicad
"""

INSTRUCTION = """# Route the {title} ({tier})

`/app/board.kicad_pcb` is a real, fabricated open-hardware board by Antmicro ([{repo}](https://github.com/{repo}),
Apache-2.0), with every track, via and zone fill removed. Placement, footprints, nets, net classes, zones and the
design rules (`/app/board.kicad_pro`{dru_note}) are as the designers left them.

**Task: route the board.** Save the result in place as `/app/board.kicad_pcb` (KiCad 10 format).

Rules:
- Do not move, rotate, flip, add or delete footprints, and do not change nets or net classes.
- Respect the net classes: controlled-impedance nets have per-layer widths and diff-pair gaps in the project rules.
- High-speed nets ({hs}) need matched lengths and low intra-pair skew, as a hardware designer would route them.

Tools in the image: `kicad-cli` and the `pcbnew` Python module (KiCad 10.0.7), Java 25 with Freerouting 2.5.0 at
`/opt/freerouting.jar` (`java -jar /opt/freerouting.jar -de in.dsn -do out.ses --gui.enabled=false`), Python 3, git,
a C toolchain, and network access for other open-source tools.

How it is scored (against the human-routed original, which you cannot see):
- **gate:** placement untouched; **completion** = connections made, squared;
- **quality:** DRC errors beyond the original's (30%), diff-pair skew within max(0.15 mm, 1.5x the human's) (25%),
  length-group spread vs the human's (15%), impedance-correct widths per layer (15%), copper length and vias vs the human's (15%).
"""

TOML = """schema_version = "1.4"
artifacts = ["/app/board.kicad_pcb"]

[task]
name = "pcb-gold-eval/route-{id}"
authors = [{{ name = "Dave Rauchwerk", email = "dbrauchwerk@gmail.com" }}]

[metadata]
category = "hardware-design"
difficulty = "{tier}"
difficulty_explanation = "{layers}-layer board, {fps} footprints, {pairs} diff-pair nets; gold master: {repo}@{short} ({fab})"
tags = ["pcb", "routing", "signal-integrity", "kicad", "antmicro"]

[verifier]
environment_mode = "separate"
timeout_sec = {vt}

[agent]
timeout_sec = {at}

[environment]
cpus = {cpus}
memory_mb = {mem}
storage_mb = 20480
"""

TEST_SH = """#!/bin/bash
# Verifier: re-fetch the gold board at its pinned commit, check sha256, score the agent's board against it.
set -uo pipefail
mkdir -p /logs/verifier /tmp/v && cd /tmp/v
base="https://raw.githubusercontent.com/{repo}/{commit}"
{fetch_lines_v}
cp /app/board.kicad_pro /tmp/v/cand.kicad_pro 2>/dev/null || cp gold.kicad_pro cand.kicad_pro
[ -f gold.kicad_dru ] && cp gold.kicad_dru cand.kicad_dru
if [ ! -s /app/board.kicad_pcb ]; then echo '{{"reward": 0}}' > /logs/verifier/reward.json; exit 0; fi
cp /app/board.kicad_pcb cand.kicad_pcb
python3 /tests/pcbeval.py score gold.kicad_pcb cand.kicad_pcb /tests/meta.json /logs/verifier/reward.json \\
  2>/dev/null | tee /logs/verifier/detail.json || echo '{{"reward": 0}}' > /logs/verifier/reward.json
"""

SOLVE_SH = """#!/bin/bash
# Oracle: restore the human-routed copper (proves the verifier scores the gold master at 1.0).
set -euo pipefail
curl -fsSL -o /tmp/gold.kicad_pcb "https://raw.githubusercontent.com/{repo}/{commit}/{pcb_path}"
echo "{pcb_sha}  /tmp/gold.kicad_pcb" | sha256sum -c -
python3 -c "import pcbnew; pcbnew.SaveBoard('/app/board.kicad_pcb', pcbnew.LoadBoard('/tmp/gold.kicad_pcb'))" 2>/dev/null
"""

HS = {"signal-integrity-test-board": "50-ohm test traces", "m2-pcie-adapter": "PCIe x4",
      "hdmi-mipi-bridge": "HDMI, MIPI CSI-2", "gmsl-deserializer": "GMSL2 coax, MIPI CSI-2",
      "jetson-orin-baseboard": "PCIe, USB 3, CSI-2, HDMI, Ethernet", "rdimm-ddr4-tester": "DDR4 RDIMM, PCIe",
      "sodimm-ddr5-tester": "DDR5 SO-DIMM", "rdimm-ddr5-tester": "DDR5 RDIMM, PCIe"}


def q(s):
    return s.replace('"', '\\"')


def main():
    out_root = ROOT / "tasks"
    for bid, b in BOARDS.items():
        meta = json.loads((ROOT / "data/meta" / f"{bid}.json").read_text())
        t = out_root / f"route-{bid}"
        shutil.rmtree(t, ignore_errors=True)
        for d in ("environment", "solution", "tests"):
            (t / d).mkdir(parents=True)
        f = b["files"]
        fetch = "".join(f'    curl -fsSL -o {dst} "$base/{f[k]["path"]}" && echo "{f[k]["sha256"]}  {dst}" | sha256sum -c -; \\\n'
                        for k, dst in (("pcb", "/tmp/gold.kicad_pcb"), ("pro", "/app/board.kicad_pro"), ("dru", "/app/board.kicad_dru"))
                        if k in f)
        fetch_v = "".join(f'curl -fsSL -o gold.kicad_{k} "$base/{f[k]["path"]}" && echo "{f[k]["sha256"]}  gold.kicad_{k}" | sha256sum -c - || {{ echo \'{{"reward": 0}}\' > /logs/verifier/reward.json; exit 0; }}\n'
                          for k in ("pcb", "pro", "dru") if k in f)
        (t / "environment/Dockerfile").write_text(DOCKERFILE.format(id=bid, repo=b["repo"], commit=b["commit"], fetch_lines=fetch, **PINS["env"]))
        shutil.copy(ROOT / "tools/pcbeval.py", t / "environment/pcbeval.py")
        shutil.copy(ROOT / "tools/pcbeval.py", t / "tests/pcbeval.py")
        (t / "tests/meta.json").write_text(json.dumps(meta, indent=1))
        (t / "tests/test.sh").write_text(TEST_SH.format(repo=b["repo"], commit=b["commit"], fetch_lines_v=fetch_v))
        (t / "solution/solve.sh").write_text(SOLVE_SH.format(repo=b["repo"], commit=b["commit"], pcb_path=f["pcb"]["path"], pcb_sha=f["pcb"]["sha256"]))
        for s in ("tests/test.sh", "solution/solve.sh"):
            (t / s).chmod(0o755)
        at, cpus, mem = LIMITS[b["tier"]]
        st = meta["stats"]
        (t / "task.toml").write_text(TOML.format(id=bid, tier=b["tier"], repo=b["repo"], short=b["commit"][:7], fab=q(b["fab_evidence"]),
                                                 layers=st["copper_layers"], fps=st["footprints"], pairs=st["pair_nets"],
                                                 at=at, vt=max(900, at // 4), cpus=cpus, mem=mem))
        (t / "instruction.md").write_text(INSTRUCTION.format(title=bid.replace("-", " "), tier=b["tier"], repo=b["repo"], hs=HS[bid],
                                                             dru_note=" and `/app/board.kicad_dru`" if "dru" in f else ""))
        print("wrote", t.relative_to(ROOT))


if __name__ == "__main__":
    main()
