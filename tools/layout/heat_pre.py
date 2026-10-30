"""heat_pre.py board.kicad_pcb - pre-route HEAT_PWM from its escape via (sig_fanout, U6 pin 48)
to the heater FET's gate network, on F.Cu: east under SW1, below the +24V via, then down
the right-hand edge, past C8/C2, to R13 (series) and R14 (pull-down), both entered from
the east since R13's gate pad and R14's GND pad face each other between them.
The buck and C8/C2 fill this side, and the router otherwise boxes it in. R14's GND pad
then ties across to Q2's source.
NRST, from SW1 (RESET) on the far side of that run, is pre-routed here too.
Runs after sig_fanout.py and corner_pre.py, before planes_fanout.py.
"""
import sys

import pcbnew

mm, T = pcbnew.FromMM, pcbnew.ToMM
b = pcbnew.LoadBoard(sys.argv[1])
O = 100.0
FP = {f.GetReference(): f for f in b.GetFootprints()}


def pad(ref, net):
    q = [p for p in FP[ref].Pads() if p.GetNetname() == net][0].GetPosition()
    return T(q.x) - O, T(q.y) - O


v = [t for t in b.GetTracks() if t.GetClass() == 'PCB_VIA' and t.GetNetname() == '/HEAT_PWM'][0].GetPosition()
v = (T(v.x) - O, T(v.y) - O)
r13, r14 = pad('R13', '/HEAT_PWM'), pad('R14', '/HEAT_PWM')
xr = max(T(p.GetBoundingBox().GetRight()) for p in FP['R13'].Pads()) - O + 0.43
pts = [v, (xr, v[1]), (xr, r14[1]), r14]
for a, c in list(zip(pts, pts[1:])) + [((xr, r13[1]), r13)]:
    t = pcbnew.PCB_TRACK(b)
    t.SetStart(pcbnew.VECTOR2I(mm(O + a[0]), mm(O + a[1])))
    t.SetEnd(pcbnew.VECTOR2I(mm(O + c[0]), mm(O + c[1])))
    t.SetWidth(mm(0.2))
    t.SetLayer(pcbnew.F_Cu)
    t.SetNet(b.FindNet('/HEAT_PWM'))
    t.SetLocked(True)
    b.Add(t)
# R14's GND pad is now closed in on the east, and L1 fills the bottom side under it: tie it
# across to Q2's source (pin 1, GND) instead of giving it a plane via of its own
g, q = pad('R14', '/GND'), [p for p in FP['Q2'].Pads() if p.GetNumber() == '1'][0].GetPosition()
t = pcbnew.PCB_TRACK(b)
t.SetStart(pcbnew.VECTOR2I(mm(O + g[0]), mm(O + g[1])))
t.SetEnd(q)
t.SetWidth(mm(0.3))
t.SetLayer(pcbnew.F_Cu)
t.SetNet(b.FindNet('/GND'))
t.SetLocked(True)
b.Add(t)
# and fix Q2 pin 1's own plane via below the pad now, before the fan-out hands that spot to R14
qv = pcbnew.VECTOR2I(q.x, q.y + mm(0.59))
t = pcbnew.PCB_TRACK(b)
t.SetStart(q)
t.SetEnd(qv)
t.SetWidth(mm(0.3))
t.SetLayer(pcbnew.F_Cu)
t.SetNet(b.FindNet('/GND'))
t.SetLocked(True)
b.Add(t)
v = pcbnew.PCB_VIA(b)
v.SetPosition(qv)
v.SetWidth(mm(0.6))
v.SetDrill(mm(0.3))
v.SetNet(b.FindNet('/GND'))
v.SetLocked(True)
b.Add(v)
# NRST: the HEAT_PWM run closes SW1 (RESET) in from the south, so NRST goes down SW1's
# east side outside it, crosses under it on B.Cu, and runs west on F.Cu through the gap
# between C8 and C2 to a via onto corner_pre's NRST track at C15
sw = [p for p in FP['SW1'].Pads() if p.GetNetname() == '/NRST'][0]
swb = sw.GetBoundingBox()
s0 = (T(swb.GetRight()) - O - 0.03, T(swb.GetBottom()) - O - 0.25)
F_PTS = [s0, (29.0, 23.5)]
F2_PTS = [(27.7, 24.15), (27.55, 23.9), (27.2, 23.1), (27.0, 22.9), (26.55, 22.65), (25.65, 22.6), (24.35, 20.8),
          (24.35, 20.5), (24.15, 20.15), (23.4, 19.85), (22.45, 19.85), (20.55, 19.25), (20.3, 19.3), (17.85, 19.35),
          (14.3, 18.75), (14.05, 18.75)]


def run(layer, pts, w=0.2, net='/NRST'):
    for a, c in zip(pts, pts[1:]):
        t = pcbnew.PCB_TRACK(b)
        t.SetStart(pcbnew.VECTOR2I(mm(O + a[0]), mm(O + a[1])))
        t.SetEnd(pcbnew.VECTOR2I(mm(O + c[0]), mm(O + c[1])))
        t.SetWidth(mm(w))
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


run(pcbnew.F_Cu, F_PTS)
via('/NRST', 29.0, 23.5)
run(pcbnew.B_Cu, [(29.0, 23.5), (27.7, 24.15)])
via('/NRST', 27.7, 24.15)
run(pcbnew.F_Cu, F2_PTS)
via('/NRST', 14.05, 18.75)
pcbnew.SaveBoard(sys.argv[1], b)
print('HEAT_PWM pre-routed')
