#!/bin/bash
# Freerouting baseline sweep: boards x max-passes x seeds, 3 containers in parallel. Results: data/baselines/*.json
set -uo pipefail
cd "$(dirname "$0")/.."
docker image inspect pcb-gold-eval-base >/dev/null 2>&1 || docker build --platform linux/amd64 -t pcb-gold-eval-base -f docker/Dockerfile.base docker
mkdir -p data/baselines
run() { b=$1; p=$2; s=$3; o=data/baselines/${b}_p${p}_s${s}.json; [ -s "$o" ] && return
  docker run --rm --platform linux/amd64 -m 4g -v "$PWD":/w -w /w pcb-gold-eval-base \
    timeout 5400 python3 tools/baseline_freerouting.py "$b" "$p" "$s" "$o" 2>/dev/null | tail -1; }
export -f run
for b in ${BOARDS:-signal-integrity-test-board m2-pcie-adapter hdmi-mipi-bridge gmsl-deserializer jetson-orin-baseboard}; do
  for p in ${PASSES:-1 3 10}; do for s in ${SEEDS:-1 2}; do echo "$b $p $s"; done; done; done |
  xargs -P ${PAR:-3} -L 1 bash -c 'run "$0" "$1" "$2"'
