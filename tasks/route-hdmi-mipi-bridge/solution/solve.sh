#!/bin/bash
# Oracle: restore the human-routed copper (proves the verifier scores the gold master at 1.0).
set -euo pipefail
curl -fsSL -o /tmp/gold.kicad_pcb "https://raw.githubusercontent.com/antmicro/hdmi-mipi-bridge/6c683289a3191ee6c92cf4f9065ca9b6cb2c0784/antmicro-hdmi-mipi-bridge-hw.kicad_pcb"
echo "565fee5d249c0389b434458f0e5d21a97d377ae6d861dedfbdf5b4e5d5cd86a8  /tmp/gold.kicad_pcb" | sha256sum -c -
python3 -c "import pcbnew; pcbnew.SaveBoard('/app/board.kicad_pcb', pcbnew.LoadBoard('/tmp/gold.kicad_pcb'))" 2>/dev/null
