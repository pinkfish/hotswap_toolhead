"""Add the inner planes (In1 = GND, In2 = +24V, whole board) and fan out every
SMD pad on those nets to a via, so the autorouter never has to route them.
V24_TOP (the logic board, where +24V only crosses the top edge): +24V is a top-layer pour with
this outline (board mm "x,y;x,y;...") instead, its bottom-side pads get vias inside it, and In2
is left to the router.
    planes_fanout.py board.kicad_pcb
Fanout tracks and vias are locked so Freerouting keeps them.
"""
import math
import sys

import pcbnew

mm, tomm = pcbnew.FromMM, pcbnew.ToMM
b = pcbnew.LoadBoard(sys.argv[1])
e = b.GetBoardEdgesBoundingBox()
import os
PLANES = {'/GND': pcbnew.In1_Cu}
# IN2_SPLIT: In2 is a +24V strip (this outline, board mm "x,y;x,y;...") with +3V3 on the rest;
# a fanout via for either net must land inside its own zone
SPLIT = [tuple(map(float, q.split(','))) for q in os.environ.get('IN2_SPLIT', '').split(';') if q]
OUTLINE = {}
TOP = [tuple(map(float, q.split(','))) for q in os.environ.get('V24_TOP', '').split(';') if q]
if SPLIT:
    PLANES['/+24V'] = PLANES['/+3V3'] = pcbnew.In2_Cu
    OUTLINE['/+24V'] = SPLIT
elif TOP:
    PLANES['/+24V'] = pcbnew.F_Cu
    OUTLINE['/+24V'] = TOP
    b.SetLayerType(pcbnew.In2_Cu, pcbnew.LT_SIGNAL)   # In2 routed
elif os.environ.get('V24_PLANE'):
    PLANES['/+24V'] = pcbnew.In2_Cu
else:
    b.SetLayerType(pcbnew.In2_Cu, pcbnew.LT_SIGNAL)   # In2 routed
# per-net fanout track width and via (diameter, drill); FAN_SMALL is tried where the +24V size
# finds no room (small parts: a 0.6 mm via still carries well over the 0.5 A fan or buck input)
FAN = {'/GND': (0.3, 0.6, 0.3), '/+24V': (0.8, 0.8, 0.4), '/+3V3': (0.3, 0.6, 0.3)}
FAN_SMALL = (0.8, 0.6, 0.3)   # the stub keeps the high-current class width
VIA_D, VIA_DRILL, CLR, TRACK = 0.6, 0.3, 0.2, 0.3
EDGE = 0.55 + VIA_D / 2   # edge bbox includes half the 0.1 mm outline
HV = {'/VIN_RAW', '/VIN_F', '/+24V', '/HEAT_N', '/FAN_N', '/FAN_P'}
HV_CLR = 0.32

ONLY = set(filter(None, os.environ.get('ONLY', '').split(',')))
for net, layer in ([] if ONLY else PLANES.items()):
    z = pcbnew.ZONE(b)
    z.SetLayer(layer)
    z.SetNet(b.FindNet(net))
    z.SetLocalClearance(mm(0.3))
    z.SetMinThickness(mm(0.25))
    z.SetPadConnection(pcbnew.ZONE_CONNECTION_THERMAL)
    z.SetThermalReliefGap(mm(0.3))
    z.SetThermalReliefSpokeWidth(mm(0.4))
    z.SetIslandRemovalMode(pcbnew.ISLAND_REMOVAL_MODE_ALWAYS)
    o = z.Outline()
    o.NewOutline()
    if net in OUTLINE:
        z.SetAssignedPriority(1)   # wins over the +3V3 zone (IN2_SPLIT) or the GND pour (V24_TOP)
        for x, y in OUTLINE[net]:
            o.Append(e.GetLeft() + mm(x), e.GetTop() + mm(y))
    else:
        for x, y in ((e.GetLeft(), e.GetTop()), (e.GetRight(), e.GetTop()),
                     (e.GetRight(), e.GetBottom()), (e.GetLeft(), e.GetBottom())):
            o.Append(x, y)
    b.Add(z)
SPLIT_SHAPE = None
if SPLIT or TOP:
    SPLIT_SHAPE = pcbnew.SHAPE_LINE_CHAIN()
    for x, y in SPLIT or TOP:
        SPLIT_SHAPE.Append(e.GetLeft() + mm(x), e.GetTop() + mm(y))
    SPLIT_SHAPE.SetClosed(True)

# keep-outs: rule areas around the mounting holes
keepouts = [z for z in b.Zones() if z.GetIsRuleArea()]   # each checked for what it forbids
pads = [p for f in b.GetFootprints() for p in f.Pads()]
vias = []      # (x, y) in IU of vias placed so far
tracks = []    # (layer, seg shape, net)
# existing copper (escape stubs, pre-placed vias, routes) is an obstacle too
if True:
    for t in b.GetTracks():
        if t.GetClass() == 'PCB_VIA':
            vias.append((t.GetPosition().x, t.GetPosition().y))
        else:
            tracks.append((t.GetLayer(), pcbnew.SEG(t.GetStart(), t.GetEnd()), t.GetNetname(), tomm(t.GetWidth())))


def legal_via(pos, net):
    if not (e.GetLeft() + mm(EDGE) < pos.x < e.GetRight() - mm(EDGE) and
            e.GetTop() + mm(EDGE) < pos.y < e.GetBottom() - mm(EDGE)):
        return False
    if SPLIT_SHAPE and net in PLANES and net in ('/+24V', '/+3V3'):
        # inside its own zone, clear of the 0.3 mm split by the via's thermal spokes
        if SPLIT_SHAPE.PointInside(pos) != (net == '/+24V') or \
                min(SPLIT_SHAPE.CSegment(i).Distance(pos) for i in range(SPLIT_SHAPE.SegmentCount())) < mm(VIA_D / 2 + 0.45):
            return False
    for k in keepouts:
        if k.GetDoNotAllowVias() and k.Outline().Collide(pos, mm(VIA_D / 2)):
            return False
    for p in pads:
        drilled = p.GetAttribute() in (pcbnew.PAD_ATTRIB_PTH, pcbnew.PAD_ATTRIB_NPTH)
        if p.GetNetname() == net and not drilled:
            # same net: fine to touch copper, but not to sit on the pad itself
            pl = pcbnew.F_Cu if p.IsOnLayer(pcbnew.F_Cu) else pcbnew.B_Cu
            if p.GetEffectiveShape(pl).Collide(pos, mm(VIA_D / 2 - 0.05)):
                return False
            continue
        clr = HV_CLR if p.GetNetname() in HV else CLR
        for layer in (pcbnew.F_Cu, pcbnew.B_Cu):
            if p.IsOnLayer(layer) and p.GetEffectiveShape(layer).Collide(pos, mm(VIA_D / 2 + clr)):
                return False
        if drilled:
            d = p.GetDrillSize()
            r = max(d.x, d.y) / 2
            if math.hypot(pos.x - p.GetPosition().x, pos.y - p.GetPosition().y) < r + mm(VIA_D / 2 + 0.3):
                return False
    for vx, vy in vias:
        if math.hypot(pos.x - vx, pos.y - vy) < mm(VIA_D + CLR):
            return False
    for layer, seg, tnet, *tw in tracks:
        clr = HV_CLR if tnet in HV or net in HV else CLR
        if tnet != net and seg.Distance(pos) < mm(VIA_D / 2 + clr + (tw[0] if tw else TRACK) / 2):
            return False
    return True


def legal_track(layer, a, c, net, own_pad):
    seg = pcbnew.SEG(a, c)
    for k in keepouts:
        if k.GetDoNotAllowTracks() and k.IsOnLayer(layer) and k.Outline().Collide(seg, mm(TRACK / 2)):
            return False
    for p in pads:
        if p is own_pad or p.GetNetname() == net or not p.IsOnLayer(layer):
            continue
        clr = HV_CLR if p.GetNetname() in HV else CLR
        if p.GetEffectiveShape(layer).Collide(seg, mm(clr + TRACK / 2)):
            return False
    for vx, vy in vias:
        if seg.Distance(pcbnew.VECTOR2I(int(vx), int(vy))) < mm(VIA_D / 2 + CLR + TRACK / 2):
            return False
    for tl, s2, tnet, *tw in tracks:
        if tl == layer and tnet != net and seg.Collide(s2, mm(CLR + TRACK / 2 + (tw[0] if tw else TRACK) / 2)):
            return False
    return True


def reaches_via(p, net):
    """True if same-net tracks joined end to end lead from the pad to a via."""
    segs = [s for _, s, tn, *_ in tracks if tn == net]
    ends = [pt for s in segs for pt in (s.A, s.B) if p.HitTest(pt)]
    seen = set()
    while ends:
        pt = ends.pop()
        if (pt.x, pt.y) in seen:
            continue
        seen.add((pt.x, pt.y))
        if any(math.hypot(pt.x - vx, pt.y - vy) < mm(0.05) for vx, vy in vias):
            return True
        for s in segs:
            if s.A == pt:
                ends.append(s.B)
            elif s.B == pt:
                ends.append(s.A)
    return False


added, failed = 0, []
for f in b.GetFootprints():
    if ONLY and f.GetReference() not in ONLY:
        continue
    for p in f.Pads():
        net = p.GetNetname()
        if net not in PLANES or p.GetAttribute() != pcbnew.PAD_ATTRIB_SMD or p.IsOnLayer(PLANES[net]):
            continue
        # SKIP_ROUTED: a pad that block copper (blocks.py) already ties to a via keeps that
        if os.environ.get('SKIP_ROUTED') and reaches_via(p, net):
            continue
        layer = pcbnew.B_Cu if p.IsOnLayer(pcbnew.B_Cu) else pcbnew.F_Cu
        TRACK, VIA_D, VIA_DRILL = FAN[net]
        CLR = HV_CLR if net in HV else 0.2
        c = p.GetPosition()
        bb = p.GetBoundingBox()
        if min(bb.GetWidth(), bb.GetHeight()) > mm(3):
            # exposed pad: a grid of vias inside the pad itself
            n = 3
            pitch = min(bb.GetWidth(), bb.GetHeight()) / (n + 0.5)
            for i in range(n):
                for j in range(n):
                    pos = pcbnew.VECTOR2I(int(c.x + (i - 1) * pitch), int(c.y + (j - 1) * pitch))
                    # the via goes through to the other side: keep it off other nets' pads there
                    if any(q.GetNetname() != net and q.IsOnLayer(ql) and
                           q.GetEffectiveShape(ql).Collide(pos, mm(VIA_D / 2 + (HV_CLR if q.GetNetname() in HV else 0.2)))
                           for q in pads for ql in (pcbnew.F_Cu, pcbnew.B_Cu)):
                        continue
                    v = pcbnew.PCB_VIA(b)
                    v.SetPosition(pos)
                    v.SetWidth(mm(VIA_D))
                    v.SetDrill(mm(VIA_DRILL))
                    v.SetNet(p.GetNet())
                    v.SetLocked(True)
                    b.Add(v)
                    vias.append((pos.x, pos.y))
                    added += 1
            continue
        best = None
        for size in [FAN[net]] + ([FAN_SMALL] if FAN[net] != FAN_SMALL and os.environ.get('NARROW') else []):
            TRACK, VIA_D, VIA_DRILL = size
            for ring in range(0, 14):
                d = min(bb.GetWidth(), bb.GetHeight()) / 2 + mm(VIA_D / 2 + 0.1 + ring * 0.2)
                for k in range(16):
                    a = k * math.pi / 8
                    pos = pcbnew.VECTOR2I(int(c.x + d * math.cos(a)), int(c.y + d * math.sin(a)))
                    if legal_via(pos, net) and legal_track(layer, c, pos, net, p):
                        best = pos
                        break
                if best:
                    break
            if best:
                break
        if best is None:
            failed.append(f'{f.GetReference()}.{p.GetNumber()}')
            continue
        t = pcbnew.PCB_TRACK(b)
        t.SetStart(c)
        t.SetEnd(best)
        t.SetWidth(mm(TRACK))
        t.SetLayer(layer)
        t.SetNet(p.GetNet())
        t.SetLocked(True)
        b.Add(t)
        v = pcbnew.PCB_VIA(b)
        v.SetPosition(best)
        v.SetWidth(mm(VIA_D))
        v.SetDrill(mm(VIA_DRILL))
        v.SetNet(p.GetNet())
        v.SetLocked(True)
        b.Add(v)
        vias.append((best.x, best.y))
        tracks.append((layer, pcbnew.SEG(c, best), net, TRACK))
        added += 1

pcbnew.ZONE_FILLER(b).Fill(b.Zones())
pcbnew.SaveBoard(sys.argv[1], b)
print('fanout vias', added, 'failed', failed)
