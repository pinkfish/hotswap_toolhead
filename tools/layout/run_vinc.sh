#!/bin/bash
# run_vinc.sh workdir : the board with the vertical XT30 and USB-C, from the routed 27 x 36 one.
#   blocks.py (blocks_vertical.py) swaps in the vertical connectors and moves everything below
#   them up SHIFT mm (default 2) with its own copper -> place.py places the parts that were under
#   the old connectors (plan_vinc.py) -> plane fan-out -> Freerouting -> pours -> maze loop -> clean-up
# Start from the 27 x 36 board: SRC (git show narrow-27:hardware/toolhead.kicad_pcb >
# src27.kicad_pcb). The board is 27 x (36 - SHIFT). PRE_ONLY, MAZE_ITER, FR_PASSES, FR_TIMEOUT as
# in run_layout.sh, HARD (nets maze-routed before Freerouting).
set -o pipefail
. "$(dirname "$0")/env.sh"
H=$(cd "$L/../../hardware" && pwd)
export SHIFT=${SHIFT:-2} BW=27 NARROW=1
export BH=$(python3 -c "print(36 - $SHIFT)")
py() { $PY "$@" 2>&1 | F; [ "${PIPESTATUS[0]}" -eq 0 ] || { echo "FAILED: $(basename "$1")"; exit 1; }; }
SRC=$(cd "$(dirname "${SRC:?set SRC to the 27 x 36 board}")" && pwd)/$(basename "$SRC")
mkdir -p "$1"; cd "$1" || exit 1
cp "$H/toolhead.kicad_pro" base.kicad_pro
cp "$H/toolhead.kicad_sch" "$H/toolhead.kicad_dru" "$H/fp-lib-table" .
rm -rf footprints; cp -R "$H/footprints" .

BLOCKS_FILE="$L/blocks_vertical.py" py "$L/blocks.py" "$SRC" blocks.kicad_pcb
PLAN_FILE="$L/plan_vinc.py" py "$L/place.py" blocks.kicad_pcb placed.kicad_pcb
cp placed.kicad_pcb toolhead.kicad_pcb
$PY "$L/netclasses.py" base.kicad_pro toolhead.kicad_pro >/dev/null 2>&1
# block copper that now clashes with other blocks, the placed parts or the pour reservations
for i in 1 2 3; do
  bash "$L/check.sh" toolhead.kicad_pcb >/dev/null; py "$L/declash.py" toolhead.kicad_pcb drc.json
done
SKIP_ROUTED=1 V24_PLANE=1 py "$L/planes_fanout.py" toolhead.kicad_pcb
# the nets Freerouting always left open, maze-routed and locked first (HARD= to skip)
HARD=${HARD-/VREFP,/NRST,/+3V3,/SENS_IN,/GATE_12V,/USB_D_N,/FAN_PWM}
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
# vias the clean-up left on one layer, and the stubs they leave
bash "$L/check.sh" board.kicad_pcb >/dev/null; py "$L/finalize.py" board.kicad_pcb drc.json board.kicad_pcb
py "$L/undangle.py" board.kicad_pcb
py "$L/silk.py" board.kicad_pcb
bash "$L/check.sh" board.kicad_pcb | grep -v "^   \["
echo "Next: copy board.kicad_pcb to hardware/, then run tools/fab.sh and tools/make_panel.sh (3 x 3 panel)"
