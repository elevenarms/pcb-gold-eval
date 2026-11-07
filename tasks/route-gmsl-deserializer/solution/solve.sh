#!/bin/bash
# Oracle: restore the human-routed copper (proves the verifier scores the gold master at 1.0).
set -euo pipefail
curl -fsSL -o /tmp/gold.kicad_pcb "https://raw.githubusercontent.com/antmicro/gmsl-deserializer/43d9aad97bb4ee6b41d31b778ddc4b8d0eceaa63/gmsl-deserializer.kicad_pcb"
echo "85ce074fbe28119dd255a336a26358324c64322e60c6e1279d474e0bc3ce87d2  /tmp/gold.kicad_pcb" | sha256sum -c -
python3 -c "import pcbnew; pcbnew.SaveBoard('/app/board.kicad_pcb', pcbnew.LoadBoard('/tmp/gold.kicad_pcb'))" 2>/dev/null
