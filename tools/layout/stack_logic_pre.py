"""stack_logic_pre.py board.kicad_pcb - the logic board's share of the heater's 4.2 A path, laid
before routing (pours.py):
  VIN_RAW: top pour from J1's +24V pins (1, 2) down to F1's input pad
  +24V:    top pour from F1's output pad, with D1's and F2's +24V pads, over a via array to a
           bottom pour on the link socket J6's +24V pins (1, 2) and C1's +24V pad
  GND:     a bottom pour on J6's GND pins (3, 4, 6) with vias to the In1 plane, which takes the
           return to J1's GND pins (3, 4) and their fan-out vias
"""
import sys

import pcbnew

from pours import CLR, box, pads, pour, span, vias

b = pcbnew.LoadBoard(sys.argv[1])
F, B = pcbnew.F_Cu, pcbnew.B_Cu
j1 = {n: box(pads(b, 'J1', n)[0]) for n in (1, 2)}
j6 = {n: box(pads(b, 'J6', n)[0]) for n in range(1, 9)}
f1 = {n: box(pads(b, 'F1', n)[0]) for n in (1, 2)}
d1v, c1v, f2v = (box(pads(b, ref, 1)[0]) for ref in ('D1', 'C1', 'F2'))

# VIN_RAW: J1 pins 1-2, then down J1 pin 2's column to F1 pad 1
a = span(j1[1], j1[2])
pour(b, '/VIN_RAW', F, [a, span([f1[1][0], a[3] - 0.5, a[0] + 1.3, a[3]], f1[1])])

# +24V on top: a field right of J1 pin 1 and over F1 pad 2, down to D1 pad 1 and F2 pad 1
xr = max(f2v[2], f1[2][2] + 2.5)
field = [j1[1][2] + CLR, j1[1][3] - 1.3, xr, f1[2][3]]
pour(b, '/+24V', F, [field, [f1[2][0], f1[2][1], xr, f1[2][3]], f1[2], f2v,
                    [f2v[0], f1[2][3] - 0.2, f2v[2], f2v[3]],
                    [d1v[0], f1[2][3] - 0.2, d1v[2], d1v[3]], d1v])
# ... and underneath, from J6 pins 1-2 down to the same field and C1 pad 1
bot = [j6[1][0] - 0.4, j6[1][1] - 0.2, xr, f1[2][3]]
pour(b, '/+24V', B, [bot, j6[1], j6[2], c1v, [c1v[0], f1[2][3] - 0.2, c1v[2], c1v[3]]])
nv = vias(b, '/+24V', [field[0] + 0.3, field[1] + 0.3, xr - 0.3, field[3] - 0.3], pitch=0.95)

# GND underneath: J6 pins 3 and 4 (one column) and 6, between and below the pad rows
g = [j6[6][0] - 0.3, j6[6][1] - 0.2, j6[3][2] + 0.3, j6[4][3] + 1.2]
pour(b, '/GND', B, [span(j6[3], j6[4]), g, [j6[3][0] - 0.3, j6[3][1] - 0.2, j6[3][2] + 0.3, g[3]]])
ng = vias(b, '/GND', [j6[6][0], j6[3][3] + 0.3, j6[3][2], g[3] - 0.3], pitch=0.95)

pcbnew.ZONE_FILLER(b).Fill(b.Zones())
pcbnew.SaveBoard(sys.argv[1], b)
print('logic power path poured: VIN_RAW, +24V (top, bottom, %d vias), GND (bottom, %d vias)' % (nv, ng))
