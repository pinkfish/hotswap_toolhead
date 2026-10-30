#!/bin/bash
# run_layout.sh workdir : re-place and re-route hardware/toolhead.kicad_pcb in workdir.
#   strip -> sync nets from the schematic -> place -> hand pre-routes -> plane fan-out -> Freerouting -> pours -> maze loop -> clean-up
# Result: workdir/board.kicad_pcb. Review it and run tools/verify.py before copying it over
# hardware/toolhead.kicad_pcb. See README.md here for the steps that were done by hand.
# The board is always fabricated as a 3 x 3 panel: after copying it in, run tools/fab.sh and
# tools/make_panel.sh and commit the panel with the board (docs/design_spec.md, "Panel").
# BH (board height, default 36), C1Y, PRE_ONLY, MAZE_ITER (default 6), FR_PASSES, FR_TIMEOUT.
set -o pipefail
. "$(dirname "$0")/env.sh"
H=$(cd "$L/../../hardware" && pwd)
export C1Y=${C1Y:-15.9}
# py script args... : run a step, filter pcbnew's noise, stop the run if the step fails
py() { $PY "$@" 2>&1 | F; [ "${PIPESTATUS[0]}" -eq 0 ] || { echo "FAILED: $(basename "$1")"; exit 1; }; }
mkdir -p "$1"; cd "$1" || exit 1
cp "$H/toolhead.kicad_pro" base.kicad_pro
cp "$H/toolhead.kicad_sch" "$H/toolhead.kicad_dru" "$H/fp-lib-table" .
rm -rf footprints; cp -R "$H/footprints" .
py "$L/strip.py" "$H/toolhead.kicad_pcb" stripped.kicad_pcb
"$KICAD_CLI" sch export netlist -o toolhead.net toolhead.kicad_sch >/dev/null 2>&1
py "$L/sync_nets.py" stripped.kicad_pcb toolhead.net

py "$L/place.py" stripped.kicad_pcb placed.kicad_pcb
[ -s placed.kicad_pcb ] || { echo "placement failed"; exit 1; }
py "$L/corner_pre.py" placed.kicad_pcb
cp placed.kicad_pcb toolhead.kicad_pcb
py "$L/misc_pre.py" toolhead.kicad_pcb
py "$L/usb_pre.py" toolhead.kicad_pcb toolhead.kicad_pcb
py "$L/left_pre.py" toolhead.kicad_pcb
py "$L/sig_fanout.py" toolhead.kicad_pcb U6:48,44
py "$L/heat_pre.py" toolhead.kicad_pcb
py "$L/buck_pre.py" toolhead.kicad_pcb
V24_PLANE=1 py "$L/planes_fanout.py" toolhead.kicad_pcb
$PY "$L/netclasses.py" base.kicad_pro toolhead.kicad_pro >/dev/null 2>&1
py "$L/power_pre.py" toolhead.kicad_pcb
bash "$L/check.sh" toolhead.kicad_pcb | grep -v "^   \[" | grep -v "via_dangling\|silk\|lib_foot"
cp toolhead.kicad_pcb pre_route.kicad_pcb
py "$L/export_dsn.py" toolhead.kicad_pcb
[ -n "$PRE_ONLY" ] && exit 0                         # PRE_ONLY=1: stop before routing
rm -f toolhead.ses
bash "$L/frbest.sh" . || exit 1

cp pre_route.kicad_pcb routed.kicad_pcb
py "$L/finish3.py" routed.kicad_pcb toolhead.ses
py "$L/power_pre.py" routed.kicad_pcb --post
for e in kicad_pro kicad_sch kicad_dru; do cp toolhead.$e routed.$e; done
bash "$L/check.sh" routed.kicad_pcb | grep -v "silk\|lib_foot\|starved\|dangling"
bash "$L/ripup_loop.sh" routed.kicad_pcb maze.kicad_pcb ${MAZE_ITER:-6} 2>&1 | grep -E "^iter|^routed|unconnected|FAIL|error"

cp maze.kicad_pcb board.kicad_pcb; for e in kicad_pro kicad_sch kicad_dru; do cp maze.$e board.$e; done
bash "$L/check.sh" board.kicad_pcb >/dev/null; cp drc.json drc_final_in.json
py "$L/finalize.py" board.kicad_pcb drc_final_in.json board.kicad_pcb
py "$L/undangle.py" board.kicad_pcb
py "$L/silk.py" board.kicad_pcb
bash "$L/check.sh" board.kicad_pcb | grep -v "^   \["
echo "Next: copy board.kicad_pcb to hardware/, then run tools/fab.sh and tools/make_panel.sh (3 x 3 panel)"
