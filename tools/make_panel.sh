#!/bin/zsh
# make_panel.sh [9|6|4] - build a JLCPCB panel holding both boards of the stack, N of each
# (default 9), in columns of logic/power pairs (tools/panel_stack.py), from
# hardware/toolhead_logic.kicad_pcb and hardware/toolhead_power.kicad_pcb:
#   9: 3 columns of 3 pairs, 99.3 x 198.6 mm   -> hardware/panel/,  gerber/panel/,  toolhead_panel
#   6: 3 columns of 2 pairs, 99.3 x 136.4 mm   -> hardware/panel6/, gerber/panel6/, toolhead_panel6
#   4: 4 columns of 1 pair,  128.4 x 74.2 mm   -> hardware/panel4/, gerber/panel4/, toolhead_panel4
# Every size is inside JLCPCB's standard-PCBA panel range (70 x 70 to 250 x 250 mm). Four as 2 x 2
# would be 70.2 mm wide, too close to the minimum, so it is one row of four pairs.
#   hardware/panelN/toolhead_panelN.kicad_pcb  KiKit panel (frame rails, tooling holes, fiducials, mouse bites)
#   gerber/panelN/                             Gerbers, drill, zip, JLC BOM + CPL (refs R1_0, R1_2 ... on
#                                              the logic boards, C2_1, C2_3 ... on the power boards)
# Needs KiCad 9 and KiKit (pip install kikit into KiCad's Python).
set -e
cd "${0:A:h}/.."
APP=/Applications/KiCad/KiCad.app/Contents
PY=$APP/Frameworks/Python.framework/Versions/Current/bin/python3
K=$APP/MacOS/kicad-cli
case ${1:-9} in
  9) UNITS=3 COLS=3 SUF= ;;
  6) UNITS=2 COLS=3 SUF=6 ;;
  4) UNITS=1 COLS=4 SUF=4 ;;
  *) echo "usage: make_panel.sh [9|6|4]"; exit 1 ;;
esac
N=toolhead_panel$SUF
P=hardware/panel$SUF
G=gerber/panel$SUF
mkdir -p $P $G
# tools/panel.json with this size's columns and pairs per column
$PY - $P $UNITS $COLS <<'PY'
import json, sys
c = json.load(open('tools/panel.json'))
p, units, cols = sys.argv[1:4]
c['layout']['arg'] = '%s/src_power.kicad_pcb;%s;%s' % (p, units, cols)
c['text']['text'] = c['text']['text'].replace('3x3', '%sx%s' % (cols, units))
json.dump(c, open(p + '/panel.json', 'w'), indent=1)
PY
cp hardware/toolhead_logic.kicad_pro $P/src.kicad_pro
cp hardware/toolhead_logic.kicad_dru $P/src.kicad_dru
cp hardware/toolhead_power.kicad_pro $P/src_power.kicad_pro
cp hardware/toolhead_power.kicad_dru $P/src_power.kicad_dru
$PY tools/panel_tabs.py hardware/toolhead_logic.kicad_pcb $P/src.kicad_pcb 2>&1 | grep -v -e Debug -e assert -e leak
$PY tools/panel_tabs.py hardware/toolhead_power.kicad_pcb $P/src_power.kicad_pcb 2>&1 | grep -v -e Debug -e assert -e leak
$PY -m kikit.ui panelize -p $P/panel.json $P/src.kicad_pcb $P/$N.kicad_pcb 2>&1 | grep -v -e 'Debug: Adding' -e leak || true
rm -f $P/src.kicad_pcb $P/src.kicad_pro $P/src.kicad_dru $P/src_power.kicad_* $P/panel.json
# KiKit's fiducials and tooling holes (KiKit_FID_*, KiKit_TO_*) and the bare solder-jumper pads
# (JP1, JP3) have no part to place: keep them out of every BOM and position file, including
# the Fabrication Toolkit's, which JLCPCB rejects when the CPL names parts the BOM lacks
$PY - $P/$N.kicad_pcb 2>&1 <<'PY' | grep -v 'Debug\|assert\|leak' || true
import re, sys, pcbnew
f = sys.argv[1]
b = pcbnew.LoadBoard(f); n = 0
for fp in b.GetFootprints():
    if re.match(r'KiKit_(FID|TO)_|JP[13]_\d+$', fp.GetReference()):
        fp.SetExcludedFromBOM(True); fp.SetExcludedFromPosFiles(True); n += 1
pcbnew.SaveBoard(f, b)
print(n, 'panel footprints excluded from BOM and position files')
PY
cp hardware/toolhead_logic.kicad_dru $P/$N.kicad_dru
# H1's and H2's rings are exactly 0.5 mm from the board corners; KiKit's rebuilt outline puts
# those corners a hair closer, so the panel allows 0.49 mm there
cat >> $P/$N.kicad_dru <<'DRU'

(rule "H1/H2 rings at the panel's board corners"
  (condition "A.memberOfFootprint('H1_*') || A.memberOfFootprint('H2_*')")
  (constraint edge_clearance (min 0.49mm)))
DRU
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
print(len(pos), 'placements on', len(boards), 'boards;', len(base), 'parts per logic + power pair')
PY
rm -f $P/pos.csv
# CPL fitted to JLCPCB's own footprints (see tools/jlc_cpl.py)
$PY tools/jlc_cpl.py $P/$N.kicad_pcb $G/$N-cpl-jlcpcb.csv 2>&1 | grep -v -e Debug -e assert || true
(cd $G && zip -q $N-gerbers.zip *.g* *.drl)
$K pcb drc --severity-error --format json -o $P/drc.json $P/$N.kicad_pcb >/dev/null
$PY -c "import json; d=json.load(open('$P/drc.json')); print('panel DRC errors', len(d['violations']), 'unconnected', len(d['unconnected_items']))"
rm -f $P/drc.json $P/~*.lck
