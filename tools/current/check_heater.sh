#!/bin/bash
# check_heater.sh [amps] : DC current flow along the heater path on both stack boards, at the full
# load current (default 4.7 A: a 100 W heater at 24 V plus a 0.5 A fan). For each stretch of copper
# it prints the resistance, the loss, each layer's peak current per mm of width (smoothed over
# 0.5 mm) and any via carrying more than 1 A.
#   export_net.py runs in KiCad's Python; current_solve.py needs numpy, scipy and Pillow, from the
#   Python in CURRENT_PY (default python3), e.g. a venv: python3 -m venv v && v/bin/pip install
#   numpy scipy pillow.
# Copper as JLCPCB builds a 4-layer board by default: 1 oz outer, 0.5 oz inner (INNER_UM=35 for
# 1 oz), 18 um via plating. Aim for no more than about 3 A/mm on outer layers and 1.5 A/mm on
# 0.5 oz inner layers outside the first 0.5 mm round a pad, and about 1.5 A per 0.3 mm via.
set -e
D=$(cd "$(dirname "$0")" && pwd); H=$D/../../hardware
KP=${KICAD_PY:-/Applications/KiCad/KiCad.app/Contents/Frameworks/Python.framework/Versions/Current/bin/python3}
CP=${CURRENT_PY:-python3}
A=${1:-4.7}
T=$(mktemp -d); trap 'rm -rf "$T"' EXIT
while read -r board net src sink; do
  "$KP" "$D/export_net.py" "$H/toolhead_$board.kicad_pcb" "$net" "$T/n.json" >/dev/null 2>&1
  echo "== $board"
  VIA_SHOW=1 "$CP" "$D/current_solve.py" "$T/n.json" "$A" "$src" "$sink" | grep -v -E "peak 0\.00|: 0\.[0-9]+ A$"
done <<'PATHS'
logic /VIN_RAW J1:1 F1:1
logic /VIN_F F1:2 Q1:5
logic /+24V Q1:1,Q1:2,Q1:3 J3:1,J3:2
logic /GND J3:3,J3:4,J3:7 J1:2
power /+24V J4:1,J4:2 J2:1
power /HEAT_N J2:5 Q2:5
power /GND Q2:1,Q2:2,Q2:3 J4:3,J4:4,J4:7
PATHS
