"""can_pre.py board.kicad_pcb - the heater's 4.2 A path as top-layer pours, laid before routing.
  VIN_RAW: J1's +24V pins (1, 2) down to F1's input pad
  +24V:    F1's output pad, a strip straight down to J3's +24V pins (3, 4), with D1's
           +24V pad joined to its side (the bulk caps are underneath; the router joins them)
  HEAT_N:  J3's HEAT_N pins (1, 2) up to Q2's drain pad
  GND:     the return, beside the strip, from J1's GND pins (3, 4) down to D1's GND pad and
           Q2's source pins
Each pour is a union of boxes taken from the pads, so it follows the placement.
The router sees the pours as planes of their nets and may cross them; pour_clear.py takes
other nets' copper back out after routing.
"""
import sys

import pcbnew

mm, T = pcbnew.FromMM, pcbnew.ToMM
b = pcbnew.LoadBoard(sys.argv[1])
FP = {f.GetReference(): f for f in b.GetFootprints()}
CLR = 0.3
STRIP = 2.6


def pads(ref, num):
    return [p for p in FP[ref].Pads() if p.GetNumber() == str(num)]


def box(p, grow=0.0):
    bb = p.GetBoundingBox()
    return [T(bb.GetLeft()) - grow, T(bb.GetTop()) - grow, T(bb.GetRight()) + grow, T(bb.GetBottom()) + grow]


def span(*bs):
    return [min(x[0] for x in bs), min(x[1] for x in bs), max(x[2] for x in bs), max(x[3] for x in bs)]


def poly(rects):
    s = pcbnew.SHAPE_POLY_SET()
    for x0, y0, x1, y1 in rects:
        r = pcbnew.SHAPE_POLY_SET()
        r.NewOutline()
        for x, y in ((x0, y0), (x1, y0), (x1, y1), (x0, y1)):
            r.Append(mm(x), mm(y))
        s.BooleanAdd(r)
    s.Simplify()
    return s


def pour(net, rects):
    z = pcbnew.ZONE(b)
    z.SetLayer(pcbnew.F_Cu)
    z.SetNet(b.FindNet(net))
    z.SetAssignedPriority(3)
    z.SetLocalClearance(mm(CLR))
    z.SetMinThickness(mm(0.25))
    z.SetPadConnection(pcbnew.ZONE_CONNECTION_FULL)
    z.SetIslandRemovalMode(pcbnew.ISLAND_REMOVAL_MODE_ALWAYS)
    z.SetZoneName(net.strip('/') + ' pour')
    s = poly(rects)
    assert s.OutlineCount() == 1, '%s pour is in pieces' % net
    o, ln = z.Outline(), s.Outline(0)
    o.NewOutline()
    for i in range(ln.PointCount()):
        o.Append(ln.CPoint(i).x, ln.CPoint(i).y)
    z.SetLocked(True)
    b.Add(z)


j1 = {n: box(pads('J1', n)[0]) for n in (1, 2, 3, 4)}
j3 = {n: box(pads('J3', n)[0]) for n in (1, 2, 3, 4)}
f1 = {n: box(pads('F1', n)[0]) for n in (1, 2)}
drain = box(pads('Q2', 5)[0])
sw = FP['SW1'].GetCourtyard(pcbnew.F_Cu).BBox()

# VIN_RAW: J1 pins 1-2, then down J1 pin 2's column to F1 pad 1
a = span(j1[1], j1[2])
pour('/VIN_RAW', [a, span([f1[1][0], a[3] - 0.5, a[0] + 1.3, a[3]], f1[1])])

# +24V: the strip, 2.6 mm wide (about 5 A in 1 oz outer copper at a 10 C rise), from F1 pad 2
# down to J3 pin 3, widening over the last 1 mm to take in pin 4. The column between the strip
# and SW1/the LEDs is left for vias
x0 = min(f1[2][0], j3[3][0])
strip = [x0, f1[2][1], x0 + STRIP, j3[3][3]]
foot = [x0, j3[3][1] - 1.0, min(j3[4][2], T(sw.GetLeft()) - 0.35), j3[3][3]]
rects = [strip, foot, j3[3], j3[4], f1[2]]
for ref in ('D1',):
    p = box(pads(ref, 1)[0])
    rects += [p, [p[0], p[1], x0 + 0.5, p[3]]]
pour('/+24V', rects)

# HEAT_N: J3 pins 1-2 up to Q2's drain
h = span(j3[1], j3[2])
pour('/HEAT_N', [h, drain, [max(h[0], drain[0]), drain[1], min(h[2], drain[2]), h[1] + 0.5]])

# GND: the return beside the strip, from J1 pins 3-4 down to D1's GND pad and Q2's source
# pins, all on the top layer (U6 and its crystal corner are underneath: no room for vias).
# Q2's gate (pin 4) ends the source row; the pour only covers pins 1-3, from the far side
# A column down from J1's GND pins takes in D1's GND pad, then a bridge runs right, below the
# link from D1's +24V pad to the strip and above Q2's gate, to the source pins
g = span(j1[3], j1[4])
d1g, d1v = box(pads('D1', 2)[0]), box(pads('D1', 1)[0])
src = span(*[box(p) for n in (1, 2, 3) for p in pads('Q2', n)])
yb = d1v[3] + CLR + 0.05
pour('/GND', [g, [g[0], g[3] - 0.5, g[2], yb + 0.6], [g[2] - 0.5, d1g[1], d1g[2], d1g[3]],
              [g[2] - 0.5, yb, src[0] + 0.5, yb + 0.6], [src[0], yb, src[2], src[3]]])

pcbnew.ZONE_FILLER(b).Fill(b.Zones())
pcbnew.SaveBoard(sys.argv[1], b)
print('power path poured: VIN_RAW, +24V, HEAT_N, GND')
