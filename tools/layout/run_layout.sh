#!/bin/bash
# run_layout.sh workdir : re-place and re-route hardware/toolhead.kicad_pcb in workdir.
#   strip -> place -> hand pre-routes -> plane fan-out -> Freerouting -> pours -> maze loop -> clean-up
# Result: workdir/board.kicad_pcb. Review it and run tools/verify.py before copying it over
# hardware/toolhead.kicad_pcb. See README.md here for the steps that were done by hand.
# BH (board height, default 33), C1Y, MAZE_ITER (default 6), FR_PASSES, FR_TIMEOUT.
set -o pipefail
. "$(dirname "$0")/env.sh"
H=$(cd "$L/../../hardware" && pwd)
export C1Y=${C1Y:-14.6}
mkdir -p "$1"; cd "$1" || exit 1
cp "$H/toolhead.kicad_pro" base.kicad_pro
cp "$H/toolhead.kicad_sch" "$H/toolhead.kicad_dru" "$H/fp-lib-table" .
rm -rf footprints; cp -R "$H/footprints" .
$PY "$L/strip.py" "$H/toolhead.kicad_pcb" stripped.kicad_pcb 2>&1 | F

$PY "$L/place.py" stripped.kicad_pcb placed.kicad_pcb 2>&1 | F | grep -v "^  "
$PY "$L/corner_pre.py" placed.kicad_pcb 2>&1 | F
cp placed.kicad_pcb toolhead.kicad_pcb
$PY "$L/misc_pre.py" toolhead.kicad_pcb 2>&1 | F
$PY "$L/usb_pre.py" toolhead.kicad_pcb toolhead.kicad_pcb 2>&1 | F
$PY "$L/th_pre.py" toolhead.kicad_pcb th 2>&1 | F
$PY "$L/left_pre.py" toolhead.kicad_pcb 2>&1 | F
$PY "$L/sig_fanout.py" toolhead.kicad_pcb U6:19,20,47,48,44 2>&1 | F | tail -1
$PY "$L/th_pre.py" toolhead.kicad_pcb pwm 2>&1 | F
$PY "$L/buck_pre.py" toolhead.kicad_pcb 2>&1 | F
V24_PLANE=1 $PY "$L/planes_fanout.py" toolhead.kicad_pcb 2>&1 | F
$PY "$L/netclasses.py" base.kicad_pro toolhead.kicad_pro >/dev/null 2>&1
$PY "$L/power_pre.py" toolhead.kicad_pcb 2>&1 | F
bash "$L/check.sh" toolhead.kicad_pcb | grep -v "^   \[" | grep -v "via_dangling\|silk\|lib_foot"
cp toolhead.kicad_pcb pre_route.kicad_pcb
$PY "$L/export_dsn.py" toolhead.kicad_pcb 2>&1 | F | tail -1
rm -f toolhead.ses
bash "$L/frbest.sh" . || exit 1

cp pre_route.kicad_pcb routed.kicad_pcb
$PY "$L/finish3.py" routed.kicad_pcb toolhead.ses 2>&1 | F
$PY "$L/power_pre.py" routed.kicad_pcb --post 2>&1 | F
for e in kicad_pro kicad_sch kicad_dru; do cp toolhead.$e routed.$e; done
bash "$L/check.sh" routed.kicad_pcb | grep -v "silk\|lib_foot\|starved\|dangling"
bash "$L/ripup_loop.sh" routed.kicad_pcb maze.kicad_pcb ${MAZE_ITER:-6} 2>&1 | grep -E "^iter|^routed|unconnected|FAIL|error"

cp maze.kicad_pcb board.kicad_pcb; for e in kicad_pro kicad_sch kicad_dru; do cp maze.$e board.$e; done
bash "$L/check.sh" board.kicad_pcb >/dev/null; cp drc.json drc_final_in.json
$PY "$L/finalize.py" board.kicad_pcb drc_final_in.json board.kicad_pcb 2>&1 | F
$PY "$L/undangle.py" board.kicad_pcb 2>&1 | F | tail -1
$PY "$L/silk.py" board.kicad_pcb 2>&1 | F | tail -1
bash "$L/check.sh" board.kicad_pcb | grep -v "^   \["
