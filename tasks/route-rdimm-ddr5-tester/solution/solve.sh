#!/bin/bash
# Oracle: restore the human-routed copper (proves the verifier scores the gold master at 1.0).
set -euo pipefail
curl -fsSL -o /tmp/gold.kicad_pcb "https://raw.githubusercontent.com/antmicro/rdimm-ddr5-tester/6bd485778de747d0e34551c4c34d2419e2c2d5b9/data-center-rdimm-ddr5-tester.kicad_pcb"
echo "2d5e5a547689ca3fd14682c21f077e658007f5245c473c6598c4785c8adaa6dc  /tmp/gold.kicad_pcb" | sha256sum -c -
python3 -c "import pcbnew; pcbnew.SaveBoard('/app/board.kicad_pcb', pcbnew.LoadBoard('/tmp/gold.kicad_pcb'))" 2>/dev/null
