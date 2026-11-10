#!/bin/zsh
# make_panel.sh [9|6|4] - build a JLCPCB panel of N USB boards (default 9) from
# hardware/toolhead_usb.kicad_pcb, in a KiKit grid:
#   9: 3 columns x 3 rows   -> hardware/panel/,  gerber/panel/,  toolhead_panel
#   6: 3 columns x 2 rows   -> hardware/panel6/, gerber/panel6/, toolhead_panel6
#   4: 2 columns x 2 rows   -> hardware/panel4/, gerber/panel4/, toolhead_panel4
# JLCPCB assembles panels from 70 x 70 to 250 x 250 mm; where the boards and the 5 mm frame come
# to less than 72 mm on a side, the gap between the boards and the frame on that side is widened.
#   hardware/panelN/toolhead_panelN.kicad_pcb  KiKit panel (frame rails, tooling holes, fiducials, mouse bites)
#   gerber/panelN/                             Gerbers, drill, zip, JLC BOM + CPL (refs R1_0, R1_1 ...)
# Needs KiCad 9 and KiKit (pip install kikit into KiCad's Python).
set -e
cd "${0:A:h}/.."
APP=/Applications/KiCad/KiCad.app/Contents
PY=$APP/Frameworks/Python.framework/Versions/Current/bin/python3
K=$APP/MacOS/kicad-cli
case ${1:-9} in
  9) ROWS=3 COLS=3 SUF= ;;
  6) ROWS=2 COLS=3 SUF=6 ;;
  4) ROWS=2 COLS=2 SUF=4 ;;
  *) echo "usage: make_panel.sh [9|6|4]"; exit 1 ;;
esac
N=toolhead_panel$SUF
P=hardware/panel$SUF
G=gerber/panel$SUF
mkdir -p $P $G
cp hardware/toolhead_usb.kicad_pro $P/src.kicad_pro
cp hardware/toolhead_usb.kicad_dru $P/src.kicad_dru
$PY tools/panel_tabs.py hardware/toolhead_usb.kicad_pcb $P/src.kicad_pcb 2>&1 | grep -v -e Debug -e assert -e leak
# tools/panel.json with this size's grid, and the frame gaps widened to reach 72 mm a side
$PY - $P $ROWS $COLS 2>&1 <<'PY' | grep -v 'Debug\|assert\|leak'
import json, sys, pcbnew
c = json.load(open('tools/panel.json'))
p, rows, cols = sys.argv[1], int(sys.argv[2]), int(sys.argv[3])
e = pcbnew.LoadBoard(p + '/src.kicad_pcb').GetBoardEdgesBoundingBox()
bw, bh = pcbnew.ToMM(e.GetWidth()), pcbnew.ToMM(e.GetHeight())
L, F = c['layout'], c['framing']
mm = lambda v: float(v.rstrip('m'))
L['rows'], L['cols'] = rows, cols
fw = mm(F['width'])
for axis, n, size, gap in (('hspace', cols, bw, mm(L['hspace'])), ('vspace', rows, bh, mm(L['vspace']))):
    inner = n * size + (n - 1) * gap
    F[axis] = '%.2fmm' % max(mm(F[axis]), (72 - inner) / 2 - fw)
    print('%s: %.1f mm' % ('width' if axis == 'hspace' else 'height', inner + 2 * (mm(F[axis]) + fw)))
c['text']['text'] = c['text']['text'].replace('3x3', '%sx%s' % (cols, rows))
json.dump(c, open(p + '/panel.json', 'w'), indent=1)
PY
$PY -m kikit.ui panelize -p $P/panel.json $P/src.kicad_pcb $P/$N.kicad_pcb 2>&1 | grep -v -e 'Debug: Adding' -e leak || true
rm -f $P/src.kicad_pcb $P/src.kicad_pro $P/src.kicad_dru $P/panel.json
# KiKit's fiducials and tooling holes (KiKit_FID_*, KiKit_TO_*) and the bare solder-jumper pads
# (JP2, JP3) have no part to place: keep them out of every BOM and position file, including
# the Fabrication Toolkit's, which JLCPCB rejects when the CPL names parts the BOM lacks
$PY - $P/$N.kicad_pcb 2>&1 <<'PY' | grep -v 'Debug\|assert\|leak' || true
import re, sys, pcbnew
f = sys.argv[1]
b = pcbnew.LoadBoard(f); n = 0
for fp in b.GetFootprints():
    if re.match(r'KiKit_(FID|TO)_|JP[23]_\d+$', fp.GetReference()):
        fp.SetExcludedFromBOM(True); fp.SetExcludedFromPosFiles(True); n += 1
pcbnew.SaveBoard(f, b)
print(n, 'panel footprints excluded from BOM and position files')
PY
cp hardware/toolhead_usb.kicad_dru $P/$N.kicad_dru
rm -rf $G && mkdir -p $G
$K pcb export gerbers -o $G/ --layers F.Cu,In1.Cu,In2.Cu,B.Cu,F.Paste,B.Paste,F.Silkscreen,B.Silkscreen,F.Mask,B.Mask,Edge.Cuts --subtract-soldermask $P/$N.kicad_pcb >/dev/null
$K pcb export drill -o $G/ --format excellon --excellon-separate-th --drill-origin absolute --excellon-units mm $P/$N.kicad_pcb >/dev/null
$K pcb export pos -o $P/pos.csv --format csv --units mm --side both --exclude-dnp $P/$N.kicad_pcb >/dev/null
$PY - $G/ $P/pos.csv $N <<'PY'
import csv, re, sys
G, POS, N = sys.argv[1:4]
rows = list(csv.DictReader(open('hardware/bom_jlcpcb.csv')))
base = {d.strip() for r in rows for d in r['Designator'].split(',')}
pos = [r for r in csv.DictReader(open(POS)) if re.sub(r'_\d+$', '', r['Ref']) in base]
n = {}
for r in pos:
    n.setdefault(re.sub(r'_\d+$', '', r['Ref']), []).append(r['Ref'])
with open(G + N + '-bom-jlcpcb.csv', 'w', newline='') as fh:
    w = csv.writer(fh); w.writerow(['Comment', 'Designator', 'Footprint', 'LCSC Part #'])
    for r in rows:
        refs = [x for d in r['Designator'].split(',') for x in sorted(n[d.strip()], key=lambda s: int(s.rsplit('_', 1)[1]))]
        w.writerow([r['Comment'], ','.join(refs), r['Footprint'], r['LCSC Part #']])
boards = {r['Ref'].rsplit('_', 1)[1] for r in pos}
print(len(pos), 'placements on', len(boards), 'boards;', len(base), 'parts per board')
PY
rm -f $P/pos.csv
# CPL fitted to JLCPCB's own footprints (see tools/jlc_cpl.py)
$PY tools/jlc_cpl.py $P/$N.kicad_pcb $G/$N-cpl-jlcpcb.csv 2>&1 | grep -v -e Debug -e assert || true
(cd $G && zip -q $N-gerbers.zip *.g* *.drl)
$K pcb drc --severity-error --format json -o $P/drc.json $P/$N.kicad_pcb >/dev/null
$PY -c "import json; d=json.load(open('$P/drc.json')); print('panel DRC errors', len(d['violations']), 'unconnected', len(d['unconnected_items']))"
rm -f $P/drc.json $P/~*.lck
