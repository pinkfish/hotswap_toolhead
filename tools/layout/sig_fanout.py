"""Escape fanout: a locked stub and via for chosen pads, placed outward
from the owner's centre.   sig_fanout.py board.kicad_pcb REF:pad,pad,...
Runs on a board that may already carry tracks and vias; all are obstacles."""
import math, sys
import pcbnew

mm = pcbnew.FromMM
b = pcbnew.LoadBoard(sys.argv[1])
e = b.GetBoardEdgesBoundingBox()
VIA_D, VIA_DRILL, CLR, TRACK = 0.6, 0.3, 0.2, 0.2
HV = {'/VIN_RAW', '/VIN_F', '/+24V', '/HEAT_N', '/FAN_N', '/FAN_P'}
keepouts = [z for z in b.Zones() if z.GetIsRuleArea() and z.GetDoNotAllowVias()]
pads = [p for f in b.GetFootprints() for p in f.Pads()]
vias = [(t.GetPosition(), pcbnew.ToMM(t.GetWidth(pcbnew.F_Cu)), t.GetNetname()) for t in b.GetTracks() if t.Type() == pcbnew.PCB_VIA_T]
tracks = [(t.GetLayer(), pcbnew.SEG(t.GetStart(), t.GetEnd()), pcbnew.ToMM(t.GetWidth()), t.GetNetname())
          for t in b.GetTracks() if t.Type() == pcbnew.PCB_TRACE_T]


def clr_of(net):
    return 0.32 if net in HV else CLR


def legal(pos, layer, a, net, own):
    if not (e.GetLeft() + mm(0.8) < pos.x < e.GetRight() - mm(0.8) and e.GetTop() + mm(0.8) < pos.y < e.GetBottom() - mm(0.8)):
        return False
    seg = pcbnew.SEG(a, pos)
    for k in keepouts:
        if k.Outline().Collide(pos, mm(VIA_D / 2)) or k.Outline().Collide(seg, mm(TRACK / 2)):
            return False
    for p in pads:
        if p.GetNetname() == net and p is not own:
            continue
        for l in (pcbnew.F_Cu, pcbnew.B_Cu):
            if not p.IsOnLayer(l):
                continue
            sh = p.GetEffectiveShape(l)
            if p is own:
                if l == layer:
                    continue
                if sh.Collide(pos, mm(VIA_D / 2 - 0.05)):
                    return False
                continue
            c = clr_of(p.GetNetname())
            if sh.Collide(pos, mm(VIA_D / 2 + c)):
                return False
            if l == layer and sh.Collide(seg, mm(c + TRACK / 2)):
                return False
        if p.GetAttribute() in (pcbnew.PAD_ATTRIB_PTH, pcbnew.PAD_ATTRIB_NPTH):
            d = p.GetDrillSize()
            if math.hypot(pos.x - p.GetPosition().x, pos.y - p.GetPosition().y) < max(d.x, d.y) / 2 + mm(VIA_D / 2 + 0.3):
                return False
    for vp, vd, vn in vias:
        if vn != net and math.hypot(pos.x - vp.x, pos.y - vp.y) < mm(VIA_D / 2 + vd / 2 + CLR):
            return False
        if vn != net and seg.Distance(vp) < mm(vd / 2 + CLR + TRACK / 2):
            return False
    for tl, s2, tw, tn in tracks:
        if tn == net:
            continue
        if s2.Distance(pos) < mm(VIA_D / 2 + CLR + tw / 2):
            return False
        if tl == layer and seg.Collide(s2, mm(CLR + tw / 2 + TRACK / 2)):
            return False
    return True


done, failed = [], []
for arg in sys.argv[2:]:
    ref, nums = arg.split(':')
    f = b.FindFootprintByReference(ref)
    c0 = f.GetPosition()
    for num in nums.split(','):
        p = [q for q in f.Pads() if q.GetNumber() == num][0]
        net = p.GetNetname()
        layer = pcbnew.B_Cu if p.IsOnLayer(pcbnew.B_Cu) else pcbnew.F_Cu
        a = p.GetPosition()
        dx, dy = a.x - c0.x, a.y - c0.y
        ux, uy = (math.copysign(1, dx), 0) if abs(dx) > abs(dy) else (0, math.copysign(1, dy))
        best = None
        for out in [1.0 + 0.1 * i for i in range(25)]:
            for lat in (0, 0.25, -0.25, 0.5, -0.5, 0.75, -0.75, 1.0, -1.0):
                pos = pcbnew.VECTOR2I(int(a.x + mm(out * ux - lat * uy)), int(a.y + mm(out * uy + lat * ux)))
                if legal(pos, layer, a, net, p):
                    best = pos
                    break
            if best:
                break
        if best is None:
            failed.append(f'{ref}.{num}')
            continue
        t = pcbnew.PCB_TRACK(b); t.SetStart(a); t.SetEnd(best); t.SetWidth(mm(TRACK)); t.SetLayer(layer)
        t.SetNet(p.GetNet()); t.SetLocked(True); b.Add(t)
        v = pcbnew.PCB_VIA(b); v.SetPosition(best); v.SetWidth(mm(VIA_D)); v.SetDrill(mm(VIA_DRILL))
        v.SetNet(p.GetNet()); v.SetLocked(True); b.Add(v)
        vias.append((best, VIA_D, net)); tracks.append((layer, pcbnew.SEG(a, best), TRACK, net))
        done.append(f'{ref}.{num}')
pcbnew.SaveBoard(sys.argv[1], b)
print('escape vias', len(done), 'failed', failed)
