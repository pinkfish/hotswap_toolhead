"""left_pre.py board.kicad_pcb - pre-route the left side between H1's keep-out and J2's pins.
H1's 3 mm keep-out, J2's pin rows and the CAN block leave no way across the left of the
board for the router, so:
- +3V3 trunk: a via beside U3 pin 3 / C16, up the F.Cu channel beside JP1, along y 11.2
  under J1 to a via beside R2; a branch along the foot of the keep-out to R22.
- SENS: J2 pin 4 to R23 and R22 (all on top).
- SENS_IN: R23 to C20, then along y 20.6 above J2's pin row to U6 pin 13's escape via.
- FAN_P: J2 pin 2 along the B.Cu strip above the pins to a via at the left edge, so the
  router only has to reach F2 and D5 from there.
- NRST: SW1 down past the USB D+ corner, along y 16.6 under D+, between U6's EP via rows
  at y 19.7, down x 14.6 to a via beside the corner's NRST track.
- SWCLK (right side, which NRST now crosses): U6 pin 36 round D9, down beside L1 and
  along y 18.3 under it to R4 on B.Cu.
Runs after th_pre th and before sig_fanout (which then leaves pin 13 alone).
"""
import sys, pcbnew
mm = pcbnew.FromMM
b = pcbnew.LoadBoard(sys.argv[1]); O = 100.0
F, B = pcbnew.F_Cu, pcbnew.B_Cu
P = lambda x, y: pcbnew.VECTOR2I(mm(O + x), mm(O + y))


def at(ref, num):
    q = [p for p in b.FindFootprintByReference(ref).Pads() if p.GetNumber() == num][0].GetPosition()
    return pcbnew.ToMM(q.x) - O, pcbnew.ToMM(q.y) - O


def tr(net, layer, *pts, w=0.2):
    for a, c in zip(pts, pts[1:]):
        t = pcbnew.PCB_TRACK(b); t.SetStart(P(*a)); t.SetEnd(P(*c)); t.SetWidth(mm(w))
        t.SetLayer(layer); t.SetNet(b.FindNet(net)); t.SetLocked(True); b.Add(t)


def via(net, x, y):
    v = pcbnew.PCB_VIA(b); v.SetPosition(P(x, y)); v.SetWidth(mm(0.6)); v.SetDrill(mm(0.3))
    v.SetNet(b.FindNet(net)); v.SetLocked(True); b.Add(v)


V = '/+3V3'
u3, c16, r2, r22 = at('U3', '3'), at('C16', '1'), at('R2', '1'), at('R22', '1')
ve, vc = (7.55, 16.95), (11.5, r2[1])
for p in (ve, vc):
    via(V, *p)
tr(V, B, c16, ve, (7.6, u3[1]), u3)
tr(V, F, ve, (8.2, 16.3), (8.2, 11.6), (8.6, 11.2), (vc[0], 11.2), vc)
tr(V, B, vc, r2)
tr(V, F, ve, (6.9, 19.32), (1.6, 19.32), r22)   # 0.2 mm under H1's ring
j4, r23s, r23i, r22s, c20 = at('J2', '4'), at('R23', '1'), at('R23', '2'), at('R22', '2'), at('C20', '1')
tr('/SENS', F, j4, (j4[0], 21.05), r23s)
tr('/SENS', F, r22s, r23s)
p13 = at('U6', '13')
vs = (12.56, 23.4)
via('/SENS_IN', *vs)
tr('/SENS_IN', F, r23i, c20, (c20[0], 20.6), (12.3, 20.6), vs)
tr('/SENS_IN', B, p13, vs)
j2 = at('J2', '2')
vf = (1.25, 25.3)
via('/FAN_P', *vf)
tr('/FAN_P', B, j2, (j2[0] - 0.6, 20.45), (vf[0], 20.45), vf, w=0.4)
vn = (13.3, 23.95)
via('/NRST', *vn)
tr('/NRST', B, vn, (vn[0], 24.59))
sw = at('SW1', '1')
tr('/NRST', F, sw, (27.6, 15.9), (27.6, 16.2), (27.2, 16.6), (22.4, 16.6), (21.3, 17.7), (20.4, 19.7),
   (14.6, 19.7), (14.6, 23.25), vn)
p36 = at('U6', '36')
tr('/SWCLK', B, p36, (p36[0], 16.25), (22.7, 16.25), (22.7, 18.3), (27.6, 18.3), at('R4', '2'))
pcbnew.SaveBoard(sys.argv[1], b)
print('left side pre-routed')
