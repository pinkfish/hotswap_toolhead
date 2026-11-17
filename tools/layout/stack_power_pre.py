"""stack_power_pre.py board.kicad_pcb - the power board's share of the heater's 4.2 A path, laid
before routing (pours.py), all on the top side:
  +24V:   a strip from the link header J7's +24V pins (1, 2) down its outer side, then across to
          the heater plug J3's +24V pins (3, 4)
  HEAT_N: J3's HEAT_N pins (1, 2) up to Q2's drain pad
  GND:    Q2's source pins joined, with two via rows beyond them to the In1 plane; J7's GND pins are
          through-hole, so the plane carries the return to them
"""
import sys

import pcbnew

from pours import CLR, box, pads, pour, span, vias

b = pcbnew.LoadBoard(sys.argv[1])
F = pcbnew.F_Cu
j7 = {n: box(pads(b, 'J7', n)[0]) for n in (1, 2, 3, 4)}
j3 = {n: box(pads(b, 'J3', n)[0]) for n in (1, 2, 3, 4)}
drain = box(pads(b, 'Q2', 5)[0])
src = span(*[box(p) for n in (1, 2, 3) for p in pads(b, 'Q2', n)])

# +24V: down beside J7's GND pins (clear of them), then across above J3 to its +24V pins
x0 = max(j7[3][2], j7[4][2]) + CLR
v = span(j7[1], j7[2])
y1 = j3[3][1] + 0.5
pour(b, '/+24V', F, [[x0, v[1], v[2], y1], [j3[3][0], y1 - 2.0, v[2], y1], span(j3[3], j3[4])])

# HEAT_N: J3 pins 1-2 up to Q2's drain
h = span(j3[1], j3[2])
pour(b, '/HEAT_N', F, [h, drain, [max(h[0], drain[0]), drain[1], min(h[2], drain[2]), h[1] + 0.5]])

# GND: Q2's source pins (not the gate, pin 4), and two via rows on the far side from the drain
up = (src[1] + src[3]) / 2 < (drain[1] + drain[3]) / 2
yv, yw = (src[1] - 1.0, src[1] - 1.95) if up else (src[3] + 1.0, src[3] + 1.95)
g = [src[0] - 0.6, min(yw, yv) - 0.45, src[2] + 0.6, max(yw, yv) + 0.45]
pour(b, '/GND', F, [src, g, [src[0], g[1], src[2], src[3]] if up else [src[0], src[1], src[2], g[3]]])
ng = vias(b, '/GND', [g[0] + 0.3, min(yv, yw), g[2] - 0.3, max(yv, yw)], pitch=0.9)

pcbnew.ZONE_FILLER(b).Fill(b.Zones())
pcbnew.SaveBoard(sys.argv[1], b)
print('power board path poured: +24V, HEAT_N, GND (%d vias)' % ng)
