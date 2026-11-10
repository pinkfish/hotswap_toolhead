"""Stitch a net's copper between layers with as many vias as fit in a region.
    add_vias.py board.kicad_pcb NET x0,y0,x1,y1 [pitch] [dia/drill]
Candidates sit on a `pitch` grid (default 0.8 mm) inside the region (board mm from the top-left).
One is kept where NET's pours cover the whole via pad on at least two layers, where it stays off
every SMD pad (solder would wick down it) and 0.3 mm clear of other holes, and where DRC (errors
and warnings) finds nothing wrong with it. Rejected candidates are dropped and the board is rebuilt
from the original until DRC passes. MAX caps the number kept (the first in grid order).
Used to give the 100 W heater's 4.7 A enough vias: a 0.3 mm via carries about 1 A comfortably.
"""
import json
import math
import os
import shutil
import subprocess
import sys
import tempfile

import pcbnew

mm, tomm = pcbnew.FromMM, pcbnew.ToMM
O = 100.0
path, net = sys.argv[1], sys.argv[2]
x0, y0, x1, y1 = (float(v) for v in sys.argv[3].split(','))
pitch = float(sys.argv[4]) if len(sys.argv) > 4 else 0.8
dia, drill = (float(v) for v in (sys.argv[5] if len(sys.argv) > 5 else '0.6/0.3').split('/'))
MAX = int(os.environ.get('MAX', '0')) or None
KICAD_CLI = os.environ.get('KICAD_CLI', '/Applications/KiCad/KiCad.app/Contents/MacOS/kicad-cli')
IGNORE = ('silk', 'lib_footprint', 'text', 'courtyard')

orig = path[:-len('.kicad_pcb')] + '_orig.kicad_pcb'
shutil.copy(path, orig)
b = pcbnew.LoadBoard(orig)
pcbnew.ZONE_FILLER(b).Fill(b.Zones())
zones = [z for z in b.Zones() if z.GetNetname() == net and not z.GetIsRuleArea()]
holes = [(tomm(t.GetPosition().x) - O, tomm(t.GetPosition().y) - O, tomm(t.GetDrill()) / 2)
         for t in b.GetTracks() if t.Type() == pcbnew.PCB_VIA_T]
smd = []
for f in b.GetFootprints():
    for p in f.Pads():
        if p.GetDrillSize().x > 0:
            holes.append((tomm(p.GetPosition().x) - O, tomm(p.GetPosition().y) - O, tomm(p.GetDrillSize().x) / 2))
        else:
            smd.append(p)
cands = []
nx, ny = int(round((x1 - x0) / pitch)) + 1, int(round((y1 - y0) / pitch)) + 1
for i in range(nx):
    for j in range(ny):
        x, y = x0 + i * pitch, y0 + j * pitch
        p = pcbnew.VECTOR2I(mm(x + O), mm(y + O))
        layers = {l for z in zones for l in z.GetLayerSet().Seq() if z.HitTestFilledArea(l, p, -mm(dia / 2))}
        if len(layers) < 2:
            continue
        if any(math.hypot(x - hx, y - hy) < hr + drill / 2 + 0.3 for hx, hy, hr in holes):
            continue
        if any(s.HitTest(p, mm(dia / 2 + 0.05)) for s in smd):
            continue
        if any(math.hypot(x - cx, y - cy) < drill + 0.3 for cx, cy in cands):
            continue
        cands.append((x, y))
print('%s: %d candidates' % (net, len(cands)))


def build(pts):
    bb = pcbnew.LoadBoard(orig)
    ni = bb.FindNet(net)
    for x, y in pts:
        v = pcbnew.PCB_VIA(bb)
        v.SetPosition(pcbnew.VECTOR2I(mm(x + O), mm(y + O)))
        v.SetWidth(mm(dia))
        v.SetDrill(mm(drill))
        v.SetNet(ni)
        bb.Add(v)
    pcbnew.ZONE_FILLER(bb).Fill(bb.Zones())
    pcbnew.SaveBoard(path, bb)


while True:
    build(cands[:MAX])
    with tempfile.TemporaryDirectory() as t:
        out = os.path.join(t, 'drc.json')
        subprocess.run([KICAD_CLI, 'pcb', 'drc', '--format', 'json', '--severity-error', '--severity-warning',
                        '-o', out, path], capture_output=True)
        d = json.load(open(out))
    bad = set()
    for v in d['violations']:
        if v['type'].startswith(IGNORE):
            continue
        for it in v['items']:
            if it['description'].startswith('Via'):
                bad.add((round(it['pos']['x'] - O, 2), round(it['pos']['y'] - O, 2)))
    for u in d.get('unconnected_items', []):
        for it in u['items']:
            bad.add((round(it['pos']['x'] - O, 2), round(it['pos']['y'] - O, 2)))
    keep = [c for c in cands[:MAX] if (round(c[0], 2), round(c[1], 2)) not in bad]
    if len(keep) == len(cands[:MAX]):
        break
    cands = keep + cands[len(cands[:MAX]):] if MAX else keep
os.remove(orig)
print('%s: %d vias added: %s' % (net, len(cands[:MAX]), ' '.join('(%.2f,%.2f)' % c for c in cands[:MAX])))
