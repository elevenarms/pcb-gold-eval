#!/bin/bash
# 3D views of the gold boards for the project page. Runs kicad-cli in the pinned image, then gltfpack (meshopt).
# Usage: tools/export_glb.sh   -> site/assets/glb/<id>.glb and <id>-hs.glb (high-speed nets only)
set -euo pipefail
cd "$(dirname "$0")/.."
IMG=$(python3 -c "import tomllib;print(tomllib.load(open('pins.toml','rb'))['env']['kicad_image'])")
mkdir -p site/assets/glb build/glb
# id | zones? | high-speed net filter (kicad-cli wildcard)
while IFS='|' read -r id zones hs; do
  z=""; [ "$zones" = y ] && z="--include-zones"
  docker run --rm --platform linux/amd64 -v "$PWD":/w -w /w "$IMG" sh -c "
    kicad-cli pcb export glb -f --no-components --include-tracks --include-pads --include-inner-copper --include-silkscreen --include-soldermask $z -o build/glb/$id.glb boards/$id/board.kicad_pcb >/dev/null &&
    kicad-cli pcb export glb -f --no-components --no-board-body --include-tracks --include-pads --include-inner-copper --net-filter '$hs' -o build/glb/$id-hs.glb boards/$id/board.kicad_pcb >/dev/null"
  for f in "$id" "$id-hs"; do npx -y gltfpack@0.25.0 -i build/glb/$f.glb -o site/assets/glb/$f.glb -cc -kn >/dev/null; done
  echo "$id: $(du -h site/assets/glb/$id.glb | cut -f1) full, $(du -h site/assets/glb/$id-hs.glb | cut -f1) high-speed"
done <<'LIST'
signal-integrity-test-board|y|*
m2-pcie-adapter|y|*Data_*
hdmi-mipi-bridge|y|*HDMI*
jetson-orin-baseboard|n|*PCIE*
rdimm-ddr5-tester|n|*DQ*
LIST
