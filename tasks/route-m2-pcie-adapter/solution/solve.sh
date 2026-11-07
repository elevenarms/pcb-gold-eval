#!/bin/bash
# Oracle: restore the human-routed copper (proves the verifier scores the gold master at 1.0).
set -euo pipefail
curl -fsSL -o /tmp/gold.kicad_pcb "https://raw.githubusercontent.com/antmicro/m2-pcie-adapter/11844f18ce14393043affde9e7aa8d51c0cd3ba7/m2-pcie-adapter.kicad_pcb"
echo "36533460dd1e940f87672a101aca968ff0e2cc1687a26e02b32b2177f95414f5  /tmp/gold.kicad_pcb" | sha256sum -c -
python3 -c "import pcbnew; pcbnew.SaveBoard('/app/board.kicad_pcb', pcbnew.LoadBoard('/tmp/gold.kicad_pcb'))" 2>/dev/null
