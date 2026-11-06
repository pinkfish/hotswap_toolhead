"""USB pre-route for the logic board of the stack (plan_logic.py placement).
    usb_stack_pre.py board.kicad_pcb
J5's pad row is on the top side directly over the MCU (U6, bottom side), so no via can drop
beside the data pads. D+ (A6/B6) is strapped above the pad row and D- (A7/B7) below it, both on
F.Cu, and each drops to a via under the receptacle body, below U6's bottom pins:
  - D+ runs on B.Cu below U6 and J5's right shield leg, then up the gap between the leg and U5
    to U5 pin 3, with U6 pin 34 joining it from the left
  - D- runs on In2 from its via to a via under U5 pin 1, and on up to a via right of U6 pin 33
SWCLK (U6 pin 36), boxed in by D+, drops to a via just right of the pin and runs up on F.Cu to
R4. U5's GND pin, boxed in by D+ and its own pins, gets a 0.5 mm via between it and VBUS.
Board mm from the top-left, seen from the top. Everything is locked and grouped.
"""
import sys

import pcbnew

O = 100.0
mm = pcbnew.FromMM
W = 0.2   # the pair and SWCLK; USB full speed has no impedance target worth widening for
VIA = (0.6, 0.3)
F, I2, B = pcbnew.F_Cu, pcbnew.In2_Cu, pcbnew.B_Cu

ROUTES = {
    '/USB_D_P': [
        (F, [(13.25, 18.58), (13.25, 18.25), (14.25, 18.25), (14.25, 18.58)]),   # A6 - B6, above the row
        (F, [(14.25, 20.03), (14.25, 20.95)]),                                     # B6 down to its via
        (B, [(14.25, 20.95), (14.25, 21.55), (14.7, 22.0), (18.2, 22.0), (18.65, 21.55),
             (18.65, 17.8), (19.81, 17.85)]),                                      # round to U5 pin 3
        (B, [(16.94, 17.55), (18.4, 17.55), (18.65, 17.8)]),                       # U6 pin 34
    ],
    '/USB_D_N': [
        (F, [(12.75, 20.03), (12.75, 20.35), (13.75, 20.35), (13.75, 20.03)]),   # B7 - A7, below the row
        (F, [(13.0, 20.35), (13.0, 20.95)]),                                       # down to its via
        (I2, [(13.0, 20.95), (13.8, 21.75), (18.7, 21.75), (19.75, 20.7)]),        # to the via by U5 pin 1
        (B, [(19.75, 20.7), (19.75, 19.75)]),                                      # U5 pin 1
        (I2, [(19.75, 20.7), (19.0, 19.95), (19.0, 17.3), (18.3, 16.6)]),          # on up to U6
        (B, [(16.94, 17.05), (17.85, 17.05), (18.3, 16.6)]),                       # U6 pin 33
    ],
    '/SWCLK': [
        (B, [(16.94, 18.55), (17.85, 18.55), (17.95, 18.62)]),                     # U6 pin 36
        (F, [(17.95, 18.62), (17.95, 17.4), (17.4, 16.9)]),                        # up to R4 pin 2
    ],
    '/GND': [(B, [(19.81, 18.8), (20.96, 18.8)])],                                 # U5 pin 2
}
VIAS = {'/USB_D_P': [(14.25, 20.95)], '/USB_D_N': [(13.0, 20.95), (19.75, 20.7), (18.3, 16.6)],
        '/SWCLK': [(17.95, 18.62)], '/GND': [(20.96, 18.8, 0.5)]}

b = pcbnew.LoadBoard(sys.argv[1])
g = pcbnew.PCB_GROUP(b)
g.SetName('usb pre-routes')
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
    for x, y, *d in VIAS[net]:
        v = pcbnew.PCB_VIA(b)
        v.SetPosition(P(x, y))
        v.SetWidth(mm(d[0] if d else VIA[0]))
        v.SetDrill(mm(VIA[1]))
        v.SetNet(ni)
        v.SetLocked(True)
        b.Add(v)
        g.AddItem(v)
pcbnew.SaveBoard(sys.argv[1], b)
print('usb pre-routes: %d tracks, %d vias' % (n, sum(len(v) for v in VIAS.values())))
