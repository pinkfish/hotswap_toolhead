#!/bin/bash
# fab.sh : regenerate gerber/ (Gerbers, drill, JLCPCB BOM + CPL) from hardware/toolhead.kicad_pcb
# KICAD_CLI overrides the kicad-cli path.
R=$(cd "$(dirname "$0")/.." && pwd)
K=${KICAD_CLI:-/Applications/KiCad/KiCad.app/Contents/MacOS/kicad-cli}
cd "$R" || exit 1
rm -f gerber/*.gtl gerber/*.gbl gerber/*.g1 gerber/*.g2 gerber/*.gtp gerber/*.gbp gerber/*.gto gerber/*.gbo gerber/*.gts gerber/*.gbs gerber/*.gm1 gerber/*.gbrjob gerber/*.drl
"$K" pcb export gerbers -o gerber/ --layers F.Cu,In1.Cu,In2.Cu,B.Cu,F.Paste,B.Paste,F.Silkscreen,B.Silkscreen,F.Mask,B.Mask,Edge.Cuts --subtract-soldermask hardware/toolhead.kicad_pcb >/dev/null 2>&1
"$K" pcb export drill -o gerber/ --format excellon --excellon-separate-th --drill-origin absolute --excellon-units mm hardware/toolhead.kicad_pcb >/dev/null 2>&1
pos=$(mktemp); trap 'rm -f "$pos"' EXIT
"$K" pcb export pos -o "$pos" --format csv --units mm --side both --exclude-dnp hardware/toolhead.kicad_pcb >/dev/null 2>&1
python3 - "$pos" <<'PY'
import csv, sys
bom = {d.strip() for r in csv.DictReader(open('hardware/bom_jlcpcb.csv')) for d in r['Designator'].split(',')}
rows = [r for r in csv.DictReader(open(sys.argv[1])) if r['Ref'] in bom]   # solder-jumper pads: nothing to place
with open('gerber/toolhead-cpl-jlcpcb.csv', 'w', newline='') as fh:
    w = csv.writer(fh); w.writerow(['Designator', 'Mid X', 'Mid Y', 'Layer', 'Rotation'])
    for r in rows:
        w.writerow([r['Ref'], f"{float(r['PosX']):.3f}mm", f"{float(r['PosY']):.3f}mm", 'Top' if r['Side'] == 'top' else 'Bottom', f"{float(r['Rot']):g}"])
print(len(rows), 'placements', sum(r['Side'] == 'bottom' for r in rows), 'bottom')
PY
cp hardware/bom_jlcpcb.csv gerber/toolhead-bom-jlcpcb.csv
