#!/bin/bash
# Verifier: re-fetch the gold board at its pinned commit, check sha256, score the agent's board against it.
set -uo pipefail
mkdir -p /logs/verifier /tmp/v && cd /tmp/v
base="https://raw.githubusercontent.com/antmicro/sodimm-ddr5-tester/05b265a75b87d63862323082bfdcb62949d22647"
curl -fsSL -o gold.kicad_pcb "$base/sodimm-ddr5-tester.kicad_pcb" && echo "6808d7b01dd8b5896b0a920ff73b11bf673f59eeb4d709babf0770d8aa2a1904  gold.kicad_pcb" | sha256sum -c - || { echo '{"reward": 0}' > /logs/verifier/reward.json; exit 0; }
curl -fsSL -o gold.kicad_pro "$base/sodimm-ddr5-tester.kicad_pro" && echo "b44e08f8b5b86ffbf57461ac990108af44d95d56929989ff3af5128a83fa6e83  gold.kicad_pro" | sha256sum -c - || { echo '{"reward": 0}' > /logs/verifier/reward.json; exit 0; }
curl -fsSL -o gold.kicad_dru "$base/sodimm-ddr5-tester.kicad_dru" && echo "c552d5fb67e706fb6015f2da7d7fdc2e7a7453747f879d5a5c56a7ff7e512b00  gold.kicad_dru" | sha256sum -c - || { echo '{"reward": 0}' > /logs/verifier/reward.json; exit 0; }

cp /app/board.kicad_pro /tmp/v/cand.kicad_pro 2>/dev/null || cp gold.kicad_pro cand.kicad_pro
[ -f gold.kicad_dru ] && cp gold.kicad_dru cand.kicad_dru
if [ ! -s /app/board.kicad_pcb ]; then echo '{"reward": 0}' > /logs/verifier/reward.json; exit 0; fi
cp /app/board.kicad_pcb cand.kicad_pcb
python3 /tests/pcbeval.py score gold.kicad_pcb cand.kicad_pcb /tests/meta.json /logs/verifier/reward.json \
  2>/dev/null | tee /logs/verifier/detail.json || echo '{"reward": 0}' > /logs/verifier/reward.json
