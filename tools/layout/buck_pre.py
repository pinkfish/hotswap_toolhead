"""buck_pre.py board.kicad_pcb - pre-route the buck's power links on B.Cu.
The buck sits in the right-hand strip (place.py).  D7's cathode, also fed from USB through
D3, starts a VIN_LOGIC rail down the gap between U1 and C4 that picks up U1 pins 4/5, C4 and
C5.  The switch node runs from U1 pin 6 down the left of C5 to L1 pad 1 and on to D9 below
it, with C6's SW pad joining on the way; C6's BOOT pad goes straight to U1 pin 1, and the
feedback line runs up between D7's pads to R3/R2.  Runs before planes_fanout so the GND and
+24V pads' vias land clear of these tracks.
"""
import sys

import pcbnew

mm = pcbnew.FromMM
b = pcbnew.LoadBoard(sys.argv[1])
O = 100.0
FP = {f.GetReference(): f for f in b.GetFootprints()}


def at(ref, num):
    q = [p for p in FP[ref].Pads() if p.GetNumber() == num][0].GetPosition()
    return pcbnew.ToMM(q.x) - O, pcbnew.ToMM(q.y) - O


def route(net, w, *pts):
    for a, c in zip(pts, pts[1:]):
        t = pcbnew.PCB_TRACK(b)
        t.SetStart(pcbnew.VECTOR2I(mm(O + a[0]), mm(O + a[1])))
        t.SetEnd(pcbnew.VECTOR2I(mm(O + c[0]), mm(O + c[1])))
        t.SetWidth(mm(w))
        t.SetLayer(pcbnew.B_Cu)
        t.SetNet(b.FindNet(net))
        t.SetLocked(True)
        b.Add(t)


# VIN_LOGIC: a rail 1.1 mm right of U1's pin column, between it and C4's GND pad
d7, p4, p5, c4, c5 = at('D7', '1'), at('U1', '4'), at('U1', '5'), at('C4', '1'), at('C5', '1')
xr = p4[0] + 1.1
route('/VIN_LOGIC', 0.4, d7, (xr, d7[1] + 0.65), (xr, p4[1]), (xr, c4[1]), c4)
route('/VIN_LOGIC', 0.4, p4, (xr, p4[1]))
route('/VIN_LOGIC', 0.3, p5, p4)
route('/VIN_LOGIC', 0.4, c5, (xr, c4[1]))
# USB supply in: D3's cathode down to D7's, between R2/R3 and SW1's locating holes
d3 = at('D3', '1')
route('/VIN_LOGIC', 0.3, d3, (d3[0] + 0.3, d3[1] + 0.6), (d3[0] + 0.3, d7[1] - 0.7), d7)
# feedback: U1 pin 3 up between D7's pads to R3's FB pad and on up to R2's, right above it
p3, r3, r2 = at('U1', '3'), at('R3', '1'), at('R2', '2')
xf = p3[0] - 0.35
route('/BUCK_FB', 0.2, p3, (xf, p3[1] - 0.76), (xf, r3[1] + 0.6), r3, r2)
# switch node: U1 pin 6 -> L1 pad 1 -> D9 pad 1, with C6's SW pad teed in
p6, c6sw, l1, d9 = at('U1', '6'), at('C6', '2'), at('L1', '1'), at('D9', '1')
knee = (l1[0], p6[1] + 1.6)
route('/BUCK_SW', 0.4, p6, (p6[0], p6[1] + 0.85), knee, (l1[0], l1[1] - 1.3))
route('/BUCK_SW', 0.4, c6sw, (c6sw[0], knee[1] - 0.6), knee)
route('/BUCK_SW', 0.4, (l1[0], l1[1] + 1.5), (d9[0], d9[1] - 0.6), d9)
# bootstrap
route('/BUCK_BOOT', 0.25, at('U1', '1'), at('C6', '1'))
pcbnew.SaveBoard(sys.argv[1], b)
print('buck pre-routed')
