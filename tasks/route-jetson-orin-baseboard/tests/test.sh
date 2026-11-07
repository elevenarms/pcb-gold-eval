#!/bin/bash
# Verifier: re-fetch the gold board at its pinned commit, check sha256, score the agent's board against it.
set -uo pipefail
mkdir -p /logs/verifier /tmp/v && cd /tmp/v
base="https://raw.githubusercontent.com/antmicro/jetson-orin-baseboard/34f0e7f5fbca441191e20ed55d93cf8614e12bed"
curl -fsSL -o gold.kicad_pcb "$base/jetson-orin-baseboard.kicad_pcb" && echo "eaeb87f5bceb46097c8161cf5e990c3609bf667f5a53668f76aa93595bd636ca  gold.kicad_pcb" | sha256sum -c - || { echo '{"reward": 0}' > /logs/verifier/reward.json; exit 0; }
curl -fsSL -o gold.kicad_pro "$base/jetson-orin-baseboard.kicad_pro" && echo "6658f8b150d948bd1b133836cc21424e49e81b04bfceef1d9e4c969606e00935  gold.kicad_pro" | sha256sum -c - || { echo '{"reward": 0}' > /logs/verifier/reward.json; exit 0; }
curl -fsSL -o gold.kicad_dru "$base/jetson-orin-baseboard.kicad_dru" && echo "2139b5445b0bb88f7513be03a9b6f9698699b25cfb5d282e9c0f46505d5bfcc0  gold.kicad_dru" | sha256sum -c - || { echo '{"reward": 0}' > /logs/verifier/reward.json; exit 0; }

cp /app/board.kicad_pro /tmp/v/cand.kicad_pro 2>/dev/null || cp gold.kicad_pro cand.kicad_pro
[ -f gold.kicad_dru ] && cp gold.kicad_dru cand.kicad_dru
if [ ! -s /app/board.kicad_pcb ]; then echo '{"reward": 0}' > /logs/verifier/reward.json; exit 0; fi
cp /app/board.kicad_pcb cand.kicad_pcb
python3 /tests/pcbeval.py score gold.kicad_pcb cand.kicad_pcb /tests/meta.json /logs/verifier/reward.json \
  2>/dev/null | tee /logs/verifier/detail.json || echo '{"reward": 0}' > /logs/verifier/reward.json
