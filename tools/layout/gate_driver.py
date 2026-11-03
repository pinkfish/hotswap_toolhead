"""gate_driver.py board.kicad_pcb - add the heater gate driver to the routed board (applied once
to the committed board; see README). Run with KiCad's Python.
U7 (UCC27517, SOT-23-5) goes on top between Q2 and the right edge, OUT facing Q2's gate. Its
12 V rail (R13 from VIN_LOGIC, D10, C21) goes underneath, in the strip between L1 and the edge.
R14 (PB9 pull-down) moves up beside C2, and HEAT_PWM runs round U7's outer side to IN+.
The new footprints lose their library silkscreen (it overlaps Q2's and their own pads) and
their reference, value and LCSC fields go on Fab, like the board's other small parts.
"""
import re
import sys

import pcbnew

F, M = pcbnew.FromMM, pcbnew.ToMM
PCB = sys.argv[1]
LIB = '/Applications/KiCad/KiCad.app/Contents/SharedSupport/footprints/'
b = pcbnew.LoadBoard(PCB)
if not b.FindNet('/GATE_12V'):
    b.Add(pcbnew.NETINFO_ITEM(b, '/GATE_12V'))
net = lambda n: b.FindNet('/' + n)
V = lambda x, y: pcbnew.VECTOR2I(F(x), F(y))


def near(p, x, y):
    return abs(M(p.x) - x) < 0.02 and abs(M(p.y) - y) < 0.02


# the old gate network's copper: HEAT_PWM's run down the right edge and its stubs to R13/R14,
# HEAT_G from R13 to Q2's gate, and R14's GND ties to Q2's source
kill = []
for t in b.GetTracks():
    if t.GetClass() == 'PCB_VIA':
        continue
    s, e, n = t.GetStart(), t.GetEnd(), t.GetNetname()
    if n == '/HEAT_PWM' and t.GetLayer() == pcbnew.F_Cu and any(M(p.x) > 127 and M(p.y) > 117 for p in (s, e)):
        kill.append(t)
    elif n == '/HEAT_G' or n == '/GND' and (near(s, 127.6, 127.69) or near(e, 127.6, 127.69)):
        kill.append(t)
for t in kill:
    b.Remove(t)


def track(pts, n, w=0.2, layer=pcbnew.F_Cu):
    for (x1, y1), (x2, y2) in zip(pts, pts[1:]):
        t = pcbnew.PCB_TRACK(b)
        t.SetStart(V(x1, y1)); t.SetEnd(V(x2, y2)); t.SetWidth(F(w)); t.SetLayer(layer); t.SetNet(net(n))
        b.Add(t)


def via(x, y, n):
    v = pcbnew.PCB_VIA(b)
    v.SetPosition(V(x, y)); v.SetWidth(F(0.6)); v.SetDrill(F(0.3)); v.SetNet(net(n))
    b.Add(v)


def place(fp, x, y, rot, bottom, nets):
    if fp.IsFlipped() != bottom:
        fp.Flip(fp.GetPosition(), pcbnew.FLIP_DIRECTION_LEFT_RIGHT)
    fp.SetPosition(V(x, y)); fp.SetOrientationDegrees(rot)
    for p in fp.Pads():
        p.SetNet(net(nets[p.GetNumber()]))


def new(lib, name, ref, value, lcsc, *where):
    fp = pcbnew.FootprintLoad(LIB + lib + '.pretty', name)
    fp.SetFPID(pcbnew.LIB_ID(lib, name)); fp.SetReference(ref); fp.SetValue(value)
    fp.SetField('LCSC', lcsc)
    b.Add(fp)
    place(fp, *where)
    return fp


def pads(fp):
    return {p.GetNumber(): (round(M(p.GetPosition().x), 3), round(M(p.GetPosition().y), 3)) for p in fp.Pads()}


# rotations chosen so the pads land as routed below (bottom parts are mirrored)
U7 = new('Package_TO_SOT_SMD', 'SOT-23-5', 'U7', 'UCC27517DBVR', 'C99395', 128.2, 126.56, 90, False,
         {'1': 'GATE_12V', '2': 'GND', '3': 'HEAT_PWM', '4': 'GND', '5': 'HEAT_G'})
D10 = new('Diode_SMD', 'D_SOD-523', 'D10', 'BZX585-C12 12V', 'C455018', 129.45, 126.05, 180, True,
          {'1': 'GATE_12V', '2': 'GND'})
C21 = new('Capacitor_SMD', 'C_0402_1005Metric', 'C21', '1uF', 'C52923', 129.3, 127.4, 180, True,
          {'1': 'GATE_12V', '2': 'GND'})
R13, R14 = b.FindFootprintByReference('R13'), b.FindFootprintByReference('R14')
place(R13, 130.0, 124.2, -90, True, {'1': 'VIN_LOGIC', '2': 'GATE_12V'})
place(R14, 127.67, 120.5, 90, False, {'1': 'HEAT_PWM', '2': 'GND'})
u, r13, r14, d10, c21 = pads(U7), pads(R13), pads(R14), pads(D10), pads(C21)

# top: OUT straight across to Q2's gate; IN- and GND to a via between OUT and IN-; HEAT_PWM down
# the edge, round U7's outer side to IN+; VDD down to the rail via below GND
y5 = u['5'][1]
track([u['5'], (125.7, 125.425)], 'HEAT_G', 0.3)
via(128.2, y5, 'GND')
track([u['4'], (128.2, y5)], 'GND', 0.3)
track([u['2'], (128.2, y5)], 'GND', 0.3)
track([(128.35, 116.85), (128.35, 124.3), (130.25, 124.3), (130.25, u['3'][1]), u['3']], 'HEAT_PWM')
track([(128.35, r14['1'][1]), r14['1']], 'HEAT_PWM')
track([r14['2'], (126.28, 120.17)], 'GND')           # C2/C8's ground via
via(128.2, 128.95, 'GATE_12V')
track([u['1'], (u['1'][0], 128.95), (128.2, 128.95)], 'GATE_12V', 0.3)

# bottom: C4's VIN_LOGIC pad -> R13 -> D10 cathode -> C21 -> rail via; grounds to U7's GND via
B = pcbnew.B_Cu
track([(r13['1'][0], 122.6), r13['1']], 'VIN_LOGIC', 0.3, B)
track([r13['2'], (d10['1'][0], r13['2'][1] + 0.6), d10['1']], 'GATE_12V', 0.3, B)
track([d10['1'], c21['1']], 'GATE_12V', 0.3, B)
track([c21['1'], (c21['1'][0], 128.5), (128.65, 128.95), (128.2, 128.95)], 'GATE_12V', 0.3, B)
track([d10['2'], (128.2, y5)], 'GND', 0.3, B)
track([c21['2'], d10['2']], 'GND', 0.3, B)

pcbnew.ZONE_FILLER(b).Fill(b.Zones())
pcbnew.SaveBoard(PCB, b)

# silkscreen and field layers, in the file text (pcbnew's bindings return dead objects for
# footprint items once anything has been removed from the footprint)
t = open(PCB).read()


def block_end(s, i):
    d = 0
    while True:
        c = s[i]
        if c == '"':
            i = s.index('"', i + 1)
            while s[i - 1] == '\\':
                i = s.index('"', i + 1)
        elif c == '(':
            d += 1
        elif c == ')':
            d -= 1
            if d == 0:
                return i + 1
        i += 1


out, pos = [], 0
for m in re.finditer(r'\(footprint "', t):
    if m.start() < pos:
        continue
    e = block_end(t, m.start())
    blk = t[m.start():e]
    ref = re.search(r'\(property "Reference" "([^"]*)"', blk).group(1)
    if ref in ('U7', 'D10', 'C21', 'R13', 'R14'):
        side = 'B' if '(layer "B.Cu")' in blk[:300] else 'F'
        if ref in ('U7', 'D10', 'C21'):
            nb, j = '', 0
            for g in re.finditer(r'\(fp_(line|poly|circle|arc|rect)\b', blk):
                if g.start() < j:
                    continue
                ge = block_end(blk, g.start())
                if '.SilkS"' in blk[g.start():ge]:
                    k = blk.rindex('\n', 0, g.start())
                    nb += blk[j:k]; j = ge
            blk = nb + blk[j:]
        for prop in ('Reference', 'Value', 'LCSC'):
            ps = blk.find(f'(property "{prop}"')
            if ps >= 0:
                pe = block_end(blk, ps)
                p = re.sub(r'\(layer "[FB]\.(SilkS|Fab)"\)', f'(layer "{side}.Fab")', blk[ps:pe], count=1)
                if prop == 'LCSC' and '(hide yes)' not in p:
                    p = p.replace(f'(layer "{side}.Fab")', f'(layer "{side}.Fab")\n\t\t\t(hide yes)', 1)
                blk = blk[:ps] + p + blk[pe:]
    out += [t[pos:m.start()], blk]
    pos = e
out.append(t[pos:])
open(PCB, 'w').write(''.join(out))
print('gate driver added: U7, R13, D10, C21 placed and routed; R14 moved')
