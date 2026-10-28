"""buck_pre.py board.kicad_pcb - pre-route the buck's power links on B.Cu.
VIN_LOGIC from D3 to C4 runs along y 10.9 between D7 and C4; BUCK_SW goes U1 pin 6 -> D9 ->
L1 through the lane between C4 and D9 (below D9 the USB pair's vias are in the way).
Runs before planes_fanout so the top-side GND pads' vias land clear of both.
"""
import sys, pcbnew
mm = pcbnew.FromMM
b = pcbnew.LoadBoard(sys.argv[1]); O = 100.0
P = lambda x, y: pcbnew.VECTOR2I(mm(O + x), mm(O + y))


def at(ref, num):
    q = [p for p in b.FindFootprintByReference(ref).Pads() if p.GetNumber() == num][0].GetPosition()
    return pcbnew.ToMM(q.x) - O, pcbnew.ToMM(q.y) - O


def tr(net, w, *pts):
    for a, c in zip(pts, pts[1:]):
        t = pcbnew.PCB_TRACK(b); t.SetStart(P(*a)); t.SetEnd(P(*c)); t.SetWidth(mm(w))
        t.SetLayer(pcbnew.B_Cu); t.SetNet(b.FindNet(net)); t.SetLocked(True); b.Add(t)


d3, c4 = at('D3', '1'), at('C4', '1')
tr('/VIN_LOGIC', 0.3, d3, (d3[0] - 0.3, 10.9), (c4[0] + 0.55, 10.9), (c4[0], 11.5), c4)
u1, d9, l1 = at('U1', '6'), at('D9', '1'), at('L1', '1')
tr('/BUCK_SW', 0.4, u1, (u1[0] + 1.1, u1[1]), (d9[0] - 0.3, d9[1] - 0.45), d9)
tr('/BUCK_SW', 0.4, (d9[0] + 0.3, d9[1] - 0.35), (d9[0] + 0.75, 13.75), (l1[0] - 1.0, 13.75),
   (l1[0] - 0.4, 14.35), l1)
pcbnew.SaveBoard(sys.argv[1], b)
print('buck pre-routed')
