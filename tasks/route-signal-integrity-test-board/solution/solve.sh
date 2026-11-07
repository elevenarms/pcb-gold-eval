#!/bin/bash
# Oracle: restore the human-routed copper (proves the verifier scores the gold master at 1.0).
set -euo pipefail
curl -fsSL -o /tmp/gold.kicad_pcb "https://raw.githubusercontent.com/antmicro/signal-integrity-test-board/de0b5922c372481bb146cbd1d0a9f3b7e97c124a/si-simulation-test-board.kicad_pcb"
echo "ad22910fb65d87b9506a860a2fc9a6ad8ddb0af7743be3a9df40e4edd2c2a318  /tmp/gold.kicad_pcb" | sha256sum -c -
python3 -c "import pcbnew; pcbnew.SaveBoard('/app/board.kicad_pcb', pcbnew.LoadBoard('/tmp/gold.kicad_pcb'))" 2>/dev/null
