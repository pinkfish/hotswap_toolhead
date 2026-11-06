#!/bin/bash
# run_stack.sh logic|power workdir : lay out one board of the two-board stack from its schematic.
#   netlist -> from_netlist.py (footprints from the donor board, SRC) -> place.py (plan_<board>.py)
#   -> pre-routes, plane fan-out, power pours -> Freerouting -> pours -> maze loop -> clean-up
# SRC: the donor board whose footprints carry over (default: the single 27 x 36 board,
#   git show narrow-27:hardware/toolhead.kicad_pcb > src27.kicad_pcb). BW/BH: board size
#   (default 27 x 27, both boards the same, so they stack). HARD: nets maze-routed and locked
#   before Freerouting. PRE_ONLY, MAZE_ITER, FR_PASSES, FR_TIMEOUT as in run_layout.sh.
# The work directory keeps the old file names (toolhead.kicad_*); the result is board.kicad_pcb.
set -o pipefail
. "$(dirname "$0")/env.sh"
H=$(cd "$L/../../hardware" && pwd)
B=$1; NAME=toolhead_$B
[ -f "$H/$NAME.kicad_sch" ] || { echo "usage: run_stack.sh logic|power workdir"; exit 1; }
export BW=${BW:-27} BH=${BH:-27}
py() { $PY "$@" 2>&1 | F; [ "${PIPESTATUS[0]}" -eq 0 ] || { echo "FAILED: $(basename "$1")"; exit 1; }; }
SRC=$(cd "$(dirname "${SRC:?set SRC to the donor board}")" && pwd)/$(basename "$SRC")
mkdir -p "$2"; cd "$2" || exit 1
cp "$H/$NAME.kicad_pro" base.kicad_pro
cp "$H/$NAME.kicad_sch" toolhead.kicad_sch; cp "$H/$NAME.kicad_dru" toolhead.kicad_dru
cp "$H/fp-lib-table" .; rm -rf footprints; cp -R "$H/footprints" .
"$KICAD_CLI" sch export netlist -o toolhead.net toolhead.kicad_sch >/dev/null 2>&1
py "$L/from_netlist.py" toolhead.net "$SRC" netlist.kicad_pcb
# the logic board takes the donor's routed MCU corner, turned with U6
[ "$B" = logic ] && py "$L/corner_import.py" netlist.kicad_pcb "$SRC"
PLAN_FILE="$L/plan_$B.py" py "$L/place.py" netlist.kicad_pcb placed.kicad_pcb
# J3's pads reach to 0.68 mm from the edge: its courtyard is cut to pads and body plus 0.25 mm,
# clear of the panel's mouse bites
[ "$B" = logic ] && py "$L/crtyd_trim.py" placed.kicad_pcb J3=0.25
cp placed.kicad_pcb toolhead.kicad_pcb
$PY "$L/netclasses.py" base.kicad_pro toolhead.kicad_pro >/dev/null 2>&1
py "$L/misc_pre.py" toolhead.kicad_pcb
# the imported MCU corner's copper gives way to anything placed on it
[ "$B" = logic ] && { bash "$L/check.sh" toolhead.kicad_pcb >/dev/null; py "$L/declash.py" toolhead.kicad_pcb drc.json; }
# the USB pair (and SWCLK, which it boxes in) from J5 to U5 and U6
[ "$B" = logic ] && py "$L/usb_stack_pre.py" toolhead.kicad_pcb
# CAN_H/CAN_L from U3 up to J1, and TX/RX across under the MCU corner to U6
[ "$B" = logic ] && py "$L/can_stack_pre.py" toolhead.kicad_pcb
# the logic board keeps the 27 x 36 board's power input (J1, F1, Q1, D1): same pours
[ "$B" = logic ] && NARROW=1 py "$L/power_pre.py" toolhead.kicad_pcb
# In2: the power board keeps a whole +24V plane. On the logic board +24V only runs along the top
# edge, from Q1's source to J3 pins 1/2, so it is a top-layer pour there (clear of J1's pins) and
# In2 is a third routing layer
if [ "$B" = logic ]; then
  SKIP_ROUTED=1 V24_TOP=${V24_TOP:-"0.6,0.4;26.6,0.4;26.6,4.3;8.6,4.3;8.6,7.1;4.9,7.1;4.9,4.3;0.6,4.3"} py "$L/planes_fanout.py" toolhead.kicad_pcb
else
  V24_PLANE=1 py "$L/planes_fanout.py" toolhead.kicad_pcb
fi
if [ -n "$HARD" ]; then
  bash "$L/check.sh" toolhead.kicad_pcb >/dev/null; cp drc.json drc_hard.json
  ONLY=$HARD ORDER=$HARD LOCK=1 $PY "$L/maze.py" toolhead.kicad_pcb drc_hard.json 2>&1 | grep -E "^(FAIL|routed)"
fi
bash "$L/check.sh" toolhead.kicad_pcb | grep -v "^   \[" | grep -v "via_dangling\|silk\|lib_foot"
cp toolhead.kicad_pcb pre_route.kicad_pcb
py "$L/export_dsn.py" toolhead.kicad_pcb
[ -n "$PRE_ONLY" ] && exit 0
rm -f toolhead.ses
bash "$L/frbest.sh" . || exit 1

cp pre_route.kicad_pcb routed.kicad_pcb
py "$L/finish3.py" routed.kicad_pcb toolhead.ses
[ "$B" = logic ] && NARROW=1 py "$L/power_pre.py" routed.kicad_pcb --post
for e in kicad_pro kicad_sch kicad_dru; do cp toolhead.$e routed.$e; done
bash "$L/check.sh" routed.kicad_pcb | grep -v "silk\|lib_foot\|starved\|dangling"
bash "$L/ripup_loop.sh" routed.kicad_pcb maze.kicad_pcb ${MAZE_ITER:-6} 2>&1 | grep -E "^iter|^routed|unconnected|FAIL|error"

cp maze.kicad_pcb board.kicad_pcb; for e in kicad_pro kicad_sch kicad_dru; do cp maze.$e board.$e; done
bash "$L/check.sh" board.kicad_pcb >/dev/null; cp drc.json drc_final_in.json
py "$L/finalize.py" board.kicad_pcb drc_final_in.json board.kicad_pcb
py "$L/undangle.py" board.kicad_pcb
py "$L/island_vias.py" board.kicad_pcb
bash "$L/check.sh" board.kicad_pcb >/dev/null; py "$L/finalize.py" board.kicad_pcb drc.json board.kicad_pcb
py "$L/undangle.py" board.kicad_pcb
py "$L/silk.py" board.kicad_pcb
bash "$L/check.sh" board.kicad_pcb | grep -v "^   \["
echo "Next: copy board.kicad_pcb to hardware/$NAME.kicad_pcb, run tools/check_stack.py, tools/fab.sh and tools/make_panel.sh"
