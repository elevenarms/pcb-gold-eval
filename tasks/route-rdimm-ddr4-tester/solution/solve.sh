#!/bin/bash
# Oracle: restore the human-routed copper (proves the verifier scores the gold master at 1.0).
set -euo pipefail
curl -fsSL -o /tmp/gold.kicad_pcb "https://raw.githubusercontent.com/antmicro/rdimm-ddr4-tester/e7c85ebc9eb35645a6c467b0362270a5792d2726/data-center-rdimm-ddr4-tester.kicad_pcb"
echo "de397b73b29dec7a4f3e44868bc6abfed0f3be6622e27395ab272d0d0eae6b79  /tmp/gold.kicad_pcb" | sha256sum -c -
python3 -c "import pcbnew; pcbnew.SaveBoard('/app/board.kicad_pcb', pcbnew.LoadBoard('/tmp/gold.kicad_pcb'))" 2>/dev/null
