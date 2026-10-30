#!/bin/bash
# fab.sh : regenerate gerber/ (Gerbers, drill, JLCPCB BOM + CPL) from hardware/toolhead.kicad_pcb
# KICAD_CLI and KICAD_PY override the kicad-cli and KiCad Python paths.
R=$(cd "$(dirname "$0")/.." && pwd)
K=${KICAD_CLI:-/Applications/KiCad/KiCad.app/Contents/MacOS/kicad-cli}
PY=${KICAD_PY:-/Applications/KiCad/KiCad.app/Contents/Frameworks/Python.framework/Versions/Current/bin/python3}
cd "$R" || exit 1
rm -f gerber/*.gtl gerber/*.gbl gerber/*.g1 gerber/*.g2 gerber/*.gtp gerber/*.gbp gerber/*.gto gerber/*.gbo gerber/*.gts gerber/*.gbs gerber/*.gm1 gerber/*.gbrjob gerber/*.drl
"$K" pcb export gerbers -o gerber/ --layers F.Cu,In1.Cu,In2.Cu,B.Cu,F.Paste,B.Paste,F.Silkscreen,B.Silkscreen,F.Mask,B.Mask,Edge.Cuts --subtract-soldermask hardware/toolhead.kicad_pcb >/dev/null 2>&1
"$K" pcb export drill -o gerber/ --format excellon --excellon-separate-th --drill-origin absolute --excellon-units mm hardware/toolhead.kicad_pcb >/dev/null 2>&1
# CPL fitted to JLCPCB's own footprints (see tools/jlc_cpl.py); BOM parts only, so the bare
# solder-jumper pads have nothing to place
"$PY" tools/jlc_cpl.py hardware/toolhead.kicad_pcb gerber/toolhead-cpl-jlcpcb.csv 2>&1 | grep -v -e Debug -e assert
cp hardware/bom_jlcpcb.csv gerber/toolhead-bom-jlcpcb.csv
