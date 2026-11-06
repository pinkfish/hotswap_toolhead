"""panel_tabs.py in.kicad_pcb out.kicad_pcb - add KiKit tab annotations on the side edges where
both neighbours are clear.
J1/J5 and J2 overhang the top and bottom edges, so the boards are held by side tabs only, two
per side. In a panel row every board is the same one, so a tab at height y on a board's right
edge meets the next board's left edge at the same y: a tab goes only where the 0.6 mm strip
along both side edges has no copper (pads, tracks, vias; a 0.5 mm bite hole centred on the edge
reaches 0.25 mm in) and no part overhangs either side edge (its courtyard crosses it). The two
tabs go as far apart as the clear windows allow, at the top of the first and the bottom of the
last (both in one window if it is long enough), each 1.4-1.8 mm wide with 0.3 mm to spare.
"""
import os
import sys

import kikit
import pcbnew

mm = pcbnew.FromMM
O = 100.0
STRIP, SPARE, WMIN, WMAX = 0.6, 0.3, 1.4, 1.8
CORNER = 1.2      # KiKit rounds the board corners: no tab within this of the top or bottom edge
LIB = os.path.join(os.path.dirname(kikit.__file__), 'resources', 'kikit.pretty')
b = pcbnew.LoadBoard(sys.argv[1])
edges = [d for d in b.GetDrawings() if d.GetLayer() == pcbnew.Edge_Cuts]   # outline geometry, not its line width
W = max(max(d.GetStart().x, d.GetEnd().x) for d in edges) / 1e6 - O
H = max(max(d.GetStart().y, d.GetEnd().y) for d in edges) / 1e6 - O

# y ranges (board mm) blocked in either side strip
blocked = []


def block(bb, strip=STRIP):
    x0, y0, x1, y1 = (pcbnew.ToMM(v) - O for v in (bb.GetLeft(), bb.GetTop(), bb.GetRight(), bb.GetBottom()))
    if x0 < strip or x1 > W - strip:
        blocked.append((y0, y1))


for f in b.GetFootprints():
    for p in f.Pads():
        block(p.GetBoundingBox())
    for layer in (pcbnew.F_Cu, pcbnew.B_Cu):
        c = f.GetCourtyard(layer)
        if c.OutlineCount():
            block(c.BBox(), 0)
for t in b.GetTracks():
    block(t.GetBoundingBox())
blocked.sort()
free, y = [], CORNER
for y0, y1 in blocked + [(H - CORNER, H)]:
    if y0 - y >= WMIN + 2 * SPARE:
        free.append((y, y0))
    y = max(y, y1)
assert free, 'no clear window on the side edges'
(a0, a1), (c0, c1) = free[0], free[-1]
wa, wc = min(WMAX, a1 - a0 - 2 * SPARE), min(WMAX, c1 - c0 - 2 * SPARE)
ya, yc = a0 + SPARE + wa / 2, c1 - SPARE - wc / 2     # top of the first window, bottom of the last
assert yc - ya >= (wa + wc) / 2 + 2 * SPARE, 'no room for two tabs on the side edges: %s' % free
TABS = []
for i, (ym, w) in enumerate(((ya, wa), (yc, wc))):
    TABS += [('KT%d' % (2 * i + 1), -0.5, ym, 0, w), ('KT%d' % (2 * i + 2), W + 0.5, ym, 180, w)]
print('board %g x %g mm; clear side windows %s' % (W, H, [(round(p, 1), round(q, 1)) for p, q in free]))
for ref, x, y, rot, w in TABS:
    # origin 0.5 mm outside the edge (KiKit grows the tab from there), orientation into the board
    f = pcbnew.FootprintLoad(LIB, 'Tab')
    f.SetFPID(pcbnew.LIB_ID('kikit', 'Tab'))
    f.SetReference(ref)
    for t in f.GraphicalItems():
        if isinstance(t, pcbnew.PCB_TEXT) and t.GetText().startswith('KIKIT:'):
            t.SetText('KIKIT: width: %gmm' % round(w, 2))
    f.SetPosition(pcbnew.VECTOR2I(mm(O + x), mm(O + y)))
    f.SetOrientationDegrees(rot)
    b.Add(f)
    print('%s at y %.2f, %.2f mm wide' % (ref, y, w))
pcbnew.SaveBoard(sys.argv[2], b)
