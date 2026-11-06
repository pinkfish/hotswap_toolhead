"""check_stack.py - check that the logic and power boards stack: same outline, mounting holes on
the same axes, and every pin of the power board's link header J4 under the matching contact of
the logic board's socket J3 with the net design.LINK gives it. Run with KiCad's Python.
    check_stack.py [logic.kicad_pcb power.kicad_pcb]
J3 is an SMD socket on the logic board's underside: its pads splay out from the contact rows,
so a contact sits on the pad's row line, 1.27 mm from the socket's centre line. Positions are
board coordinates seen from the top, which is how the two boards line up in the stack.
"""
import math
import os
import sys

import pcbnew

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
sys.path.insert(0, os.path.join(ROOT, 'tools'))
import design  # noqa: E402

files = sys.argv[1:3] or [os.path.join(ROOT, 'hardware', design.BOARDS[b][0] + '.kicad_pcb') for b in ('logic', 'power')]
logic, power = (pcbnew.LoadBoard(f) for f in files)
mm = pcbnew.ToMM
TOL = 0.02
bad = []


def xy(v):
    return (mm(v.x), mm(v.y))


def outline(b):
    e = b.GetBoardEdgesBoundingBox()
    return [round(mm(v), 2) for v in (e.GetLeft(), e.GetTop(), e.GetRight(), e.GetBottom())]


if outline(logic) != outline(power):
    bad.append('outlines differ: %s / %s' % (outline(logic), outline(power)))
for ref in ('H1', 'H2'):
    a, c = (b.FindFootprintByReference(ref) for b in (logic, power))
    if math.dist(xy(a.GetPosition()), xy(c.GetPosition())) > TOL:
        bad.append('%s: %s / %s' % (ref, xy(a.GetPosition()), xy(c.GetPosition())))

j3, j4 = logic.FindFootprintByReference('J3'), power.FindFootprintByReference('J4')
pads3 = {p.GetNumber(): p for p in j3.Pads()}
c = xy(j3.GetPosition())
p1, p3 = xy(pads3['1'].GetPosition()), xy(pads3['3'].GetPosition())
u = ((p3[0] - p1[0]) / 2.54, (p3[1] - p1[1]) / 2.54)          # along the rows
contacts = {}
for n, p in pads3.items():
    d = (xy(p.GetPosition())[0] - c[0], xy(p.GetPosition())[1] - c[1])
    along = d[0] * u[0] + d[1] * u[1]
    perp = (d[0] - along * u[0], d[1] - along * u[1])
    k = 1.27 / math.hypot(*perp)
    contacts[n] = (c[0] + along * u[0] + perp[0] * k, c[1] + along * u[1] + perp[1] * k)
for p in j4.Pads():
    n = p.GetNumber()
    want = tuple('/' + x for x in design.LINK[int(n)])
    got = (pads3[n].GetNetname(), p.GetNetname())
    off = math.dist(contacts[n], xy(p.GetPosition()))
    if off > TOL:
        bad.append('pin %s: J3 contact %s, J4 pin %s (%.2f mm apart)' % (
            n, tuple(round(v - 100, 2) for v in contacts[n]), tuple(round(v - 100, 2) for v in xy(p.GetPosition())), off))
    if got != want:
        bad.append('pin %s nets %s, design.LINK says %s' % (n, got, want))
print('outline', [round(v - 100, 2) for v in outline(logic)], 'mm; holes and link pins checked')
print('\n'.join(bad) if bad else 'stack OK: outline, H1/H2 and all 12 link pins line up')
sys.exit(1 if bad else 0)
