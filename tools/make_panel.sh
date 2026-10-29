#!/bin/zsh
# make_panel.sh - build the 3 x 3 JLCPCB panel from hardware/toolhead.kicad_pcb and its fab files.
#   hardware/panel/toolhead_panel.kicad_pcb   KiKit panel (frame rails, tooling holes, fiducials, mouse bites)
#   gerber/panel/                            Gerbers, drill, zip, JLC BOM + CPL (refs R1_0 ... R1_8)
# Needs KiCad 9 and KiKit (pip install kikit into KiCad's Python).
set -e
cd "${0:A:h}/.."
APP=/Applications/KiCad/KiCad.app/Contents
PY=$APP/Frameworks/Python.framework/Versions/Current/bin/python3
K=$APP/MacOS/kicad-cli
P=hardware/panel
G=gerber/panel
mkdir -p $P $G
cp hardware/toolhead.kicad_pro $P/src.kicad_pro
cp hardware/toolhead.kicad_dru $P/src.kicad_dru
$PY tools/panel_tabs.py hardware/toolhead.kicad_pcb $P/src.kicad_pcb 2>/dev/null
$PY -m kikit.ui panelize -p tools/panel.json $P/src.kicad_pcb $P/toolhead_panel.kicad_pcb 2>&1 | grep -v 'Debug: Adding' || true
rm -f $P/src.kicad_pcb $P/src.kicad_pro $P/src.kicad_dru
# KiKit's fiducials and tooling holes (KiKit_FID_*, KiKit_TO_*) and the bare solder-jumper pads
# (JP1, JP3) have no part to place: keep them out of every BOM and position file, including
# the Fabrication Toolkit's, which JLCPCB rejects when the CPL names parts the BOM lacks
$PY - 2>&1 <<'PY' | grep -v 'Debug\|assert\|leak' || true
import re, pcbnew
f = 'hardware/panel/toolhead_panel.kicad_pcb'
b = pcbnew.LoadBoard(f); n = 0
for fp in b.GetFootprints():
    if re.match(r'KiKit_(FID|TO)_|JP[13]_\d+$', fp.GetReference()):
        fp.SetExcludedFromBOM(True); fp.SetExcludedFromPosFiles(True); n += 1
pcbnew.SaveBoard(f, b)
print(n, 'panel footprints excluded from BOM and position files')
PY
cp hardware/toolhead.kicad_dru $P/toolhead_panel.kicad_dru
# H2's ring is exactly 0.5 mm from the board corner; KiKit's rebuilt outline puts that corner
# 0.0006 mm closer, so the panel allows 0.49 mm there
cat >> $P/toolhead_panel.kicad_dru <<'DRU'

(rule "H2 ring at the panel's board corners"
  (condition "A.memberOfFootprint('H2_*')")
  (constraint edge_clearance (min 0.49mm)))
DRU
rm -rf $G && mkdir -p $G
$K pcb export gerbers -o $G/ --layers F.Cu,In1.Cu,In2.Cu,B.Cu,F.Paste,B.Paste,F.Silkscreen,B.Silkscreen,F.Mask,B.Mask,Edge.Cuts --subtract-soldermask $P/toolhead_panel.kicad_pcb >/dev/null
$K pcb export drill -o $G/ --format excellon --excellon-separate-th --drill-origin absolute --excellon-units mm $P/toolhead_panel.kicad_pcb >/dev/null
$K pcb export pos -o $P/pos.csv --format csv --units mm --side both --exclude-dnp $P/toolhead_panel.kicad_pcb >/dev/null
$PY - <<'PY'
import csv, re
G = 'gerber/panel/'
rows = list(csv.DictReader(open('hardware/bom_jlcpcb.csv')))
base = {d.strip() for r in rows for d in r['Designator'].split(',')}
pos = [r for r in csv.DictReader(open('hardware/panel/pos.csv')) if re.sub(r'_\d+$', '', r['Ref']) in base]
n = {}
for r in pos:
    n.setdefault(re.sub(r'_\d+$', '', r['Ref']), []).append(r['Ref'])
with open(G + 'toolhead_panel-bom-jlcpcb.csv', 'w', newline='') as fh:
    w = csv.writer(fh); w.writerow(['Comment', 'Designator', 'Footprint', 'LCSC Part #'])
    for r in rows:
        refs = [x for d in r['Designator'].split(',') for x in sorted(n[d.strip()], key=lambda s: int(s.rsplit('_', 1)[1]))]
        w.writerow([r['Comment'], ','.join(refs), r['Footprint'], r['LCSC Part #']])
with open(G + 'toolhead_panel-cpl-jlcpcb.csv', 'w', newline='') as fh:
    w = csv.writer(fh); w.writerow(['Designator', 'Mid X', 'Mid Y', 'Layer', 'Rotation'])
    for r in pos:
        w.writerow([r['Ref'], f"{float(r['PosX']):.3f}mm", f"{float(r['PosY']):.3f}mm",
                    'Top' if r['Side'] == 'top' else 'Bottom', f"{float(r['Rot']):g}"])
boards = {r['Ref'].rsplit('_', 1)[1] for r in pos}
print(len(pos), 'placements on', len(boards), 'boards;', len(base), 'parts per board')
PY
rm -f $P/pos.csv
(cd $G && zip -q toolhead_panel-gerbers.zip *.g* *.drl)
$K pcb drc --severity-error --format json -o $P/drc.json $P/toolhead_panel.kicad_pcb >/dev/null
$PY -c "import json; d=json.load(open('$P/drc.json')); print('panel DRC errors', len(d['violations']), 'unconnected', len(d['unconnected_items']))"
rm -f $P/drc.json $P/~*.lck
