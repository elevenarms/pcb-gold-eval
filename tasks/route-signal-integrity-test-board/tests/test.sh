#!/bin/bash
# Verifier: re-fetch the gold board at its pinned commit, check sha256, score the agent's board against it.
set -uo pipefail
mkdir -p /logs/verifier /tmp/v && cd /tmp/v
base="https://raw.githubusercontent.com/antmicro/signal-integrity-test-board/de0b5922c372481bb146cbd1d0a9f3b7e97c124a"
curl -fsSL -o gold.kicad_pcb "$base/si-simulation-test-board.kicad_pcb" && echo "ad22910fb65d87b9506a860a2fc9a6ad8ddb0af7743be3a9df40e4edd2c2a318  gold.kicad_pcb" | sha256sum -c - || { echo '{"reward": 0}' > /logs/verifier/reward.json; exit 0; }
curl -fsSL -o gold.kicad_pro "$base/si-simulation-test-board.kicad_pro" && echo "f309d6a9f5a0555fc0ad1d05388b3b4b309863cbff8b0976b562579bd705b209  gold.kicad_pro" | sha256sum -c - || { echo '{"reward": 0}' > /logs/verifier/reward.json; exit 0; }

cp /app/board.kicad_pro /tmp/v/cand.kicad_pro 2>/dev/null || cp gold.kicad_pro cand.kicad_pro
[ -f gold.kicad_dru ] && cp gold.kicad_dru cand.kicad_dru
if [ ! -s /app/board.kicad_pcb ]; then echo '{"reward": 0}' > /logs/verifier/reward.json; exit 0; fi
cp /app/board.kicad_pcb cand.kicad_pcb
python3 /tests/pcbeval.py score gold.kicad_pcb cand.kicad_pcb /tests/meta.json /logs/verifier/reward.json \
  2>/dev/null | tee /logs/verifier/detail.json || echo '{"reward": 0}' > /logs/verifier/reward.json
