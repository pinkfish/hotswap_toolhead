"""left_pre.py board.kicad_pcb - pre-route the lines leaving U6's left side, on B.Cu.
TH_ADC (pin 13) and SENS_IN (pin 14) leave side by side and run down parallel lanes past
the crystal cluster, TH_ADC inside, so they never cross:
- TH_ADC drops beside C15/C14 to R19, picks up C19 next to it and, through one via, the
  D6 clamp on top: the filter and clamp stay within a few mm of the pin
- SENS_IN drops one lane further out, turns west under C16 and comes up through a via
  under C20, the switch input's filter cap on top
CAN_TX/CAN_RX run in two more lanes outside SENS_IN's, down past U3's pin column, and
U3's +3V3 pin, boxed in by the CAN lanes, is fed through a via beside it. FAN_PWM
crosses the lanes on F.Cu just below JP1, so U3's CAN pins stay clear.
Runs before planes_fanout so the plane vias land clear of all of these.
"""
import sys

import pcbnew

mm = pcbnew.FromMM
b = pcbnew.LoadBoard(sys.argv[1])
O = 100.0
FP = {f.GetReference(): f for f in b.GetFootprints()}
F, B = pcbnew.F_Cu, pcbnew.B_Cu


def at(ref, num):
    q = [p for p in FP[ref].Pads() if p.GetNumber() == num][0].GetPosition()
    return pcbnew.ToMM(q.x) - O, pcbnew.ToMM(q.y) - O


def pad_net(ref, net):
    p = [p for p in FP[ref].Pads() if p.GetNetname() == net][0].GetPosition()
    return pcbnew.ToMM(p.x) - O, pcbnew.ToMM(p.y) - O


def route(net, layer, *pts):
    for a, c in zip(pts, pts[1:]):
        t = pcbnew.PCB_TRACK(b)
        t.SetStart(pcbnew.VECTOR2I(mm(O + a[0]), mm(O + a[1])))
        t.SetEnd(pcbnew.VECTOR2I(mm(O + c[0]), mm(O + c[1])))
        t.SetWidth(mm(0.2))
        t.SetLayer(layer)
        t.SetNet(b.FindNet(net))
        t.SetLocked(True)
        b.Add(t)


def via(net, x, y):
    v = pcbnew.PCB_VIA(b)
    v.SetPosition(pcbnew.VECTOR2I(mm(O + x), mm(O + y)))
    v.SetWidth(mm(0.6))
    v.SetDrill(mm(0.3))
    v.SetNet(b.FindNet(net))
    v.SetLocked(True)
    b.Add(v)


th, sens = at('U6', '13'), at('U6', '14')
r19, c19, d6 = pad_net('R19', '/TH_ADC'), pad_net('C19', '/TH_ADC'), pad_net('D6', '/TH_ADC')
c20 = pad_net('C20', '/SENS_IN')
# TH_ADC: lane 0.45 mm left of C15's pads, down to R19, C19 alongside, via up to D6
xt = pad_net('C15', '/NRST')[0] - 0.75
route('/TH_ADC', B, th, (xt, th[1]), (xt, r19[1] - 0.6), r19, c19)
vy = d6[1] - 0.75
via('/TH_ADC', xt, vy)
route('/TH_ADC', F, (xt, vy), (xt, d6[1]), d6)
# SENS_IN: lane 0.6 mm further out, west between C16 and C19, up under C20
xs, ys = xt - 0.6, r19[1] - 0.75
xv = c20[0] + 1.6
route('/SENS_IN', B, sens, (xs, sens[1]), (xs, ys), (xv, ys))
via('/SENS_IN', xv, ys)
route('/SENS_IN', F, (xv, ys), (c20[0], ys), c20)
# CAN_TX / CAN_RX: straight across from pins 20/19 and down two lanes between U3's pin
# column and SENS_IN's, TX inside to U3 pin 1, RX outside to pin 4 at the bottom
tx, rx = at('U6', '20'), at('U6', '19')
u3tx, u3rx = pad_net('U3', '/CAN_TX'), pad_net('U3', '/CAN_RX')
xtx, xrx = u3tx[0] + 0.25, xs - 0.55
route('/CAN_TX', B, tx, (xtx, tx[1]), (xtx, u3tx[1] - 0.45), u3tx)
route('/CAN_RX', B, rx, (xrx, rx[1]), (xrx, u3rx[1]), u3rx)          # level with pin 4, clear of pin 3
# +3V3 for U3 pin 3, which sits inside the CAN_TX/CAN_RX loop: a via beside the pin, then
# F.Cu round to D6's +3V3 pad, with a second via down to C16, U3's decoupling cap
p3 = pad_net('U3', '/+3V3')
p3r = max(pcbnew.ToMM(p.GetBoundingBox().GetRight()) for p in FP['U3'].Pads() if p.GetNetname() == '/+3V3') - O
c16, d6v = pad_net('C16', '/+3V3'), pad_net('D6', '/+3V3')
lv = (p3r + 0.51, p3[1])
xt3 = c16[0] + 0.18
route('/+3V3', B, p3, lv)
via('/+3V3', *lv)
route('/+3V3', F, lv, (xt3, lv[1]), (xt3, c16[1] - 0.75), (xt3, d6v[1]), d6v)
via('/+3V3', xt3, c16[1] - 0.75)
route('/+3V3', B, (xt3, c16[1] - 0.75), c16)
# CAN_H / CAN_L at U3: pins 6/7 face H1's keep-out, with one track's width between them,
# and pin 8 (GND) above them. Pins 8 and 2 tie into the exposed pad instead of taking a via;
# CAN_H takes the corridor up and across under D4 to its pad 1, and CAN_L drops through a
# via below pin 5 and runs up on F.Cu to JP1, with a second via down to D4 pad 2
ep = [p for p in FP['U3'].Pads() if p.GetNumber() == ''][0].GetBoundingBox()
epl, epr = pcbnew.ToMM(ep.GetLeft()) - O, pcbnew.ToMM(ep.GetRight()) - O
g8, g2 = at('U3', '8'), at('U3', '2')
route('/GND', B, g8, (epl + 0.2, g8[1]))
route('/GND', B, g2, (epr - 0.2, g2[1]))
ec = ((epl + epr) / 2, pcbnew.ToMM(ep.GetCenter().y) - O)
via('/GND', ec[0] - 0.15, ec[1] + 0.7)    # the pad's plane via, clear of FAN_PWM and the +3V3 feed on top
ch, cl = at('U3', '7'), at('U3', '6')
d4h, d4l, jl2 = pad_net('D4', '/CAN_H'), pad_net('D4', '/CAN_L'), pad_net('JP1', '/CAN_L')
xc = ch[0] - 0.76                          # corridor between the pins and H1's keep-out
yh = d4h[1] + 1.21                         # under D4's pads, above pin 8
route('/CAN_H', B, ch, (xc, ch[1]), (xc, yh), (d4h[0], yh), d4h)
v1 = (xc + 0.11, cl[1] + 1.42)             # below pin 5, clear of C20 on top
route('/CAN_L', B, cl, (xc, cl[1]), (xc, v1[1] - 0.35), v1)
via('/CAN_L', *v1)
v2 = (xc + 0.46, d4l[1] + 0.06)            # beside D4 pad 2
route('/CAN_L', F, v1, (v1[0], jl2[1] + 0.35), (v2[0], jl2[1]), jl2)
route('/CAN_L', F, (v2[0], jl2[1]), v2)
via('/CAN_L', *v2)
route('/CAN_L', B, v2, d4l)
# FAN_PWM: pin 17 sits between the CAN_RX and SENS_IN lanes, which wall U6 off from the
# west on B.Cu. A via just off the pin, then F.Cu down the gap between C1's pads, west under
# C1 and JP1 (crossing all four lanes), down between JP1 and CAN_L's F.Cu run, and west
# above Q3 to R15/R16
fp = at('U6', '17')
r15, r16 = pad_net('R15', '/FAN_PWM'), pad_net('R16', '/FAN_PWM')
c1r = pcbnew.ToMM([p for p in FP['C1'].Pads() if p.GetNetname() == '/+24V'][0].GetBoundingBox().GetRight()) - O
jp = [p.GetBoundingBox() for p in FP['JP1'].Pads()]
jl, jr = (min(pcbnew.ToMM(r.GetLeft()) for r in jp) - O, max(pcbnew.ToMM(r.GetRight()) for r in jp) - O)
jb = max(pcbnew.ToMM(r.GetBottom()) for r in jp) - O
qt = min(pcbnew.ToMM(p.GetBoundingBox().GetTop()) for p in FP['Q3'].Pads()) - O
vf = (fp[0] - 1.06, fp[1] - 0.35)          # 0.3 mm from C1's 24 V pad above, CAN_RX's lane below
xg, y1, xw, yl = c1r + 0.45, jb + 0.3, jl - 0.55, qt - 0.5
route('/FAN_PWM', B, fp, (fp[0] - 0.71, fp[1]), vf)
via('/FAN_PWM', *vf)
route('/FAN_PWM', F, vf, (xg, vf[1]), (xg, y1 - 0.17), (jr + 0.25, y1 - 0.17), (jr + 0.05, y1), (xw, y1), (xw, yl),
      (r15[0] + 1.6, yl), (r15[0] + 1.45, yl - 0.1), (r15[0], yl - 0.1), r15, r16)
pcbnew.SaveBoard(sys.argv[1], b)
print('TH_ADC, SENS_IN, CAN_TX/RX, the U3 CAN_H/CAN_L escape, U3 +3V3 and FAN_PWM pre-routed')
