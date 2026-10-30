"""jlc_cpl.py board.kicad_pcb out.csv - write a JLCPCB CPL for every BOM part on a board or panel.
Run with KiCad's Python. Each part's JLCPCB footprint (tools/jlc_footprints.json, from
jlc_fetch.py) is fitted onto the part's pads by pad number, so 'Mid X/Y' is JLCPCB's
footprint origin and 'Rotation' its rotation: as seen from above on the top side and, as
JLCPCB expects, from below on the bottom side. No per-package rotation table is needed.
Parts with no cached footprint, or whose pads don't fit, fall back to the KiCad anchor and
orientation (180 - orientation on the bottom) and are listed as warnings.
"""
import csv
import json
import math
import os
import re
import sys

import pcbnew

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
TOL = 0.35   # mm: worst pad misfit accepted (pad shapes differ a little between libraries)

b = pcbnew.LoadBoard(sys.argv[1])
rows = list(csv.DictReader(open(os.path.join(ROOT, 'hardware', 'bom_jlcpcb.csv'))))
base = {d.strip(): r['LCSC Part #'] for r in rows for d in r['Designator'].split(',')}
db = json.load(open(os.path.join(ROOT, 'tools', 'jlc_footprints.json')))


def fit(brd, jlc):
    """Best (worst-pad error, rotation, centre) of jlc pads rotated onto brd pads."""
    best = None
    for rot in (0, 90, 180, 270):
        c, s = math.cos(math.radians(rot)), math.sin(math.radians(rot))
        r = {n: (x * c - y * s, x * s + y * c) for n, (x, y) in jlc.items()}
        cx = sum(brd[n][0] - r[n][0] for n in r) / len(r)
        cy = sum(brd[n][1] - r[n][1] for n in r) / len(r)
        err = {n: math.hypot(brd[n][0] - r[n][0] - cx, brd[n][1] - r[n][1] - cy) for n in r}
        if best is None or max(err.values()) < best[0] - 1e-6:
            best = (max(err.values()), rot, (cx, cy), err)
    return best


out, warn = [], []
for fp in b.GetFootprints():
    ref = fp.GetReference()
    code = base.get(re.sub(r'_\d+$', '', ref))
    if code is None or fp.IsExcludedFromPosFiles() or fp.IsDNP():
        continue
    bottom = fp.IsFlipped()
    pads = {}
    for p in fp.Pads():
        if p.GetNumber():
            q = p.GetPosition()
            pads.setdefault(p.GetNumber(), []).append((pcbnew.ToMM(q.x), -pcbnew.ToMM(q.y)))
    # several pads with one number (shield tabs, split exposed pads): use their centroid
    pads = {n: (sum(x for x, _ in v) / len(v), sum(y for _, y in v) / len(v)) for n, v in pads.items()}
    res = None
    if code in db:
        # seen from above, a bottom part is JLCPCB's footprint mirrored left-right
        jlc = {n: ((-x if bottom else x), y) for n, (x, y) in db[code]['pads'].items() if n in pads}
        # pads that share a number but not a place (a merged drain tab) are dropped worst-first
        while len(jlc) >= 2:
            res = fit(pads, jlc)
            if res[0] <= TOL:
                break
            del jlc[max(res[3], key=res[3].get)]
            res = None
    if res:
        _, rot, (x, y), _ = res
        rot = -rot if bottom else rot
    else:
        a = fp.GetPosition()
        x, y = pcbnew.ToMM(a.x), -pcbnew.ToMM(a.y)
        o = fp.GetOrientationDegrees()
        rot = 180 - o if bottom else o
        warn.append(ref)
    out.append([ref, f'{x:.3f}mm', f'{y:.3f}mm', 'Bottom' if bottom else 'Top', f'{rot % 360:g}'])

out.sort(key=lambda r: [int(t) if t.isdigit() else t for t in re.split(r'(\d+)', r[0])])
with open(sys.argv[2], 'w', newline='') as fh:
    w = csv.writer(fh)
    w.writerow(['Designator', 'Mid X', 'Mid Y', 'Layer', 'Rotation'])
    w.writerows(out)
print(len(out), 'placements', sum(r[3] == 'Bottom' for r in out), 'bottom;',
      'no JLCPCB footprint fit (KiCad anchor used): ' + ' '.join(sorted({re.sub(r'_\d+$', '', r) for r in warn}))
      if warn else 'all fitted to JLCPCB footprints')
