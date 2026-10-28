"""4-layer finish: import a Freerouting session, add a HEAT_N pour on the layer
Q2 sits on and GND pours on F/B (In1 = GND plane, In2 = +24V plane), stitch
with vias, fill, save.
    finish3.py board.kicad_pcb session.ses
"""
import pcbnew, sys

src, ses = sys.argv[1:3]
OX, OY = 100.0, 100.0
b = pcbnew.LoadBoard(src)
assert pcbnew.ImportSpecctraSES(b, ses), 'SES import failed'
mm = pcbnew.FromMM


def zone(net, layer, pts, prio, clearance=0.3):
    z = pcbnew.ZONE(b)
    z.SetLayer(layer)
    z.SetNet(b.FindNet(net))
    z.SetAssignedPriority(prio)
    z.SetLocalClearance(mm(clearance))
    z.SetMinThickness(mm(0.25))
    z.SetPadConnection(pcbnew.ZONE_CONNECTION_THERMAL)
    z.SetThermalReliefGap(mm(0.3))
    z.SetThermalReliefSpokeWidth(mm(0.5))
    z.SetIslandRemovalMode(pcbnew.ISLAND_REMOVAL_MODE_ALWAYS)
    o = z.Outline()
    o.NewOutline()
    for x, y in pts:
        o.Append(mm(OX + x), mm(OY + y))
    b.Add(z)
    return z


def rect(x0, y0, x1, y1):
    return ((x0, y0), (x1, y0), (x1, y1), (x0, y1))


# heater drain: a top-layer HEAT_N pour around J2 pin 2 and Q2's drain tab,
# sized from where those pads ended up.  Solid connection so the tab sinks heat.
pads = [p for f in b.GetFootprints() for p in f.Pads() if p.GetNetname() == '/HEAT_N']
bb = pads[0].GetBoundingBox()
for p in pads[1:]:
    bb.Merge(p.GetBoundingBox())
m = mm(1.2)
x0, y0, x1, y1 = [pcbnew.ToMM(v) - o for v, o in ((bb.GetLeft() - m, OX), (bb.GetTop() - m, OY), (bb.GetRight() + m, OX), (bb.GetBottom() + m, OY))]
q2 = b.FindFootprintByReference('Q2')
z = zone('/HEAT_N', pcbnew.B_Cu if q2.IsFlipped() else pcbnew.F_Cu, rect(x0, y0, x1, y1), 2)
z.SetPadConnection(pcbnew.ZONE_CONNECTION_FULL)
print('HEAT_N pour %.1f x %.1f mm' % (x1 - x0, y1 - y0))

e = b.GetBoardEdgesBoundingBox()
W, H = pcbnew.ToMM(e.GetWidth()), pcbnew.ToMM(e.GetHeight())
POUR = [pcbnew.F_Cu, pcbnew.B_Cu]
if b.GetLayerType(pcbnew.In2_Cu) == pcbnew.LT_SIGNAL:
    POUR.append(pcbnew.In2_Cu)
for layer in POUR:
    zone('/GND', layer, rect(0, 0, W, H), 0)

filler = pcbnew.ZONE_FILLER(b)
filler.Fill(b.Zones())

# stitching vias wherever both layers are solid GND with room for a via
gnd = b.FindNet('/GND')
fills = {l: [z.GetFilledPolysList(l) for z in b.Zones() if z.GetNetname() == '/GND' and z.GetLayer() == l]
         for l in POUR}


def solid(layer, x, y, r):
    pts = [(x, y)] + [(x + dx, y + dy) for dx, dy in ((r, 0), (-r, 0), (0, r), (0, -r),
                                                       (r * .7, r * .7), (-r * .7, r * .7), (r * .7, -r * .7), (-r * .7, -r * .7))]
    return any(all(p.Contains(pcbnew.VECTOR2I(mm(px), mm(py))) for px, py in pts) for p in fills[layer])


added = 0
via_pos = [t.GetPosition() for t in b.GetTracks() if t.GetClass() == 'PCB_VIA']
step = 2.0
y = 1.0
while y < H - 0.5:
    x = 1.0
    while x < W - 0.5:
        px, py = OX + x, OY + y
        here = pcbnew.VECTOR2I(mm(px), mm(py))
        # solid copper can also be a pad with vias already in it (U6's exposed pad)
        if all(solid(l, px, py, 0.65) for l in POUR) and \
                all((v - here).EuclideanNorm() >= mm(0.9) for v in via_pos):
            v = pcbnew.PCB_VIA(b)
            v.SetPosition(pcbnew.VECTOR2I(mm(px), mm(py)))
            v.SetWidth(mm(0.6))
            v.SetDrill(mm(0.3))
            v.SetNet(gnd)
            b.Add(v)
            via_pos.append(v.GetPosition())
            added += 1
        x += step
    y += step

filler.Fill(b.Zones())
pcbnew.SaveBoard(src, b)
tracks = list(b.GetTracks())
print('tracks', sum(1 for t in tracks if t.GetClass() == 'PCB_TRACK'),
      'vias', sum(1 for t in tracks if t.GetClass() == 'PCB_VIA'), 'stitching vias', added)
