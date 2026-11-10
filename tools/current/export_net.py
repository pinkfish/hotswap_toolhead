"""export_net.py board.kicad_pcb net out.json : one net's copper per layer (polygons with holes),
its vias and plated holes, and its pads (ref, number, layers, polygon), for current_solve.py."""
import json, sys
import pcbnew

b = pcbnew.LoadBoard(sys.argv[1])
net = sys.argv[2]
mm = pcbnew.ToMM
CU = [l for l in b.GetEnabledLayers().CuStack()]
names = {l: b.GetLayerName(l) for l in CU}


def polys(ps):
    out = []
    for i in range(ps.OutlineCount()):
        o = ps.Outline(i)
        holes = [[(mm(p.x), mm(p.y)) for p in ps.Hole(i, j).CPoints()] for j in range(ps.HoleCount(i))]
        out.append([[(mm(p.x), mm(p.y)) for p in o.CPoints()], holes])
    return out


layers = {names[l]: [] for l in CU}
for z in b.Zones():
    if z.GetNetname() != net or z.GetIsRuleArea():
        continue
    for l in z.GetLayerSet().Seq():
        if l in names:
            layers[names[l]] += polys(z.GetFilledPolysList(l))
vias = []
for t in b.GetTracks():
    if t.GetNetname() != net:
        continue
    if t.Type() == pcbnew.PCB_VIA_T:
        vias.append(dict(x=mm(t.GetPosition().x), y=mm(t.GetPosition().y), drill=mm(t.GetDrill()),
                         dia=mm(t.GetWidth(pcbnew.F_Cu))))
        continue
    ps = pcbnew.SHAPE_POLY_SET()
    t.TransformShapeToPolygon(ps, t.GetLayer(), 0, pcbnew.FromMM(0.01), pcbnew.ERROR_INSIDE)
    layers[names[t.GetLayer()]] += polys(ps)
pads = []
for f in b.GetFootprints():
    for p in f.Pads():
        if p.GetNetname() != net:
            continue
        pl = [names[l] for l in p.GetLayerSet().Seq() if l in names]
        shapes = {}
        for l in p.GetLayerSet().Seq():
            if l not in names:
                continue
            ps = pcbnew.SHAPE_POLY_SET()
            p.TransformShapeToPolygon(ps, l, 0, pcbnew.FromMM(0.01), pcbnew.ERROR_INSIDE)
            shapes[names[l]] = polys(ps)
            layers[names[l]] += shapes[names[l]]
        th = p.GetAttribute() == pcbnew.PAD_ATTRIB_PTH
        pads.append(dict(ref=f.GetReference(), num=p.GetNumber(), layers=pl, shapes=shapes,
                         x=mm(p.GetPosition().x), y=mm(p.GetPosition().y),
                         drill=mm(min(p.GetDrillSize().x, p.GetDrillSize().y)) if th else 0))
o = b.GetBoardEdgesBoundingBox()
json.dump(dict(net=net, layers=layers, vias=vias, pads=pads, order=[names[l] for l in CU],
               bbox=[mm(o.GetLeft()), mm(o.GetTop()), mm(o.GetRight()), mm(o.GetBottom())]),
          open(sys.argv[3], 'w'))
print(net, {k: len(v) for k, v in layers.items()}, len(vias), 'vias', len(pads), 'pads')
