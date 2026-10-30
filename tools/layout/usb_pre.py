"""Hand pre-route of the USB-C data pins and the USBLC6 flow-through.
    usb_pre.py in.kicad_pcb out.kicad_pcb
D+ (B6/A6) joined above the pad row, D- (A7/B7) below it, both on F.Cu;
one via per pair down to U5, whose pins 3-4 and 1-6 are joined straight across.
On to U6 (pins 33/34, top row): the pin row is only ~1.8 mm below J5's pads, and SWCLK
(pin 36) and the A9 VBUS pad need that strip too, so it is laid out here:
- D+ and D- run west on F.Cu from their U5 vias, D+ above, D- below, each to a via
  in front of its pin (D- the outer one, so they don't cross)
- SWCLK leaves pin 36 eastward under the package corner to a via, then F.Cu round the
  BOOT pads (JP3) to R4, which sits on top under JP3
- J5's A9 VBUS pad drops through a via into the space that frees on B.Cu, and runs down to D3
- CC2 (B5) and CC1 (A5) go up through vias above their pads instead, to R21/R20 under the shell
A keep-out stops the router running F.Cu tracks under the receptacle body.
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
# U5's GND pin is boxed in by the pair: its own via, between the two data vias
track('/GND', B, (25.0, 8.34), (25.0, 9.45))
via('/GND', 25.0, 9.45)
FP = {f.GetReference(): f for f in b.GetFootprints()}


def at(ref, num):
    q = [p for p in FP[ref].Pads() if p.GetNumber() == num][0].GetPosition()
    return pcbnew.ToMM(q.x) - O, pcbnew.ToMM(q.y) - O


dn, dp, sw = at('U6', '33'), at('U6', '34'), at('U6', '36')
top = dn[1] - 0.44                         # pin row top edge
# CC2 (B5, 23.25): no room for a via below the pad row (VBUS's via and the D+ lane), so it
# goes up through a via just above the pad and across under the shell on B.Cu to R21
track('/USB_CC2', F, (23.25, 7.69), (23.25, 6.55))
via('/USB_CC2', 23.25, 6.55)
track('/USB_CC2', B, (23.25, 6.55), (23.0, 5.3), (22.1, 5.01))
# CC1 (A5, 26.25) the same way, the via offset right of U5 pin 6, to R20
track('/USB_CC1', F, (26.25, 7.69), (26.25, 6.55), (26.85, 6.35))
via('/USB_CC1', 26.85, 6.35)
track('/USB_CC1', B, (26.85, 6.35), (27.2, 5.4), (27.9, 5.01))
# U5 to U6: D+ lane 0.85 above the vias' row, D- lane 0.7 below it (under the D+ via)
yp, yn = 9.5, 10.05
vp = (dp[0] + 0.2, top - 0.92)             # D+ via in front of pin 34
vn = (dn[0] - 0.15, top - 0.57)            # D- via, outside it
track('/USB_D_P', F, (24.05, 9.35), (23.9, yp), (vp[0] + 0.2, yp), vp)
via('/USB_D_P', *vp)
track('/USB_D_P', B, vp, (dp[0], top - 0.45), dp)
track('/USB_D_N', F, (25.95, 9.35), (25.65, yn), (vn[0] + 0.35, yn), vn)
via('/USB_D_N', *vn)
track('/USB_D_N', B, vn, (dn[0], top - 0.2), dn)
# SWCLK: east under the corner to a via, F.Cu down past JP3's BOOT pad to R4 (on top)
jb = FP['JP3'].GetBoundingBox(False)       # pads only
vs = (sw[0] + 0.75, sw[1])
track('/SWCLK', B, sw, vs)
via('/SWCLK', *vs)
r4s, r4b = at('R4', '2'), at('R4', '1')
xe = pcbnew.ToMM(max(p.GetBoundingBox().GetRight() for p in FP['JP3'].Pads())) - O + 0.4
track('/SWCLK', F, vs, (xe, vs[1] + 0.45), (xe, r4s[1]), r4s)
track('/BOOT_SW', F, at('JP3', '2'), r4b)
# VBUS from A9 (22.55): a via just below the pad, then down to D3's VBUS pad
d3 = at('D3', '2')
W = 0.3
track('/VBUS', F, (22.55, 7.69), (22.55, 8.85))
via('/VBUS', 22.55, 8.85)
track('/VBUS', B, (22.55, 8.85), (22.9, 9.2), (22.9, 10.0), (23.6, 10.3), d3)
W = 0.2
# no F.Cu tracks under the receptacle body, ahead of its pad row (the shell sits there);
# the GND pour may still fill it
k = pcbnew.ZONE(b)
k.SetIsRuleArea(True)
ls = pcbnew.LSET()
ls.AddLayer(F)
k.SetLayerSet(ls)
k.SetDoNotAllowTracks(True)
k.SetDoNotAllowVias(False)                 # GND vias for the parts underneath are fine
k.SetDoNotAllowZoneFills(False)
k.SetDoNotAllowPads(False)
k.SetDoNotAllowFootprints(False)
k.SetZoneName('USB-C body keep-out')
o = k.Outline(); o.NewOutline()
for x, y in ((20.0, -0.6), (30.0, -0.6), (30.0, 6.2), (20.0, 6.2)):
    o.Append(mm(O + x), mm(O + y))
b.Add(k)
pcbnew.SaveBoard(dst, b)
