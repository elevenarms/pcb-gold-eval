#!/bin/bash
# Verifier: re-fetch the gold board at its pinned commit, check sha256, score the agent's board against it.
set -uo pipefail
mkdir -p /logs/verifier /tmp/v && cd /tmp/v
base="https://raw.githubusercontent.com/antmicro/rdimm-ddr5-tester/6bd485778de747d0e34551c4c34d2419e2c2d5b9"
curl -fsSL -o gold.kicad_pcb "$base/data-center-rdimm-ddr5-tester.kicad_pcb" && echo "2d5e5a547689ca3fd14682c21f077e658007f5245c473c6598c4785c8adaa6dc  gold.kicad_pcb" | sha256sum -c - || { echo '{"reward": 0}' > /logs/verifier/reward.json; exit 0; }
curl -fsSL -o gold.kicad_pro "$base/data-center-rdimm-ddr5-tester.kicad_pro" && echo "bf66809ee42667212c29c0d4f2e704eaa3a93d0c2e9ac9584a86dddd1d173615  gold.kicad_pro" | sha256sum -c - || { echo '{"reward": 0}' > /logs/verifier/reward.json; exit 0; }
curl -fsSL -o gold.kicad_dru "$base/data-center-rdimm-ddr5-tester.kicad_dru" && echo "2ea75f1eda038707dbd8a5e91316a61ed7c9626283c5fd3f2d20943ae0eb9980  gold.kicad_dru" | sha256sum -c - || { echo '{"reward": 0}' > /logs/verifier/reward.json; exit 0; }

cp /app/board.kicad_pro /tmp/v/cand.kicad_pro 2>/dev/null || cp gold.kicad_pro cand.kicad_pro
[ -f gold.kicad_dru ] && cp gold.kicad_dru cand.kicad_dru
if [ ! -s /app/board.kicad_pcb ]; then echo '{"reward": 0}' > /logs/verifier/reward.json; exit 0; fi
cp /app/board.kicad_pcb cand.kicad_pcb
python3 /tests/pcbeval.py score gold.kicad_pcb cand.kicad_pcb /tests/meta.json /logs/verifier/reward.json \
  2>/dev/null | tee /logs/verifier/detail.json || echo '{"reward": 0}' > /logs/verifier/reward.json
