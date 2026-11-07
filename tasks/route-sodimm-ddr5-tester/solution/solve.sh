#!/bin/bash
# Oracle: restore the human-routed copper (proves the verifier scores the gold master at 1.0).
set -euo pipefail
curl -fsSL -o /tmp/gold.kicad_pcb "https://raw.githubusercontent.com/antmicro/sodimm-ddr5-tester/05b265a75b87d63862323082bfdcb62949d22647/sodimm-ddr5-tester.kicad_pcb"
echo "6808d7b01dd8b5896b0a920ff73b11bf673f59eeb4d709babf0770d8aa2a1904  /tmp/gold.kicad_pcb" | sha256sum -c -
python3 -c "import pcbnew; pcbnew.SaveBoard('/app/board.kicad_pcb', pcbnew.LoadBoard('/tmp/gold.kicad_pcb'))" 2>/dev/null
