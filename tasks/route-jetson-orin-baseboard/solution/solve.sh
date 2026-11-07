#!/bin/bash
# Oracle: restore the human-routed copper (proves the verifier scores the gold master at 1.0).
set -euo pipefail
curl -fsSL -o /tmp/gold.kicad_pcb "https://raw.githubusercontent.com/antmicro/jetson-orin-baseboard/34f0e7f5fbca441191e20ed55d93cf8614e12bed/jetson-orin-baseboard.kicad_pcb"
echo "eaeb87f5bceb46097c8161cf5e990c3609bf667f5a53668f76aa93595bd636ca  /tmp/gold.kicad_pcb" | sha256sum -c -
python3 -c "import pcbnew; pcbnew.SaveBoard('/app/board.kicad_pcb', pcbnew.LoadBoard('/tmp/gold.kicad_pcb'))" 2>/dev/null
