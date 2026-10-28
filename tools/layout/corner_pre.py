"""Hand layout of the U6 pin 4-10 corner (crystal, load caps, decoupling, VREF), before routing.
    corner_pre.py board.kicad_pcb
Same cluster as rev A's routed board, shifted with U6: parts placed with pad 1 up/down,
+3V3 pins 4 and 6 dropped to staggered vias so VREFP (pin 5) runs straight down between
them, and GND pin 7 tied into the exposed pad.
"""
import sys

import pcbnew

mm = pcbnew.FromMM
b = pcbnew.LoadBoard(sys.argv[1])
OX = OY = 100.0
FP = {f.GetReference(): f for f in b.GetFootprints()}
u6 = FP['U6']
DX = pcbnew.ToMM(u6.GetPosition().x) - OX - 16.3
DY = pcbnew.ToMM(u6.GetPosition().y) - OY - 23.6
PLACE = {
    'Y1': (14.0, 30.4, 270),
    'C9': (16.4, 29.43, 'up'),
    'C11': (17.42, 29.48, 'up'),
    'C12': (18.44, 29.48, 'up'),
    'FB1': (19.46, 29.48, 'down'),     # pad 2 (VREFP) on top, in line with C11/C12
    'C13': (16.4, 31.8, 'up'),
    'C10': (18.9, 32.85, 0),
    'C14': (11.6, 31.4, 'down'),       # GND pad up, so it can tie to C15's (TH_ADC boxes it in below)
    'C15': (11.45, 28.6, 'up'),        # 0.3 right of rev A: opens the TH_ADC lane by J2
}
PIN_VIAS = {'6': (16.4, 28.2), '4': (17.75, 28.15)}
KNEE_Y = 27.6


def P(x, y):
    return pcbnew.VECTOR2I(mm(OX + x + DX), mm(OY + y + DY))


def pad(f, n):
    return [p for p in f.Pads() if p.GetNumber() == n][0]


def track(net, a, c, w):
    t = pcbnew.PCB_TRACK(b)
    t.SetStart(a)
    t.SetEnd(c)
    t.SetWidth(mm(w))
    t.SetLayer(pcbnew.B_Cu)
    t.SetNet(net)
    t.SetLocked(True)
    b.Add(t)


for ref, (x, y, rot) in PLACE.items():
    f = FP[ref]
    f.SetPosition(P(x, y))
    if rot in ('up', 'down'):
        best = None
        for a in (0, 90, 180, 270):
            f.SetOrientationDegrees(a)
            key = pad(f, '1').GetPosition().y * (1 if rot == 'up' else -1)
            if best is None or key < best[0]:
                best = (key, a)
        rot = best[1]
    f.SetOrientationDegrees(rot)

p7, ep = pad(u6, '7'), pad(u6, '49')
c7 = p7.GetPosition()
track(p7.GetNet(), c7, pcbnew.VECTOR2I(c7.x, ep.GetBoundingBox().GetBottom() - mm(0.2)), 0.2)
for num, (x, y) in PIN_VIAS.items():
    p = pad(u6, num)
    pos = P(x, y)
    knee = pcbnew.VECTOR2I(p.GetPosition().x, P(0, KNEE_Y).y)
    track(p.GetNet(), p.GetPosition(), knee, 0.25)
    track(p.GetNet(), knee, pos, 0.25)
    v = pcbnew.PCB_VIA(b)
    v.SetPosition(pos)
    v.SetWidth(mm(0.6))
    v.SetDrill(mm(0.3))
    v.SetNet(p.GetNet())
    v.SetLocked(True)
    b.Add(v)
# U6 pins 8-10 (OSC_IN, OSC_OUT, NRST) pre-routed so none boxes another in: NRST hugs the
# pin row out to C15, OSC_OUT runs under it and round the left of Y1's GND pad 4 to pad 3
# and C14, OSC_IN drops straight to Y1 pad 1 and on down the right side to C13.  Pad 4 is
# then enclosed, so it ties diagonally across the crystal to GND pad 2.
y1 = FP['Y1']


def R(*pts, net, w=0.2):
    pts = [pcbnew.VECTOR2I(mm(OX + x), mm(OY + y)) for x, y in pts]
    for a, c in zip(pts, pts[1:]):
        track(b.FindNet(net), a, c, w)


def at(f, n):
    q = pad(f, n).GetPosition()
    return pcbnew.ToMM(q.x) - OX, pcbnew.ToMM(q.y) - OY


def box(f, n):
    r = pad(f, n).GetBoundingBox()
    return [pcbnew.ToMM(v) - o for v, o in ((r.GetX(), OX), (r.GetY(), OY), (r.GetRight(), OX), (r.GetBottom(), OY))]


x8, yp = at(u6, '8')
x9, _ = at(u6, '9')
x10, _ = at(u6, '10')
row = box(u6, '9')[3]                      # pin row bottom edge
c15, c14, c13 = at(FP['C15'], '1'), at(FP['C14'], '1'), at(FP['C13'], '1')
p4 = box(y1, '4')                          # GND pad nearest the pins, left
p1 = box(y1, '1')                          # OSC_IN pad, right
q3 = at(y1, '3')
xl = p4[0] - 0.33
yo = row + 0.72
R((x10, yp), (x10, row + 0.32), (c15[0] + 0.35, row + 0.32), c15, net='/NRST')
R((x9, yp), (x9, yo), (xl, yo), (xl, c14[1]), c14, net='/OSC_OUT')
R((xl, c14[1]), (q3[0] - 0.35, q3[1] - 0.3), net='/OSC_OUT')
xr = p1[2] + 0.3
R((x8, yp), (x8, p1[1] + 0.2), (p1[2] - 0.25, p1[1] + 0.4), net='/OSC_IN')
R((x8, p1[1] + 0.2), (xr, p1[1] + 0.4), (xr, c13[1]), c13, net='/OSC_IN')
R(at(y1, '4'), at(y1, '2'), net='/GND')
# TH_ADC's lane (th_pre) closes off the GND pads under the crystal: tie them to neighbours with vias
R(at(FP['C14'], '2'), at(FP['C15'], '2'), net='/GND')
g = at(FP['C14'], '2'); g = (g[0] - 0.2, g[1] - 0.35)   # that pair is boxed in too: via on C14's pad edge, clear of Q2's drain
gv = pcbnew.PCB_VIA(b)
gv.SetPosition(pcbnew.VECTOR2I(mm(OX + g[0]), mm(OY + g[1])))
gv.SetWidth(mm(0.6))
gv.SetDrill(mm(0.3))
gv.SetNet(b.FindNet('/GND'))
gv.SetLocked(True)
b.Add(gv)
R(at(y1, '2'), at(FP['C13'], '2'), net='/GND')
pcbnew.SaveBoard(sys.argv[1], b)
print('corner placed, shift %.2f %.2f' % (DX, DY))
