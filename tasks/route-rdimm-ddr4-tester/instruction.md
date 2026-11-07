# Route the rdimm ddr4 tester (hard)

`/app/board.kicad_pcb` is a real, fabricated open-hardware board by Antmicro ([antmicro/rdimm-ddr4-tester](https://github.com/antmicro/rdimm-ddr4-tester),
Apache-2.0), with every track, via and zone fill removed. Placement, footprints, nets, net classes, zones and the
design rules (`/app/board.kicad_pro` and `/app/board.kicad_dru`) are as the designers left them.

**Task: route the board.** Save the result in place as `/app/board.kicad_pcb` (KiCad 10 format).

Rules:
- Do not move, rotate, flip, add or delete footprints, and do not change nets or net classes.
- Respect the net classes: controlled-impedance nets have per-layer widths and diff-pair gaps in the project rules.
- High-speed nets (DDR4 RDIMM, PCIe) need matched lengths and low intra-pair skew, as a hardware designer would route them.

Tools in the image: `kicad-cli` and the `pcbnew` Python module (KiCad 10.0.7), Java 25 with Freerouting 2.5.0 at
`/opt/freerouting.jar` (`java -jar /opt/freerouting.jar -de in.dsn -do out.ses --gui.enabled=false`), Python 3, git,
a C toolchain, and network access for other open-source tools.

How it is scored (against the human-routed original, which you cannot see):
- **gate:** placement untouched; **completion** = connections made, squared;
- **quality:** DRC errors beyond the original's (30%), diff-pair skew within max(0.15 mm, 1.5x the human's) (25%),
  length-group spread vs the human's (15%), impedance-correct widths per layer (15%), copper length and vias vs the human's (15%).
