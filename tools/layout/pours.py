"""Helpers for the power-path pre-route scripts (stack_logic_pre.py, stack_power_pre.py):
copper pours built as unions of boxes, and via arrays dropped where they fit.
Boxes are [x0, y0, x1, y1] in KiCad mm (the board's 100 mm offset included), as box() gives
them from a pad.
"""
import pcbnew

mm, T = pcbnew.FromMM, pcbnew.ToMM
CLR = 0.3          # 24 V clearance (the board's rules)
VIA_D, VIA_DRILL = 0.6, 0.3


def pads(b, ref, num):
    return [p for p in b.FindFootprintByReference(ref).Pads() if p.GetNumber() == str(num)]


def box(p, grow=0.0):
    bb = p.GetBoundingBox()
    return [T(bb.GetLeft()) - grow, T(bb.GetTop()) - grow, T(bb.GetRight()) + grow, T(bb.GetBottom()) + grow]


def span(*bs):
    return [min(x[0] for x in bs), min(x[1] for x in bs), max(x[2] for x in bs), max(x[3] for x in bs)]


def poly(rects):
    s = pcbnew.SHAPE_POLY_SET()
    for x0, y0, x1, y1 in rects:
        r = pcbnew.SHAPE_POLY_SET()
        r.NewOutline()
        for x, y in ((x0, y0), (x1, y0), (x1, y1), (x0, y1)):
            r.Append(mm(x), mm(y))
        s.BooleanAdd(r)
    s.Simplify()
    return s


def pour(b, net, layer, rects, name=None):
    """A locked zone of net on layer over the union of rects, named '<net> pour' (planes_fanout.py,
    pour_clear.py and maze.py treat zones so named as the power path)."""
    s = poly(rects)
    assert s.OutlineCount() == 1, '%s pour on %s is in pieces' % (net, pcbnew.LayerName(layer))
    z = pcbnew.ZONE(b)
    z.SetLayer(layer)
    z.SetNet(b.FindNet(net))
    z.SetAssignedPriority(3)
    z.SetLocalClearance(mm(CLR))
    z.SetMinThickness(mm(0.25))
    z.SetPadConnection(pcbnew.ZONE_CONNECTION_FULL)
    z.SetIslandRemovalMode(pcbnew.ISLAND_REMOVAL_MODE_ALWAYS)
    z.SetZoneName(name or (net.strip('/') + (' pour' if layer == pcbnew.F_Cu else ' B pour')))
    o, ln = z.Outline(), s.Outline(0)
    o.NewOutline()
    for i in range(ln.PointCount()):
        o.Append(ln.CPoint(i).x, ln.CPoint(i).y)
    z.SetLocked(True)
    b.Add(z)
    return z


def vias(b, net, rect, pitch=1.0, most=99):
    """Through vias of net on a pitch grid inside rect, where each clears every other net's pad,
    via, pour and keep-out, and every SMD pad (no via in a pad), by CLR; returns how many it placed."""
    n = b.FindNet(net)
    others = [p for f in b.GetFootprints() for p in f.Pads()
              if p.GetNetname() != net or p.GetAttribute() == pcbnew.PAD_ATTRIB_SMD]
    have = [t.GetPosition() for t in b.GetTracks() if t.GetClass() == 'PCB_VIA']
    zones = [z for z in b.Zones() if (z.GetIsRuleArea() and z.GetDoNotAllowVias()) or
             (not z.GetIsRuleArea() and z.GetZoneName().endswith('pour') and z.GetNetname() != net)]
    placed = 0
    x0, y0, x1, y1 = rect
    y = y0
    while y <= y1 + 1e-6 and placed < most:
        x = x0
        while x <= x1 + 1e-6 and placed < most:
            c = pcbnew.VECTOR2I(mm(x), mm(y))
            r = mm(VIA_D / 2 + CLR)
            ok = all(not (p.IsOnLayer(L) and p.GetEffectiveShape(L).Collide(c, r))
                     for p in others for L in (pcbnew.F_Cu, pcbnew.B_Cu))
            ok = ok and all((h - c).EuclideanNorm() >= mm(VIA_D + CLR) for h in have)
            ok = ok and not any(z.Outline().Collide(c, r) for z in zones)
            if ok:
                v = pcbnew.PCB_VIA(b)
                v.SetPosition(c)
                v.SetWidth(mm(VIA_D))
                v.SetDrill(mm(VIA_DRILL))
                v.SetNet(n)
                v.SetLocked(True)
                b.Add(v)
                have.append(c)
                placed += 1
            x += pitch
        y += pitch
    return placed
