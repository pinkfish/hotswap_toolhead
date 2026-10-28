#!/bin/bash
# ripup_loop.sh in.kicad_pcb out.kicad_pcb [max_iter]  (needs <in>.kicad_pro/.kicad_sch/.kicad_dru alongside)
# Re-runs DRC and maze.py on what is still unconnected. SOFT_ITERS: iterations that may rip up soft routes.
. "$(dirname "$0")/env.sh"
in=$1; out=$2; n=${3:-8}
d=$(dirname "$out"); base=$(basename "$out" .kicad_pcb)
cp "$in" "$out"; for e in kicad_pro kicad_sch kicad_dru; do cp "${in%.kicad_pcb}.$e" "$d/$base.$e"; done
for i in $(seq 1 $n); do
  u=$(bash "$L/check.sh" "$out" | awk '/^unconnected /{print $2}')
  echo "iter $i: unconnected $u"
  [ "$u" = 0 ] && break
  cp "$d/drc.json" "$d/drc_loop.json"
  if [ $i -le ${SOFT_ITERS:-99} ]; then export SOFT=1; else unset SOFT; fi
  $PY "$L/maze.py" "$out" "$d/drc_loop.json" "$out" 2>&1 | grep -E "^(ok|FAIL|ripped|routed)"
done
bash "$L/check.sh" "$out" | grep -v "silk\|lib_foot"
