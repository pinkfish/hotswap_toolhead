"""Hand pre-route of the USB-C data pins and the USBLC6 flow-through.
    usb_pre.py in.kicad_pcb out.kicad_pcb
D+ (B6/A6) joined above the pad row, D- (A7/B7) below it, both on F.Cu;
one via per pair down to U5, whose pins 3-4 and 1-6 are joined straight across.
"""
import sys

import pcbnew

mm = pcbnew.FromMM
src, dst = sys.argv[1:3]
b = pcbnew.LoadBoard(src)
O = 100.0
W = 0.2


def P(x, y):
    return pcbnew.VECTOR2I(mm(O + x), mm(O + y))


def track(net, layer, *pts):
    for a, c in zip(pts, pts[1:]):
        t = pcbnew.PCB_TRACK(b)
        t.SetStart(P(*a))
        t.SetEnd(P(*c))
        t.SetWidth(mm(W))
        t.SetLayer(layer)
        t.SetNet(b.FindNet(net))
        t.SetLocked(True)
        b.Add(t)


def via(net, x, y):
    v = pcbnew.PCB_VIA(b)
    v.SetPosition(P(x, y))
    v.SetWidth(mm(0.6))
    v.SetDrill(mm(0.3))
    v.SetNet(b.FindNet(net))
    v.SetLocked(True)
    b.Add(v)


F, B = pcbnew.F_Cu, pcbnew.B_Cu
# D+: B6 (24.25) and A6 (25.25), over the top of A7
track('/USB_D_P', F, (24.25, 7.69), (24.25, 6.65), (25.25, 6.65), (25.25, 7.69))
track('/USB_D_P', F, (24.25, 7.69), (24.25, 8.415), (24.05, 9.35))
via('/USB_D_P', 24.05, 9.35)
track('/USB_D_P', B, (24.05, 9.35), (24.05, 8.34), (24.05, 6.06))
# D-: A7 (24.75) and B7 (25.75), under A6
# all three D- pieces meet at (25.75, 8.75); a U with the via stub off its middle vertex
# sends Freerouting 2.2.4 into endless recursion in PolylineTrace.combine
track('/USB_D_N', F, (24.75, 7.69), (24.75, 8.75), (25.75, 8.75))
track('/USB_D_N', F, (25.75, 7.69), (25.75, 8.75))
track('/USB_D_N', F, (25.75, 8.75), (25.95, 9.35))
via('/USB_D_N', 25.95, 9.35)
track('/USB_D_N', B, (25.95, 9.35), (25.95, 8.34), (25.95, 6.06))
# The pair arrives at U6 in the opposite order (D- pin 33 left of D+ pin 34), so it
# crosses once, right below U5: D- drops to B.Cu between D3's pads and comes back up
# between the LED rows; D+ stays on F.Cu round the LED column.  Needs C1 at y <= 14.6
# so its GND pad clears the via above pin 34.
track('/USB_D_P', F, (24.05, 9.35), (24.85, 10.15), (26.0, 10.15), (26.4, 10.55), (26.4, 15.55),
      (26.0, 15.95), (19.6, 15.95))
via('/USB_D_P', 19.6, 15.95)
track('/USB_D_P', B, (19.6, 15.95), (19.25, 16.3), (19.25, 16.75))
track('/USB_D_N', B, (25.95, 9.35), (25.45, 9.85), (25.1, 10.2), (25.1, 11.9), (25.65, 12.2))
# U5's GND pin is boxed in by the pair: its own via, between the two data vias
track('/GND', B, (25.0, 8.34), (25.0, 9.45))
via('/GND', 25.0, 9.45)
via('/USB_D_N', 25.65, 12.2)
track('/USB_D_N', F, (25.65, 12.2), (25.45, 12.0), (18.6, 12.0), (18.0, 12.6), (18.0, 15.95))
via('/USB_D_N', 18.0, 15.95)
track('/USB_D_N', B, (18.0, 15.95), (18.6, 15.95), (18.75, 16.1), (18.75, 16.75))
# the D+ run walls the LED anodes off from R5/R6 on F.Cu: drop them to B.Cu inside it
track('/LED1_A', F, (24.79, 11.0), (25.6, 11.0), (25.75, 10.85))
via('/LED1_A', 25.75, 10.85)
track('/LED2_A', F, (24.79, 13.0), (25.45, 13.0), (25.75, 13.3))
via('/LED2_A', 25.75, 13.3)
pcbnew.SaveBoard(dst, b)
