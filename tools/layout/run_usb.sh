#!/bin/bash
# run_usb.sh workdir : lay out the USB board from its schematic.
#   netlist -> from_netlist.py (footprints from the donor board, SRC) -> corner_import.py (the
#   donor's routed MCU corner, turned with U6 to U6_AT) -> place.py (plan_usb.py) -> plane
#   fan-out -> Freerouting -> pours -> maze loop -> clean-up
# SRC: the donor board, the stack's logic board (git show stack:hardware/toolhead_logic.kicad_pcb
#   > logic.kicad_pcb). BW/BH: board size (default 18 x 23.5). U6_AT: U6's place, "x,y,rot".
#   PRE: pre-route scripts run before the plane fan-out (default usb_pair_pre.py, the USB pair).
#   HARD: nets maze-routed and locked before Freerouting (default none). PRE_ONLY, MAZE_ITER, FR_PASSES,
#   FR_TIMEOUT as in run_layout.sh. The work directory keeps the old file names
#   (toolhead.kicad_*); the result is board.kicad_pcb.
set -o pipefail
. "$(dirname "$0")/env.sh"
H=$(cd "$L/../../hardware" && pwd)
NAME=toolhead_usb
export BW=${BW:-18} BH=${BH:-23.5}
export U6_AT=${U6_AT:-$(awk "BEGIN { print $BW / 2 }"),12.2,90}   # centred
export KEEP=   # no mounting holes
HARD=${HARD-}
PRE=${PRE-usb_pair_pre.py}
py() { $PY "$@" 2>&1 | F; [ "${PIPESTATUS[0]}" -eq 0 ] || { echo "FAILED: $(basename "$1")"; exit 1; }; }
SRC=$(cd "$(dirname "${SRC:?set SRC to the donor board}")" && pwd)/$(basename "$SRC")
mkdir -p "$1"; cd "$1" || exit 1
cp "$H/$NAME.kicad_pro" base.kicad_pro
cp "$H/$NAME.kicad_sch" toolhead.kicad_sch; cp "$H/$NAME.kicad_dru" toolhead.kicad_dru
cp "$H/fp-lib-table" .; rm -rf footprints; cp -R "$H/footprints" .
"$KICAD_CLI" sch export netlist -o toolhead.net toolhead.kicad_sch >/dev/null 2>&1
py "$L/from_netlist.py" toolhead.net "$SRC" netlist.kicad_pcb
py "$L/corner_import.py" netlist.kicad_pcb "$SRC"
PLAN_FILE="$L/plan_usb.py" py "$L/place.py" netlist.kicad_pcb placed.kicad_pcb
cp placed.kicad_pcb toolhead.kicad_pcb
$PY "$L/netclasses.py" base.kicad_pro toolhead.kicad_pro >/dev/null 2>&1
py "$L/misc_pre.py" toolhead.kicad_pcb
# the imported MCU corner's copper gives way to anything placed on it
bash "$L/check.sh" toolhead.kicad_pcb >/dev/null; py "$L/declash.py" toolhead.kicad_pcb drc.json
[ -n "$PRE" ] && for p in $PRE; do py "$L/$p" toolhead.kicad_pcb; done
# In1 GND plane, In2 routed
SKIP_ROUTED=1 py "$L/planes_fanout.py" toolhead.kicad_pcb
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
echo "Next: copy board.kicad_pcb to hardware/$NAME.kicad_pcb, then run tools/fab.sh and tools/make_panel.sh"
