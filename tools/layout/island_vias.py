"""island_vias.py board.kicad_pcb - a GND via into each F/B GND pour island that has none.
An island boxed in by tracks (a decoupling cap's GND pad between two signal runs) is joined to
the In1 plane only through its pads otherwise, and DRC counts it as unconnected. The via goes at
the first spot on a 0.1 mm grid inside the island that clears other nets' copper on F/B, holes
and the board edge.
"""
import sys

import pcbnew

mm = pcbnew.FromMM
b = pcbnew.LoadBoard(sys.argv[1])
HV = {'/VIN_RAW', '/VIN_F', '/+24V', '/HEAT_N', '/FAN_N', '/FAN_P'}
D, DRILL, HOLE_CLR, EDGE_CLR = 0.6, 0.3, 0.25, 0.5
CU = (pcbnew.F_Cu, pcbnew.B_Cu)
filler = pcbnew.ZONE_FILLER(b)
filler.Fill(b.Zones())
gnd = b.FindNet('/GND')
e = b.GetBoardEdgesBoundingBox()


def fits(pos):
    if not (e.GetLeft() + mm(EDGE_CLR + D / 2) < pos.x < e.GetRight() - mm(EDGE_CLR + D / 2)
            and e.GetTop() + mm(EDGE_CLR + D / 2) < pos.y < e.GetBottom() - mm(EDGE_CLR + D / 2)):
        return False
    r = mm(D / 2)
    for p in b.GetPads():
        if p.GetDrillSize().x and (pos - p.GetPosition()).EuclideanNorm() < p.GetDrillSize().x / 2 + mm(DRILL / 2 + HOLE_CLR):
            return False
        if p.GetNetname() == '/GND':
            continue
        cl = mm(0.3 if p.GetNetname() in HV else 0.2)
        if any(p.IsOnLayer(l) and p.GetEffectiveShape(l).Collide(pos, r + cl) for l in CU):
            return False
    for t in b.GetTracks():
        if t.GetClass() == 'PCB_VIA':
            if (pos - t.GetPosition()).EuclideanNorm() < r + t.GetWidth(pcbnew.F_Cu) / 2 + mm(0.2 if t.GetNetname() == '/GND' else 0.3 if t.GetNetname() in HV else 0.2):
                return False
        elif t.GetNetname() != '/GND' and t.GetLayer() in CU:
            cl = mm(0.3 if t.GetNetname() in HV else 0.2)
            if pcbnew.SEG(t.GetStart(), t.GetEnd()).Distance(pos) < r + t.GetWidth() / 2 + cl:
                return False
    return True


added = []
for layer in CU:
    anchors = [t.GetPosition() for t in b.GetTracks() if t.GetClass() == 'PCB_VIA' and t.GetNetname() == '/GND'] + \
              [p.GetPosition() for p in b.GetPads() if p.GetNetname() == '/GND' and p.GetAttribute() == pcbnew.PAD_ATTRIB_PTH]
    for z in b.Zones():
        if z.GetNetname() != '/GND' or not z.IsOnLayer(layer):
            continue
        polys = z.GetFilledPolysList(layer)
        for i in range(polys.OutlineCount()):
            if any(polys.Contains(a, i) for a in anchors):
                continue
            bb = polys.Outline(i).BBox()
            spot = None
            y = bb.GetTop()
            while spot is None and y < bb.GetBottom():
                x = bb.GetLeft()
                while x < bb.GetRight():
                    pos = pcbnew.VECTOR2I(x, y)
                    if polys.Contains(pos, i) and fits(pos):
                        spot = pos
                        break
                    x += mm(0.1)
                y += mm(0.1)
            if spot is None:
                print('no room for a via in the', b.GetLayerName(layer), 'island at',
                      [round(pcbnew.ToMM(v) - 100, 2) for v in (bb.GetLeft(), bb.GetTop(), bb.GetRight(), bb.GetBottom())])
                continue
            v = pcbnew.PCB_VIA(b)
            v.SetPosition(spot)
            v.SetWidth(mm(D))
            v.SetDrill(mm(DRILL))
            v.SetNet(gnd)
            b.Add(v)
            anchors.append(spot)
            added.append((b.GetLayerName(layer), round(pcbnew.ToMM(spot.x) - 100, 2), round(pcbnew.ToMM(spot.y) - 100, 2)))
filler.Fill(b.Zones())
pcbnew.SaveBoard(sys.argv[1], b)
print('island vias', added)
