"""narrow_pre.py board.kicad_pcb - pre-routes for the 27 mm board (run_narrow.sh).
FAN_P: F2's output reaches the fan clamp D5, under J2, round the right-hand end of J2's pin rows: down
from F2 pad 2 on F.Cu to a via right of J2 pin 1, then on B.Cu down the lane between J2's pins
and L1 and across to D5 pad 1. The 31 mm board's via was where Q2 now is; between J2's pins
there's no room (0.8 mm gaps), and the HEAT_N pour takes the lane on top.
D7's +24V via: up-left of its pad as on the 31 mm board (BUCK_FB runs between D7's pads, and
U6 pin 48's escape takes the room below), replacing the block copper's.
LED_STAT: from U6 pin 44 up to a via above D7's, then on F.Cu down its left to R6.
HEAT_PWM, NRST: kept from crossing east of U6 (U7 is below that, SW1 above); NRST above C8.
VREFP: out of its decoupling to the right and back left on F.Cu between C8 and F2.
LED1_A, LED2_A: R6 left, R5 right, so the anodes go up the right of the LEDs without crossing;
R5's +3V3 up the right of LED1's lane to a via above LED1, then on B.Cu to R2.
F2's +24V: a plane via below pad 1, between Y1 and J2's pins.
FAN_PWM: round the CAN pair to R15, along the strip below J1 (CAN_L drops to B.Cu above it).
CAN_L: D4 to U3's pin 6 down U3's left.
"""
import sys

import pcbnew

mm = pcbnew.FromMM
b = pcbnew.LoadBoard(sys.argv[1])
O = 100.0
FP = {f.GetReference(): f for f in b.GetFootprints()}
F, B = pcbnew.F_Cu, pcbnew.B_Cu
W = 0.4
G = pcbnew.PCB_GROUP(b)          # declash.py keeps these over the block copper they clash with
G.SetName('narrow pre-routes')
b.Add(G)


def at(ref, num):
    q = [p for p in FP[ref].Pads() if p.GetNumber() == num][0].GetPosition()
    return pcbnew.ToMM(q.x) - O, pcbnew.ToMM(q.y) - O


def route(layer, *pts, net='/FAN_P', w=W):
    for a, c in zip(pts, pts[1:]):
        t = pcbnew.PCB_TRACK(b)
        t.SetStart(pcbnew.VECTOR2I(mm(O + a[0]), mm(O + a[1])))
        t.SetEnd(pcbnew.VECTOR2I(mm(O + c[0]), mm(O + c[1])))
        t.SetWidth(mm(w))
        t.SetLayer(layer)
        t.SetNet(b.FindNet(net))
        t.SetLocked(True)
        b.Add(t)
        G.AddItem(t)


def via(net, xy, d=0.6, drill=0.3):
    v = pcbnew.PCB_VIA(b)
    v.SetPosition(pcbnew.VECTOR2I(mm(O + xy[0]), mm(O + xy[1])))
    v.SetWidth(mm(d))
    v.SetDrill(mm(drill))
    v.SetNet(b.FindNet(net))
    v.SetLocked(True)
    b.Add(v)
    G.AddItem(v)


f2, p1, p5, d5 = at('F2', '2'), at('J2', '1'), at('J2', '5'), at('D5', '1')
x = p1[0] + 1.6                  # 0.75 mm clear of J2 pins 1/5 (HV clearance 0.32)
v = (x, p1[1] - 1.3)             # below F2, clear of J2 pin 1
bend = (x, p5[1] + 1.9)          # below the second pin row
route(F, f2, (f2[0], v[1] - (x - f2[0])), v)
via('/FAN_P', v)
route(B, v, bend, (bend[0] - (d5[1] - bend[1]), d5[1]), d5)

d7 = at('D7', '2')
near = pcbnew.VECTOR2I(mm(O + d7[0]), mm(O + d7[1]))
for t in list(b.GetTracks()):
    if t.GetNetname() == '/+24V' and min((p - near).EuclideanNorm() for p in (
            [t.GetPosition()] if t.GetClass() == 'PCB_VIA' else [t.GetStart(), t.GetEnd()])) < mm(1.5):
        b.Remove(t)
v24 = (d7[0] - 0.74, d7[1] - 0.74)
route(B, d7, v24, net='/+24V', w=0.8)
via('/+24V', v24, 0.8, 0.4)

p44, r6 = at('U6', '44'), at('R6', '1')
vl = (p44[0] + 1.34, p44[1] - 1.1)
route(B, p44, (p44[0] + 0.6, p44[1]), (vl[0], p44[1] - 0.74), vl, net='/LED_STAT', w=0.2)
via('/LED_STAT', vl)
xs = vl[0] - 0.63                # down the left of D7's +24V via
route(F, vl, (xs, vl[1] + 0.63), (xs, r6[1] - (r6[0] - xs)), r6, net='/LED_STAT', w=0.2)

# the LED anodes up the right of the LEDs, LED2's inside LED1's: R6 under LED2's lane, R5 under LED1's
r6b, l2, r5, l1 = at('R6', '2'), at('LED2', '2'), at('R5', '2'), at('LED1', '2')
x2 = l2[0] + 0.16                # clear of the GND via right of D7's
route(F, r6b, (r6b[0], r6b[1] - 0.45), (x2, r6b[1] - 0.45 - (x2 - r6b[0])), (x2, l2[1]), net='/LED2_A', w=0.2)
x1 = l1[0] + 0.76                # between LED2 and SW1's pads and peg, room for +3V3 on its right
route(F, r5, (r5[0], r5[1] - 0.2), (x1, r5[1] - 0.2 - (x1 - r5[0])), (x1, l1[1] + (x1 - l1[0])), l1,
      net='/LED1_A', w=0.2)
# R5's +3V3 up the strip between LED1's lane and SW1's pads, to a via above LED1 and on B.Cu to R2
r5p, r2 = at('R5', '1'), at('R2', '1')
sw_l = min(pcbnew.ToMM(p.GetBoundingBox().GetLeft()) - O for p in FP['SW1'].Pads())
x3 = (x1 + 0.1 + sw_l) / 2       # midway between LED1's lane and SW1's pads
v3 = (x1 + 0.05, l1[1] - 0.7)
route(F, r5p, (x3, r5p[1] - (x3 - r5p[0])), (x3, v3[1] + (x3 - v3[0])), v3, net='/+3V3', w=0.2)
via('/+3V3', v3)
route(B, v3, r2, net='/+3V3', w=0.25)

# F2's +24V plane via below its pad 1, right of the 31 mm board's (now on J2 pin 3 and Y1's GND via)
f2a = at('F2', '1')
vf = (f2a[0] + 0.34, f2a[1] + 2.0)
route(F, f2a, (f2a[0], vf[1] - 0.34), vf, net='/+24V', w=0.8)
via('/+24V', vf, 0.8, 0.4)

# HEAT_PWM and NRST, which would cross east of U6: HEAT_PWM from pin 48 on B.Cu to a via below R6,
# clear of D7 and U1, then on F.Cu down to U7; NRST above C8 and under the LED resistors to SW1
for t in list(b.GetTracks()):
    if t.GetNetname() == '/HEAT_PWM':
        b.Remove(t)
p48, u7 = at('U6', '48'), at('U7', '3')
vh = (p48[0] + 1.36, p48[1] + 0.85)
route(B, p48, (vh[0] - 0.85, p48[1]), vh, net='/HEAT_PWM', w=0.2)
via('/HEAT_PWM', vh)
route(F, vh, (u7[0], vh[1] + (u7[0] - vh[0])), u7, net='/HEAT_PWM', w=0.2)
r14 = at('R14', '1')             # its pull-down, straight across below U7's pin 3
route(F, u7, (u7[0], u7[1] + 0.6), (u7[0] - (r14[1] - u7[1] - 0.6), r14[1]), r14, net='/HEAT_PWM', w=0.2)

# The strip on F.Cu between C8 and F2 is VREFP's only way out of its decoupling (boxed in on B.Cu
# by C9, the crystal and U6's pins), so it isn't NRST's: the block's NRST run along it goes, and
# NRST runs above C8 instead, between it and U6's thermal vias, from a via left of pin 10's B.Cu
# run to C15, then down past C8's GND pad (clear of LED_STAT) and under the LED resistors to SW1.
# U6's +3V3 vias to C8's pad 1 move up 0.1 mm, to leave VREFP the strip under them.
c81, c82, p4, p6, p10 = at('C8', '1'), at('C8', '2'), at('U6', '4'), at('U6', '6'), at('U6', '10')


def near(t, xy, r):
    q = pcbnew.VECTOR2I(mm(O + xy[0]), mm(O + xy[1]))
    return min((p - q).EuclideanNorm() for p in ([t.GetPosition()] if t.GetClass() == 'PCB_VIA'
                                                  else [t.GetStart(), t.GetEnd()])) < mm(r)


for t in list(b.GetTracks()):
    n, x0 = t.GetNetname(), pcbnew.ToMM(t.GetPosition().x) - O
    if (n == '/NRST' and (t.GetLayer() == F and t.GetClass() == 'PCB_TRACK' or t.GetClass() == 'PCB_VIA')
            or n == '/+3V3' and t.GetLayer() != B and (near(t, c81, 1.2) or t.GetClass() == 'PCB_VIA'
                                                       and near(t, (p4[0], p4[1] + 1.1), 1.3))):
        b.Remove(t)
va, vb = (p6[0] - 0.15, p6[1] + 1.06), (p4[0] + 0.2, p4[1] + 1.01)   # on U6 pin 6's and 4's B.Cu stubs
via('/+3V3', va)
via('/+3V3', vb)
route(F, vb, (c81[0], vb[1]), net='/+3V3', w=0.25)
sw = max(((pcbnew.ToMM(p.GetPosition().x) - O, pcbnew.ToMM(p.GetPosition().y) - O)
          for p in FP['SW1'].Pads() if p.GetNumber() == '1'), key=lambda q: q[1])   # the lower one
nv = (p10[0] - 1.65, p10[1] + 0.49)
yt, xd, yn = c81[1] - 1.4, c82[0] + 0.97, r6[1] + 0.63
via('/NRST', nv)
route(B, nv, (nv[0], p10[1] + 0.75), net='/NRST', w=0.2)
route(F, nv, (c81[0] - 1.13, nv[1]), (c81[0] - 1.13, yt), (xd, yt), (xd, yn), (sw[0] - 0.28, yn),
      (sw[0] - 0.28, sw[1]), net='/NRST', w=0.2)
fb = at('FB1', '2')
vr = (fb[0] + 1.04, fb[1] - 1.0)  # above C6, right of C8's GND pad
yr = vr[1] + 0.75                 # 0.35 mm above F2
via('/VREFP', vr)
route(B, fb, vr, net='/VREFP', w=0.2)
route(F, vr, (vr[0], vr[1] + 0.3), (vr[0] - 0.45, yr), (at('F2', '1')[0] - 0.3, yr), net='/VREFP', w=0.2)
via('/GND', (c82[0] + 0.42, c82[1] + 0.2))   # C8's GND pad and the pour between NRST and VREFP
# FB1's +3V3 to the buck output: boxed in on B.Cu too, so F.Cu down the left of R14 and under it
# (clear of R14's HEAT_PWM link) to a via above L1, then B.Cu to L1's pad 2
fb1, l12 = at('FB1', '1'), at('L1', '2')
v1, v2 = (fb1[0] + 0.29, fb1[1] + 0.04), (l12[0] - 2.05, l12[1] - 2.4)
via('/+3V3', v1)
via('/+3V3', v2)
route(B, fb1, v1, net='/+3V3', w=0.25)
route(F, v1, (v1[0] + 0.35, v1[1] + 0.35), (v1[0] + 0.35, v2[1] - 1.5), v2, net='/+3V3', w=0.25)
route(B, v2, (v2[0] + 0.2, v2[1] + 0.2), (l12[0], v2[1] + 0.2), l12, net='/+3V3', w=0.25)

# FAN_PWM to R15 on the left edge has to cross the CAN pair coming down from J1: from U6 pin 17
# on B.Cu to a via left of C1, then on F.Cu up and along the strip below J1 to R15. CAN_L drops
# to B.Cu at the end of its F.Cu run from J1, above the strip, so the two don't cross on F.Cu.
p17, r15 = at('U6', '17'), at('R15', '1')
vp = (p17[0] - 2.46, p17[1])     # left of C1
yb = 11.2                        # below J1, above R11
route(B, p17, vp, net='/FAN_PWM', w=0.2)
via('/FAN_PWM', vp)
route(F, vp, (vp[0], yb), (r15[0] + 0.4, yb), (r15[0], yb + 0.4), r15, net='/FAN_PWM', w=0.2)
cl = max((t.GetEnd() if t.GetEnd().y > t.GetStart().y else t.GetStart() for t in b.GetTracks()
          if t.GetNetname() == '/CAN_L' and t.GetLayer() == F and t.GetClass() == 'PCB_TRACK'
          and pcbnew.ToMM(min(t.GetStart().x, t.GetEnd().x)) - O < 4), key=lambda q: q.y)
via('/CAN_L', (pcbnew.ToMM(cl.x) - O, pcbnew.ToMM(cl.y) - O))
# CAN_L from D4 down the left of U3 to its pin 6 (the routers left it boxed in by CAN_H and the fan)
u36, d42 = at('U3', '6'), at('D4', '2')
route(B, u36, (u36[0] - 0.76, u36[1]), (u36[0] - 1.2, u36[1] - 0.44), (u36[0] - 1.2, u36[1] - 2.3),
      (u36[0] - 0.95, u36[1] - 2.5), (d42[0] - 0.25, u36[1] - 2.8), d42, net='/CAN_L', w=0.2)
pcbnew.SaveBoard(sys.argv[1], b)
print('FAN_P via', [round(c, 2) for c in v], 'D7 +24V via', [round(c, 2) for c in v24],
      'LED_STAT via', [round(c, 2) for c in vl])
