#!/bin/bash
# Verifier: re-fetch the gold board at its pinned commit, check sha256, score the agent's board against it.
set -uo pipefail
mkdir -p /logs/verifier /tmp/v && cd /tmp/v
base="https://raw.githubusercontent.com/antmicro/rdimm-ddr4-tester/e7c85ebc9eb35645a6c467b0362270a5792d2726"
curl -fsSL -o gold.kicad_pcb "$base/data-center-rdimm-ddr4-tester.kicad_pcb" && echo "de397b73b29dec7a4f3e44868bc6abfed0f3be6622e27395ab272d0d0eae6b79  gold.kicad_pcb" | sha256sum -c - || { echo '{"reward": 0}' > /logs/verifier/reward.json; exit 0; }
curl -fsSL -o gold.kicad_pro "$base/data-center-rdimm-ddr4-tester.kicad_pro" && echo "59464410ccf42b2238a0869bc79eda7b23f15a5c373749ae51c65c5b5fac7a50  gold.kicad_pro" | sha256sum -c - || { echo '{"reward": 0}' > /logs/verifier/reward.json; exit 0; }
curl -fsSL -o gold.kicad_dru "$base/data-center-rdimm-ddr4-tester.kicad_dru" && echo "59d9354b7dc08197c6c66dba4510e19d3dcc3a23b4157217070867b566c53f41  gold.kicad_dru" | sha256sum -c - || { echo '{"reward": 0}' > /logs/verifier/reward.json; exit 0; }

cp /app/board.kicad_pro /tmp/v/cand.kicad_pro 2>/dev/null || cp gold.kicad_pro cand.kicad_pro
[ -f gold.kicad_dru ] && cp gold.kicad_dru cand.kicad_dru
if [ ! -s /app/board.kicad_pcb ]; then echo '{"reward": 0}' > /logs/verifier/reward.json; exit 0; fi
cp /app/board.kicad_pcb cand.kicad_pcb
python3 /tests/pcbeval.py score gold.kicad_pcb cand.kicad_pcb /tests/meta.json /logs/verifier/reward.json \
  2>/dev/null | tee /logs/verifier/detail.json || echo '{"reward": 0}' > /logs/verifier/reward.json
