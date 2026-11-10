#!/bin/bash
# fab.sh : regenerate gerber/usb/ (Gerbers, drill, JLCPCB BOM + CPL) from
# hardware/toolhead_usb.kicad_pcb.
# KICAD_CLI and KICAD_PY override the kicad-cli and KiCad Python paths.
R=$(cd "$(dirname "$0")/.." && pwd)
K=${KICAD_CLI:-/Applications/KiCad/KiCad.app/Contents/MacOS/kicad-cli}
PY=${KICAD_PY:-/Applications/KiCad/KiCad.app/Contents/Frameworks/Python.framework/Versions/Current/bin/python3}
cd "$R" || exit 1
for b in usb; do
  N=toolhead_$b; G=gerber/$b
  rm -rf $G; mkdir -p $G
  "$K" pcb export gerbers -o $G/ --layers F.Cu,In1.Cu,In2.Cu,B.Cu,F.Paste,B.Paste,F.Silkscreen,B.Silkscreen,F.Mask,B.Mask,Edge.Cuts --subtract-soldermask hardware/$N.kicad_pcb >/dev/null 2>&1
  "$K" pcb export drill -o $G/ --format excellon --excellon-separate-th --drill-origin absolute --excellon-units mm hardware/$N.kicad_pcb >/dev/null 2>&1
  # CPL fitted to JLCPCB's own footprints (see tools/jlc_cpl.py); BOM parts only, so the bare
  # solder-jumper pads have nothing to place
  "$PY" tools/jlc_cpl.py hardware/$N.kicad_pcb $G/$N-cpl-jlcpcb.csv 2>&1 | grep -v -e Debug -e assert -e leak
  cp hardware/$N-bom-jlcpcb.csv $G/
  (cd $G && zip -q $N-gerbers.zip *.g* *.drl)
done
