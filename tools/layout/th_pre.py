"""th_pre.py board.kicad_pcb th|pwm - pre-route TH_ADC from U6 pin 14 to R19/C19 (th), or HEAT_PWM (pwm).
U6's ADC pins face left, but the thermistor filter sits below the crystal and Q2, which wall
it off on top (Q2, HEAT_N) and bottom (crystal cluster).  TH_ADC stays on B.Cu: out of the
pin above SENS_IN's escape, down the lane between J2's heater pins and C15/C14 (needs C15 at
corner_pre's shifted spot for the 0.3 mm 24 V clearance to J2), then along y 29.37 under the
crystal to R19.
Also pre-routes HEAT_PWM from U6 pin 48's escape via to R13 and R14 on F.Cu, which the
autorouters kept leaving open.
'th' runs before sig_fanout (SENS_IN's escape then keeps clear of the lane); 'pwm' after it
(needs the pin 48 via); both before planes_fanout (GND vias move round them).
"""
import sys, pcbnew
mm = pcbnew.FromMM
b = pcbnew.LoadBoard(sys.argv[1]); O = 100.0
F, B = pcbnew.F_Cu, pcbnew.B_Cu
P = lambda x, y: pcbnew.VECTOR2I(mm(O + x), mm(O + y))
net = b.FindNet('/TH_ADC')
p14 = [p for p in b.FindFootprintByReference('U6').Pads() if p.GetNumber() == '14'][0].GetPosition()
x0, y0 = pcbnew.ToMM(p14.x) - O, pcbnew.ToMM(p14.y) - O


def tr(layer, *pts):
    for a, c in zip(pts, pts[1:]):
        t = pcbnew.PCB_TRACK(b); t.SetStart(P(*a)); t.SetEnd(P(*c)); t.SetWidth(mm(0.2))
        t.SetLayer(layer); t.SetNet(net); t.SetLocked(True); b.Add(t)


r19 = [p for p in b.FindFootprintByReference('R19').Pads() if p.GetNetname() == '/TH_ADC'][0].GetPosition()
c19 = [p for p in b.FindFootprintByReference('C19').Pads() if p.GetNetname() == '/TH_ADC'][0].GetPosition()
mmx = lambda q: (pcbnew.ToMM(q.x) - O, pcbnew.ToMM(q.y) - O)
rx, ry = mmx(r19)
MODE = sys.argv[2]
# all on B.Cu: out of pin 14 above SENS_IN's stub and via, down the lane, under the crystal
if MODE == 'th':
    tr(B, (x0, y0), (12.25, y0), (11.9, y0 + 0.35), (11.9, 29.0), (12.27, 29.37), (rx - 0.6, 29.37), (rx, 29.97), (rx, ry), mmx(c19))
if MODE == 'th':
    pcbnew.SaveBoard(sys.argv[1], b)
    print('TH_ADC pre-routed from pin 14 at %.2f %.2f' % (x0, y0))
    sys.exit()
hv = [t for t in b.GetTracks() if t.GetClass() == 'PCB_VIA' and t.GetNetname() == '/HEAT_PWM']
assert len(hv) == 1, 'expected one HEAT_PWM escape via'
hx, hy = mmx(hv[0].GetPosition())
r13 = mmx([p for p in b.FindFootprintByReference('R13').Pads() if p.GetNetname() == '/HEAT_PWM'][0].GetPosition())
r14 = mmx([p for p in b.FindFootprintByReference('R14').Pads() if p.GetNetname() == '/HEAT_PWM'][0].GetPosition())
net = b.FindNet('/HEAT_PWM')
# R13/R14 stand upright with their HEAT_PWM pads in a row: across from the via to R14, on to R13
tr(F, (hx, hy), (hx - abs(hy - r14[1]), r14[1]), r14, r13)
pcbnew.SaveBoard(sys.argv[1], b)
print('HEAT_PWM pre-routed from via at %.2f %.2f' % (hx, hy))
