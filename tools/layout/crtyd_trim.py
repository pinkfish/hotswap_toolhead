"""Cut a footprint's courtyard to its body and pads plus a margin.
    crtyd_trim.py board.kicad_pcb REF=margin_mm ...
The courtyard becomes one rectangle around the pads and the fab-layer body outline, `margin`
larger (IPC's nominal courtyard excess is 0.25 mm; KiCad's connector footprints use 0.5). The
logic board's link socket J3 needs it: its pads reach to 0.68 mm from the right-hand edge, and
the library's 0.5 mm courtyard would put the panel's mouse-bite holes inside it. Copper is
untouched, so it can run on a routed board.
"""
import sys

import pcbnew

mm = pcbnew.FromMM
b = pcbnew.LoadBoard(sys.argv[1])
for arg in sys.argv[2:]:
    ref, margin = arg.split('=')
    f = b.FindFootprintByReference(ref)
    crt = pcbnew.B_CrtYd if f.IsFlipped() else pcbnew.F_CrtYd
    fab = pcbnew.B_Fab if f.IsFlipped() else pcbnew.F_Fab
    boxes = [p.GetBoundingBox() for p in f.Pads()] + \
        [g.GetBoundingBox() for g in f.GraphicalItems() if g.GetLayer() == fab and isinstance(g, pcbnew.PCB_SHAPE)]
    m = mm(float(margin))
    lo = pcbnew.VECTOR2I(min(x.GetLeft() for x in boxes) - m, min(x.GetTop() for x in boxes) - m)
    hi = pcbnew.VECTOR2I(max(x.GetRight() for x in boxes) + m, max(x.GetBottom() for x in boxes) + m)
    for g in [g for g in f.GraphicalItems() if g.GetLayer() == crt]:
        f.Remove(g)
    r = pcbnew.PCB_SHAPE(f, pcbnew.SHAPE_T_RECTANGLE)
    r.SetLayer(crt)
    r.SetWidth(mm(0.05))
    r.SetStart(lo)
    r.SetEnd(hi)
    f.Add(r)
    print('%s courtyard [%.2f, %.2f .. %.2f, %.2f]' % (ref, *(pcbnew.ToMM(v) - 100 for v in (lo.x, lo.y, hi.x, hi.y))))
pcbnew.SaveBoard(sys.argv[1], b)
