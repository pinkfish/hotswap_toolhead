"""Bring the routed MCU corner over from the donor board, turned to U6's new rotation.
    corner_import.py board.kicad_pcb donor.kicad_pcb
On the donor (the 27 x 36 board) the crystal, its load caps and U6's VDD / VREF+ decoupling sit in
a hand-laid strip along U6's pins 1-12 (corner_pre.py), with their copper. This puts U6 at U6_AT
(board mm, rotation), places the corner parts where the same move takes them, and copies the
corner's copper: the bottom-side tracks, and the GND / +3V3 plane vias, of the corner parts'
nets that lie within the corner's area (its parts and U6's pin row beside them), so runs that
went on elsewhere keep only their escapes. declash.py removes any of it that a top-side part
placed later lands on. Run it before place.py,
with the corner parts in the plan as (None, None, None, 'B', 1) so they stay put.
"""
import os
import sys

import pcbnew

O = 100.0
mm, tomm = pcbnew.FromMM, pcbnew.ToMM
CORNER = ['U6', 'Y1', 'C9', 'C11', 'C12', 'C13', 'C14', 'C15', 'FB1']
U6_AT = tuple(map(float, os.environ.get('U6_AT', '13.5,15.8,0').split(',')))   # board mm, rotation
TRIM = 0.3
PLANE_NETS = {'/GND', '/+3V3'}

b = pcbnew.LoadBoard(sys.argv[1])
d = pcbnew.LoadBoard(sys.argv[2])
du = d.FindFootprintByReference('U6')
c = du.GetPosition()
ang = pcbnew.EDA_ANGLE(U6_AT[2] - du.GetOrientationDegrees(), pcbnew.DEGREES_T)
shift = pcbnew.VECTOR2I(mm(O + U6_AT[0]) - c.x, mm(O + U6_AT[1]) - c.y)


def move(item):
    item.Rotate(c, ang)
    item.Move(shift)


# the corner's area on the donor: its parts' courtyards (not U6's), TRIM larger, stretched to
# U6's pin row beside it (on the donor the corner is below U6)
e = []
for ref in CORNER[1:]:
    f = d.FindFootprintByReference(ref)
    for ly in (pcbnew.F_CrtYd, pcbnew.B_CrtYd):
        if f.GetCourtyard(ly).OutlineCount():
            bb = f.GetCourtyard(ly).BBox()
            e.append((bb.GetLeft(), bb.GetTop(), bb.GetRight(), bb.GetBottom()))
u = du.GetCourtyard(pcbnew.B_CrtYd).BBox()
box = (min(a[0] for a in e) - mm(TRIM), min(min(a[1] for a in e) - mm(TRIM), u.GetBottom() - mm(1.0)),
       max(a[2] for a in e) + mm(TRIM), max(a[3] for a in e) + mm(TRIM))
nets = {p.GetNetname() for r in CORNER[1:] for p in d.FindFootprintByReference(r).Pads()}


def within(p):
    return box[0] <= p.x <= box[2] and box[1] <= p.y <= box[3]


# the corner's own nets, inside its area: runs that go on elsewhere keep only their escapes
copied = 0
for t in d.GetTracks():
    ends = [t.GetPosition()] if t.GetClass() == 'PCB_VIA' else [t.GetStart(), t.GetEnd()]
    if t.GetNetname() not in nets or not all(within(p) for p in ends):
        continue
    # bottom-side copper only (the top side holds other parts here); a via only on a plane net,
    # where it lands on the plane, not as the start of a top-side run
    via = t.GetClass() == 'PCB_VIA'
    if (via and t.GetNetname() not in PLANE_NETS) or (not via and t.GetLayer() != pcbnew.B_Cu):
        continue
    n = t.Duplicate()
    b.Add(n)
    n.SetNet(b.FindNet(t.GetNetname()))
    move(n)
    n.SetLocked(True)
    copied += 1
for ref in CORNER:
    src, dst = d.FindFootprintByReference(ref), b.FindFootprintByReference(ref)
    if dst.IsFlipped() != src.IsFlipped():
        dst.Flip(dst.GetPosition(), pcbnew.FLIP_DIRECTION_TOP_BOTTOM)
    dst.SetPosition(src.GetPosition())
    dst.SetOrientation(src.GetOrientation())
    move(dst)
pcbnew.SaveBoard(sys.argv[1], b)
print('corner placed:', ' '.join('%s (%.2f, %.2f, %d)' % (r, tomm(f.GetPosition().x) - O, tomm(f.GetPosition().y) - O,
                                                          f.GetOrientationDegrees())
                                 for r in CORNER for f in [b.FindFootprintByReference(r)]), '; copper items', copied)
