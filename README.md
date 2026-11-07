# PCB Gold-Master Eval

**Can machines route high-frequency boards like the engineers who shipped them?**

Eight fabricated, open-source Antmicro boards with their copper stripped. An agent or algorithm routes each one, and the result is scored against the human original on completion, design rules, differential-pair skew, length matching and impedance-correct trace widths. The tasks use the [Harbor](https://github.com/harbor-framework/harbor) format.

- **Project page (3D views of every board):** https://pcb-gold-eval.vercel.app
- **Field report (10 pages):** [`report/Rauchwerk-Research_PCB-Gold-Master-Eval_Field-Report.pdf`](report/Rauchwerk-Research_PCB-Gold-Master-Eval_Field-Report.pdf)
- **Paper (arXiv draft):** [`paper/main.pdf`](paper/main.pdf)

## Why

ML placers and routers are judged on wirelength, vias and DRC. None of the public PCB benchmarks we found measures the properties that make a fast board work. Antmicro's rule files set widths and gaps but no length or skew limits; those targets exist only in the designers' copper. This eval uses that copper as the answer key.

## The boards

| Task | Tier | Cu layers | Parts | Pair nets | Connections to route | Interfaces |
|---|---|---|---|---|---|---|
| `route-signal-integrity-test-board` | easy | 4 | 28 | 2 | 107 | 50 Ω test lines |
| `route-m2-pcie-adapter` | easy | 4 | 20 | 18 | 93 | PCIe x4 |
| `route-hdmi-mipi-bridge` | easy | 4 | 121 | 36 | 304 | HDMI, MIPI CSI-2 |
| `route-gmsl-deserializer` | medium | 4 | 236 | 28 | 413 | GMSL2, CSI-2 |
| `route-jetson-orin-baseboard` | medium | 8 | 680 | 208 | 1,625 | PCIe, USB 3, CSI-2, HDMI, GbE |
| `route-rdimm-ddr4-tester` | hard | 12 | 691 | 226 | 2,021 | DDR4 RDIMM |
| `route-sodimm-ddr5-tester` | hard | 12 | 706 | 102 | 1,770 | DDR5 SO-DIMM |
| `route-rdimm-ddr5-tester` | hard | 12 | 797 | 178 | 2,300 | DDR5 RDIMM |

All boards are © Antmicro, Apache-2.0. They are fetched at the commits pinned in [`boards.toml`](boards.toml) and checked by sha256. This repo does not redistribute them.

## Scoring

```
reward = placement_intact × completion² × (0.30 DRC + 0.25 pair_skew + 0.15 length_groups + 0.15 impedance_width + 0.15 efficiency)
```

| Term | What it measures |
|---|---|
| `completion` | Connections made, normalised between the stripped board and the gold board. Counted with KiCad's connectivity engine, because `kicad-cli` DRC stops listing unconnected items at 499. |
| `drc` | DRC errors beyond those the gold board itself has, by type. |
| `pair_skew` | Share of differential pairs whose skew is within max(0.15 mm, 1.5× the human skew). |
| `length_groups` | Length spread per net class, compared with the human spread. |
| `impedance_width` | Share of controlled-impedance copper that uses a width the designers used for that class on that layer. |
| `efficiency` | Total copper length and via count compared with the human board. |
| `gold_copy_fraction` | Integrity signal. Share of segments that coincide with the gold copper on a 10 µm grid. Independent routing scores about 0.01; runs above 0.5 are disqualified. |

## Run it

Needs Docker, Python ≥ 3.11, [uv](https://docs.astral.sh/uv/) and Node. Everything is pinned in [`pins.toml`](pins.toml): the KiCad 10.0.7 image digest, the Temurin 25 and Freerouting 2.5.0 sha256s, and Harbor 0.25.0.

```sh
make fetch       # gold boards at pinned commits, sha256-checked
make meta        # gold DRC, stripped connection counts, stats
make tasks       # Harbor tasks -> tasks/route-<id>/
make oracle      # gold copper through Harbor: every task scores 1.0
make baselines   # Freerouting sweep -> data/baselines/
make forecast    # outcome-vs-compute model -> charts
make report      # 10-page field report PDF
make paper       # arXiv paper PDF (tectonic)
```

Run an agent on one task:

```sh
uvx --from harbor==0.25.0 harbor run -p tasks/route-m2-pcie-adapter -a claude-code -m anthropic/claude-opus-5-5 -y
```

## Results so far

The oracle (gold copper) scores 1.00 on 8 of 8 tasks through Harbor. Freerouting 2.5 with no agent completes 72–96% of connections on boards without dense BGAs, stalls at 18% on the BGA-heavy HDMI bridge, and misses the high-frequency terms everywhere. On the M.2 PCIe adapter it routed 92% of connections, met the skew tolerance on 1 of 9 pairs, and reached a reward of 0.21–0.27 across runs. On the eight-layer Jetson Orin baseboard, Freerouting did not finish within 90 minutes under x86 emulation; that board and the hard DDR tier still need native-hardware baselines. Full tables are in [`data/baselines/`](data/baselines), the report and the paper.

## Forecast

[`forecast/forecast.toml`](forecast/forecast.toml) models the reward each strategy reaches for a given budget and wall-clock time. Each parameter is tagged as measured, from a cited paper, a price, or an assumption. `make forecast` redraws the charts. The current conclusion: with open-source tools, compute is cheap (about $0.01 per routing candidate on a medium board), so wall-clock time and evaluator fidelity limit the outcome.

## Repo map

| Path | Contents |
|---|---|
| `boards.toml`, `pins.toml` | Pinned inputs |
| `tools/pcbeval.py` | Strip, stats, DRC and score (runs in the KiCad image) |
| `tools/make_tasks.py`, `tools/make_meta.py` | Harbor task generator and its metadata |
| `tools/baseline_freerouting.py`, `tools/sweep_baselines.sh` | Baselines |
| `tools/export_glb.sh` | 3D board models for the site |
| `tasks/` | Generated Harbor tasks (committed for direct use) |
| `data/` | Board metadata, baseline results, the v3 routing curve |
| `forecast/` | Model parameters and charts |
| `report/`, `paper/`, `site/`, `video/` | Field report, arXiv paper, project page, explainer video |

## Limitations

- **One design house:** all eight boards come from Antmicro.
- **Training-data contamination:** the boards are public and may be in model training data.
- **Geometric scoring:** signal integrity is scored with geometric proxies. Full-wave checks on sampled nets via gerber2ems are next.
- **Placement is fixed:** placement tasks are future work.
- **Baseline hardware:** baselines ran under x86 emulation on one laptop.

## Licence

Apache-2.0 (see [`LICENSE`](LICENSE)). Board designs © Antmicro, Apache-2.0 (see [`NOTICE`](NOTICE)).

Built by Dave Rauchwerk · [Rauchwerk Research](mailto:dbrauchwerk@gmail.com) · November 2026.
