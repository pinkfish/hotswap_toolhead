"""CAN pre-route for the logic board of the stack (plan_logic.py placement).
    can_stack_pre.py board.kicad_pcb
U3 (bottom side, under J1's CAN pins) has CAN_H/CAN_L facing up and TX/RX facing down, toward
RESET, with the MCU corner (crystal, decoupling) between it and U6:
  - CAN_H and CAN_L run on B.Cu straight up to J1 pins 3 and 4, CAN_L passing left of pin 3
  - RX leaves U3 pin 4 to the left and runs up the edge to a via, TX leaves pin 1 to the right to
    a via; both cross under the corner on In2 (RX below J1's pins, both in the strip between the
    corner's vias and J1's power pins) to vias just above U6 pins 19 and 20
D4, R11 and JP1 on the top side are left to the router (J1's pins reach both sides).
Board mm from the top-left, seen from the top. Everything is locked and grouped.
"""
import sys

import pcbnew

O = 100.0
mm = pcbnew.FromMM
W = 0.2
VIA = (0.6, 0.3)
I2, B = pcbnew.In2_Cu, pcbnew.B_Cu

ROUTES = {
    '/CAN_H': [(B, [(2.725, 9.25), (2.725, 8.6), (3.68, 7.65)])],
    '/CAN_L': [(B, [(2.075, 9.25), (2.075, 8.6), (2.3, 8.375), (2.3, 6.35), (3.0, 5.65), (3.68, 5.65)])],
    '/CAN_RX': [
        (B, [(1.425, 12.15), (0.85, 12.15), (0.85, 8.4)]),
        (I2, [(0.85, 8.4), (1.2, 8.75), (5.25, 8.75), (5.6, 9.1), (5.6, 11.0), (5.95, 11.35),
              (13.2, 11.35), (13.55, 11.05)]),
        (B, [(13.55, 11.05), (13.75, 11.25), (13.75, 12.36)]),
    ],
    '/CAN_TX': [
        (B, [(3.375, 12.15), (3.675, 12.45), (4.2, 12.45)]),
        (I2, [(4.2, 12.45), (4.9, 11.75), (13.9, 11.75), (14.4, 11.35)]),
        (B, [(14.4, 11.35), (14.25, 11.5), (14.25, 12.36)]),
    ],
}
VIAS = {'/CAN_H': [], '/CAN_L': [], '/CAN_RX': [(0.85, 8.4), (13.55, 11.05)],
        '/CAN_TX': [(4.2, 12.45), (14.4, 11.35)]}

b = pcbnew.LoadBoard(sys.argv[1])
g = pcbnew.PCB_GROUP(b)
g.SetName('can pre-routes')
b.Add(g)


def P(x, y):
    return pcbnew.VECTOR2I(mm(O + x), mm(O + y))


n = 0
for net, runs in ROUTES.items():
    ni = b.FindNet(net)
    for layer, pts in runs:
        for a, c in zip(pts, pts[1:]):
            t = pcbnew.PCB_TRACK(b)
            t.SetStart(P(*a))
            t.SetEnd(P(*c))
            t.SetWidth(mm(W))
            t.SetLayer(layer)
            t.SetNet(ni)
            t.SetLocked(True)
            b.Add(t)
            g.AddItem(t)
            n += 1
    for x, y in VIAS[net]:
        v = pcbnew.PCB_VIA(b)
        v.SetPosition(P(x, y))
        v.SetWidth(mm(VIA[0]))
        v.SetDrill(mm(VIA[1]))
        v.SetNet(ni)
        v.SetLocked(True)
        b.Add(v)
        g.AddItem(v)
pcbnew.SaveBoard(sys.argv[1], b)
print('can pre-routes: %d tracks, %d vias' % (n, sum(len(v) for v in VIAS.values())))
