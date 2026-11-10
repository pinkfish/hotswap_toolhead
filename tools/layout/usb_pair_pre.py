"""USB board: pre-route the USB pair from J5 through U5 to U6, locked.
    usb_pair_pre.py board.kicad_pcb
J5's pad row (top) is right over U6's USB pins (bottom), and the two connectors' pin orders
cross: on J5 D+ drops to the bottom left of D-, but U6's D+ (pin 34) is right of D- (pin 33).
  - J5: D+ (B6, A6) strapped above the pad row to a via in U5 pin 3, D- (A7, B7) strapped
    below it on F.Cu and up past B7 to a via in U5 pin 1. U5 passes each line through
    (pins 3/4 and 1/6 joined on B.Cu)
  - D- straight down from U5 pin 1 to U6 pin 33 on B.Cu
  - D+ from its via over D-'s via on In2 to a via right of U5, then down to U6 pin 34 on B.Cu
  - a GND via in U5 pin 2, which the pair boxes in
  - J5's right VBUS pad (A4/B9) and CC1 (A5), boxed in by U6's pins below and the pair's vias
    above: both out along under the pad row on F.Cu, VBUS to a via right of J5's shell leg and
    on to C17 on B.Cu, CC1 below it to a via further right (the router takes it on to R20).
    That leaves the gap at U6's corner, between pin 36 and the VBUS via, for SWCLK, and the
    strip right of J5 for the LEDs
The coordinates are for plan_usb.py's placement on a 22 mm wide board (J5 and U5 on the board's
centre line, U6 at 11.0, 12.2, 90, C17 6.6 mm right of it, its VBUS pad clear of the CC1 via), moved sideways with the
centre line for the board's width (BW); the script stops if the pads aren't where it expects them.
"""
import os
import sys

import pcbnew

O = 100.0
DX = float(os.environ.get('BW', '22')) / 2 - 11.0   # from the 22 mm board's centre line
mm = pcbnew.FromMM
W = 0.25
EXPECT = {('J5', 'A4'): (13.45, 7.695), ('J5', 'A5'): (12.25, 7.695), ('C17', '1'): (17.6, 7.95), ('J5', 'B6'): (10.25, 7.695), ('J5', 'A6'): (11.25, 7.695), ('J5', 'A7'): (10.75, 7.695),
          ('J5', 'B7'): (11.75, 7.695), ('U5', '1'): (11.95, 6.2875), ('U5', '3'): (10.05, 6.2875),
          ('U6', '33'): (12.25, 8.7625), ('U6', '34'): (12.75, 8.7625)}
P, N = '/USB_D_P', '/USB_D_N'
TRACKS = [
    # D+ strap above J5's pad row, B6 to A6, and its via in U5 pin 3
    (P, 'F.Cu', [(10.25, 6.995), (10.25, 6.795), (10.5, 6.595), (11.0, 6.595), (11.25, 6.845), (11.25, 6.995)]),
    (P, 'F.Cu', [(10.15, 6.487), (10.3, 6.637)]),
    # D- strap below it, A7 to B7, and up past B7 to its via in U5 pin 1
    (N, 'F.Cu', [(10.75, 8.395), (10.75, 8.595), (11.0, 8.795), (11.5, 8.795), (11.75, 8.545), (11.75, 8.395)]),
    (N, 'F.Cu', [(11.75, 6.987), (11.8, 6.637), (11.85, 6.487)]),
    # U5's pass-through pins
    (P, 'B.Cu', [(10.25, 4.662), (10.25, 5.662)]),
    (N, 'B.Cu', [(11.95, 4.662), (11.95, 5.662)]),
    # D- down to U6 pin 33
    (N, 'B.Cu', [(11.95, 6.29), (11.95, 7.3), (12.25, 7.6), (12.25, 8.6)]),
    # D+ over D-'s via on In2, then down to U6 pin 34
    (P, 'In2.Cu', [(10.15, 6.487), (10.15, 5.2), (12.95, 5.2), (12.95, 6.2)]),
    (P, 'B.Cu', [(12.95, 6.2), (12.95, 7.9), (12.75, 8.1), (12.75, 8.6)]),
    # J5's right VBUS pad to C17
    ('/VBUS', 'F.Cu', [(13.45, 8.3), (13.45, 8.8), (16.2, 8.8), (16.5, 8.5)]),
    ('/VBUS', 'B.Cu', [(16.5, 8.5), (17.05, 7.95), (17.6, 7.95)]),
    # CC1 under it, to a via below and right of VBUS's
    ('/USB_CC1', 'F.Cu', [(12.25, 8.3), (12.25, 9.0), (12.55, 9.3), (16.9, 9.3)]),
]
VIAS = [(P, 10.15, 6.487, 0.6, 0.3), (N, 11.85, 6.487, 0.6, 0.3), (P, 12.95, 6.2, 0.6, 0.3),
        # U5's GND pin, boxed in by the pair: a via in its pad, clear of the D+ strap above it
        # (F.Cu) and D+'s In2 run below it
        ('/GND', 11.0, 5.9, 0.6, 0.3), ('/VBUS', 16.5, 8.5, 0.6, 0.3),
        ('/USB_CC1', 16.9, 9.3, 0.6, 0.3)]

b = pcbnew.LoadBoard(sys.argv[1])
for (ref, num), (x, y) in EXPECT.items():
    p = [q for q in b.FindFootprintByReference(ref).Pads() if q.GetNumber() == num][0]
    px, py = pcbnew.ToMM(p.GetPosition().x) - O - DX, pcbnew.ToMM(p.GetPosition().y) - O
    if abs(px - x) > 0.01 or abs(py - y) > 0.01:
        sys.exit('%s.%s is at (%.3f, %.3f), not (%.3f, %.3f): placement changed' % (ref, num, px + DX, py, x + DX, y))
# look the nets up before deleting anything: pcbnew's SWIG types break after a removal
nets = {n: b.FindNet(n) for n in (P, N, '/GND', '/VBUS', '/USB_CC1')}
for t in list(b.GetTracks()):
    if t.GetNetname() in (P, N):
        b.Delete(t)
layers = {b.GetLayerName(l): l for l in b.GetEnabledLayers().CuStack()}
n = 0
for net, layer, pts in TRACKS:
    for (x0, y0), (x1, y1) in zip(pts, pts[1:]):
        w = {'/VBUS': 0.3, '/USB_CC1': 0.2}.get(net, W)
        t = pcbnew.PCB_TRACK(b)
        t.SetStart(pcbnew.VECTOR2I(mm(x0 + O + DX), mm(y0 + O)))
        t.SetEnd(pcbnew.VECTOR2I(mm(x1 + O + DX), mm(y1 + O)))
        t.SetWidth(mm(w))
        t.SetLayer(layers[layer])
        t.SetNet(nets[net])
        t.SetLocked(True)
        b.Add(t)
        n += 1
for net, x, y, dia, drill in VIAS:
    v = pcbnew.PCB_VIA(b)
    v.SetPosition(pcbnew.VECTOR2I(mm(x + O + DX), mm(y + O)))
    v.SetWidth(mm(dia))
    v.SetDrill(mm(drill))
    v.SetNet(nets[net])
    v.SetLocked(True)
    b.Add(v)
pcbnew.SaveBoard(sys.argv[1], b)
print('USB pair pre-routed: %d tracks, %d vias' % (n, len(VIAS)))
