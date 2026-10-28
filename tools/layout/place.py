"""Two-sided placement on a W x H, 4-layer board.
    place.py in.kicad_pcb out.kicad_pcb
PLAN entries: ref: (x, y, rot, side, fixed)   board coords from the top-left,
seen from the top.  side 'F' or 'B'.  Movable parts are pushed apart until
courtyards on each side don't overlap; bottom parts also keep clear of the
through-hole and NPTH pads of top parts.  rot None = try all four rotations
and keep the one with the shortest connections.
"""
import pcbnew, sys, math

import os
W, H = 31.0, float(os.environ.get('BH', '33'))
E = lambda k, d: float(os.environ.get(k, d))
H1Y, C1X, C1Y, JPX, JPY, U6X, U6Y = E('H1Y', 16.0), E('C1X', 17.6), E('C1Y', 15.6), E('JPX', 20.0), E('JPY', H - 3.0), E('U6X', 17.5), E('U6Y', 20.4)
OX, OY = 100.0, 100.0
# clear circle around each M3 hole on both sides, for a heat-set insert in a
# printed base: 3 mm radius, enough for an M3 screw head or washer
KEEP_R = 3.0
GAP = 0.15

PLAN = {
    # ---------------- top side: connectors, button, LEDs, bulk caps, jumpers, heater FET
    'H1': (3.5, H1Y, 0, 'F', 1), 'H2': (27.5, H - 3.5, 0, 'F', 1),
    'J1': (8.4, 7.27, 180, 'F', 1),
    'J5': (25.0, 3.65, 180, 'F', 1),
    'J2': (10.6, H - 11.1, 270, 'F', 1),
    'SW1': (29.0, 13.4, 90, 'F', 1), 'JP3': (29.6, 18.3, 90, 'F', 1),
    'LED1': (24.0, 11.0, 0, 'F', 1), 'LED2': (24.0, 13.0, 0, 'F', 1),
    'C1': (C1X, C1Y, 0, 'F', 1),
    'R11': (9.6, 12.95, 90, 'F', 1), 'JP1': (9.6, 16.6, 90, 'F', 1),
    # heater FET on top next to J2 pin 5, drain tab toward the connector
    # R13/R14 stand upright between U6's EP and corner vias, HEAT_PWM pads on top
    'Q2': (15.1, H - 7.25, 180, 'F', 1), 'R13': (18.0, 23.4, 90, 'F', 1), 'R14': (19.2, 23.4, 90, 'F', 1),
    'JP2': (JPX, JPY, 0, 'F', 1),
    # moved up from the bottom so J2 and the parts round it can come up 3 mm
    'C8': (24.8, 18.6, 0, 'F', 0),                                   # +3V3 bulk, over L1
    'C2': (24.8, 21.2, 0, 'F', 1), 'C3': (24.8, 23.7, 0, 'F', 1),    # +24V bulk ceramics
    'D6': (28.9, 22.9, 270, 'F', 1),                                 # TH_ADC clamp, right edge
    'Q3': (14.65, H - 2.9, 90, 'F', 1),                              # fan switch, under Q2
    'R17': (21.6, H - 6.1, 90, 'F', 0), 'R18': (22.8, H - 6.1, 90, 'F', 0),  # thermistor pull-ups by JP2
    # ---------------- bottom: power input under J1
    'Q1': (9.7, 3.9, 0, 'B', 1), 'F1': (14.7, 4.6, 90, 'B', 1), 'D1': (18.0, 4.6, 90, 'B', 1),
    'D2': (3.45, 2.75, 0, 'B', 1), 'R1': (1.5, 6.0, 90, 'B', 1),
    # CAN: ESD, transceiver; termination on top
    'D4': (9.0, 14.3, 90, 'B', 1), 'U3': (10.0, 18.2, 0, 'B', 1),   # up 0.7: J2's pins are below
    'C16': (6.95, 18.2, 270, 'B', 1),   # +3V3 pad up, beside U3 pin 3
    # USB under J5
    'U5': (25.0, 7.2, 90, 'B', 1), 'C17': (25.0, 3.0, 0, 'B', 1),
    'R20': (27.9, 4.5, 90, 'B', 1), 'R21': (22.1, 4.5, 90, 'B', 1), 'D3': (25.4, 11.0, 0, 'B', 1),
    # buck between the CAN block and L1
    'D7': (20.6, 9.4, 0, 'B', 1), 'C4': (20.75, 12.3, 0, 'B', 1), 'C5': (17.5, 9.4, 90, 'B', 1),
    'U1': (16.2, 12.9, 0, 'B', 1), 'C6': (13.2, 14.25, 90, 'B', 1),
    'R2': (12.75, 11.25, 0, 'B', 1), 'R3': (12.75, 12.5, 0, 'B', 1),
    'D9': (20.6, 14.85, 0, 'B', 1), 'L1': (25.2, 15.9, 0, 'B', 1),
    # LEDs, boot
    'R5': (28.3, 10.6, 90, 'B', 1), 'R6': (28.3, 15.15, 90, 'B', 1), 'R4': (28.6, 18.3, 90, 'B', 1),
    # MCU; crystal under pins 8/9, supply and VREF caps along its lower side
    'U6': (U6X, U6Y, 90, 'B', 1),
    # corner cluster: corner_pre.py sets the final positions and rotations
    'Y1': (U6X - 2.3, U6Y + 6.8, 270, 'B', 1), 'C9': (U6X + 0.1, U6Y + 5.83, 90, 'B', 1),
    'C11': (U6X + 1.12, U6Y + 5.88, 90, 'B', 1), 'C12': (U6X + 2.14, U6Y + 5.88, 90, 'B', 1),
    'FB1': (U6X + 3.16, U6Y + 5.88, 90, 'B', 1), 'C13': (U6X + 0.1, U6Y + 8.2, 90, 'B', 1),
    'C10': (U6X + 2.6, U6Y + 9.25, 0, 'B', 1), 'C14': (U6X - 4.7, U6Y + 7.8, 90, 'B', 1),
    'C15': (U6X - 5.15, U6Y + 5.0, 90, 'B', 1),
    # thermistor filter under the crystal; fan switch and sensor parts round J2's pins
    'R19': (16.0, 30.6, 90, 'B', 1), 'C19': (17.2, 30.6, 90, 'B', 1),   # th_pre's lane ends here
    'R15': (10.3, H - 6.3, 0, 'B', 0), 'R16': (8.6, H - 1.4, 0, 'B', 0),
    'F2': (5.85, H - 4.9, 0, 'B', 1), 'D5': (1.5, H - 4.8, 90, 'B', 1),
    # sensor pull-up, series resistor and filter in a row on top, between H1's keep-out and
    # J2's courtyard; the bottom strip above J2's pins is left for FAN_P
    'R22': (1.4, 19.95, 0, 'F', 1), 'R23': (3.5, 19.95, 0, 'F', 1), 'C20': (5.6, 19.95, 0, 'F', 1),
}
PIN_TARGET = {}
ESCAPE = {'U6': (1.2, 0.4, 0.6, 0.3)}
PIN_OUT = 3.0   # mm outward from the owner's centre past the pin
EDGE_OK = {'J1', 'J2', 'J5', 'SW1', 'H1', 'H2'}
HOLES = {'H1', 'H2'}   # keep-out on both sides


def main(src, dst):
    b = pcbnew.LoadBoard(src)
    # drop keep-outs from an earlier run of this script, so moved holes don't leave stale ones
    # (b.Remove() leaves the other SWIG proxies dangling, so save and reload afterwards)
    stale = [z for z in b.Zones() if z.GetIsRuleArea() and z.GetZoneName().endswith('insert keep-out')]
    if stale:
        for z in stale:
            b.Remove(z)
        pcbnew.SaveBoard(dst, b)
        b = pcbnew.LoadBoard(dst)
    fps = {f.GetReference(): f for f in b.GetFootprints()}
    missing = sorted(set(fps) - set(PLAN))
    assert not missing, missing

    # 4 copper layers: In1 = GND plane, In2 = signals + pours
    b.SetCopperLayerCount(4)
    b.SetLayerType(pcbnew.In1_Cu, pcbnew.LT_POWER)
    b.SetLayerType(pcbnew.In2_Cu, pcbnew.LT_POWER)
    en = b.GetEnabledLayers()
    en.AddLayer(pcbnew.In1_Cu)
    en.AddLayer(pcbnew.In2_Cu)
    b.SetEnabledLayers(en)

    drawings = list(b.GetDrawings())
    for d in drawings:
        if d.GetLayerName() == 'User.Comments' and hasattr(d, 'SetPosition'):
            p = d.GetPosition()
            d.SetPosition(pcbnew.VECTOR2I(p.x, p.y - pcbnew.FromMM(60)))
    for d in drawings:
        if d.GetLayerName() == 'Edge.Cuts':
            b.Remove(d)
    r = pcbnew.PCB_SHAPE(b)
    r.SetShape(pcbnew.SHAPE_T_RECT)
    r.SetStart(pcbnew.VECTOR2I_MM(OX, OY))
    r.SetEnd(pcbnew.VECTOR2I_MM(OX + W, OY + H))
    r.SetLayer(pcbnew.Edge_Cuts)
    r.SetWidth(pcbnew.FromMM(0.1))
    b.Add(r)

    def put(ref, x, y, rot):
        f = fps[ref]
        f.SetOrientationDegrees(rot)
        f.SetPosition(pcbnew.VECTOR2I_MM(OX + x, OY + y))

    for ref, (x, y, rot, side, _) in PLAN.items():
        f = fps[ref]
        if f.IsFlipped() != (side == 'B'):
            f.Flip(f.GetPosition(), False)
        put(ref, x, y, rot or 0)

    def side(ref):
        return PLAN[ref][3]

    # mounting holes: courtyard circles of KEEP_R on both sides, so DRC flags any
    # part inside, plus a rule area keeping tracks, vias and pours out
    hole_c = []
    for ref in sorted(HOLES):
        f = fps[ref]
        c = f.GetPosition()
        hole_c.append((pcbnew.ToMM(c.x), pcbnew.ToMM(c.y)))
        for item in list(f.GraphicalItems()):
            if item.GetLayer() in (pcbnew.F_CrtYd, pcbnew.B_CrtYd):
                f.Remove(item)
        for layer in (pcbnew.F_CrtYd, pcbnew.B_CrtYd):
            g = pcbnew.PCB_SHAPE(f, pcbnew.SHAPE_T_CIRCLE)
            g.SetLayer(layer)
            g.SetCenter(c)
            g.SetEnd(pcbnew.VECTOR2I(c.x + pcbnew.FromMM(KEEP_R), c.y))
            g.SetWidth(pcbnew.FromMM(0.05))
            f.Add(g)
        f.BuildCourtyardCaches()
        z = pcbnew.ZONE(b)
        z.SetIsRuleArea(True)
        z.SetLayerSet(pcbnew.LSET.AllCuMask())
        z.SetDoNotAllowTracks(True)
        z.SetDoNotAllowVias(True)
        z.SetDoNotAllowZoneFills(True)
        z.SetDoNotAllowPads(False)
        z.SetDoNotAllowFootprints(False)
        z.SetZoneName(ref + ' insert keep-out')
        o = z.Outline(); o.NewOutline()
        for i in range(36):
            a = 2 * math.pi * i / 36
            o.Append(c.x + pcbnew.FromMM(KEEP_R * math.cos(a)), c.y + pcbnew.FromMM(KEEP_R * math.sin(a)))
        b.Add(z)

    def hits_hole(bx):
        for cx, cy in hole_c:
            nx, ny = min(max(cx, bx[0]), bx[2]), min(max(cy, bx[1]), bx[3])
            if math.hypot(cx - nx, cy - ny) < KEEP_R:
                return True
        return False

    def box(f):
        c = f.GetCourtyard(pcbnew.B_Cu if f.IsFlipped() else pcbnew.F_Cu)
        bb = c.BBox() if c.OutlineCount() else f.GetBoundingBox(False)
        return [pcbnew.ToMM(v) for v in (bb.GetLeft(), bb.GetTop(), bb.GetRight(), bb.GetBottom())]

    # fixed keep-outs on the bottom: through-hole and NPTH pads of top parts, and the holes
    obst_b = []
    for ref, f in fps.items():
        if side(ref) != 'F':
            continue
        if ref in HOLES:
            continue
        for p in f.Pads():
            if p.GetAttribute() in (pcbnew.PAD_ATTRIB_PTH, pcbnew.PAD_ATTRIB_NPTH):
                bb = p.GetBoundingBox()
                m = 0.25
                obst_b.append([pcbnew.ToMM(bb.GetLeft()) - m, pcbnew.ToMM(bb.GetTop()) - m,
                               pcbnew.ToMM(bb.GetRight()) + m, pcbnew.ToMM(bb.GetBottom()) + m])

    # ratsnest length for choosing rotations
    def pads_by_net():
        d = {}
        for ref, f in fps.items():
            for p in f.Pads():
                n = p.GetNetname()
                if n and not n.startswith('unconnected') and n not in ('/GND',):
                    d.setdefault(n, []).append((ref, p))
        return d
    nets = pads_by_net()

    def cost(ref):
        c = 0.0
        for p in fps[ref].Pads():
            n = p.GetNetname()
            if n not in nets:
                continue
            a = p.GetPosition()
            ds_ = [math.hypot(a.x - q.GetPosition().x, a.y - q.GetPosition().y)
                   for r2, q in nets[n] if r2 != ref]
            if ds_:
                c += min(ds_)
        return c

    def choose_rotations():
        for ref, (x, y, rot, s, fixed) in PLAN.items():
            if rot is not None or fixed:
                continue
            pos = fps[ref].GetPosition()
            best = None
            for r_ in (0, 90, 180, 270):
                fps[ref].SetOrientationDegrees(r_)
                fps[ref].SetPosition(pos)
                k = cost(ref)
                if best is None or k < best[0] - 1:
                    best = (k, r_)
            fps[ref].SetOrientationDegrees(best[1])
            fps[ref].SetPosition(pos)

    def legal_place():
        """Greedy: fixed parts first, then movable parts by size, each at the
        free spot nearest its planned position (rotations tried in order of
        shortest connections)."""
        placed = {'F': [], 'B': list(obst_b)}
        for ref in PLAN:
            if PLAN[ref][4] and ref not in HOLES:
                placed[side(ref)].append(box(fps[ref]))
        # escape ring round the MCU: room for fanout vias (left, top, right, bottom)
        for ref, (ml, mt, mr, mb) in ESCAPE.items():
            L, T, R, B_ = box(fps[ref])
            placed[side(ref)].append([L - ml, T - mt, R + mr, B_ + mb])
        mov = [r for r in PLAN if not PLAN[r][4] and r not in HOLES]
        def area(r):
            L, T, R, B_ = box(fps[r]); return (R - L) * (B_ - T)
        order = list(PIN_TARGET)
        mov.sort(key=lambda r: (order.index(r) if r in order else len(order), -area(r)))
        def free(bx, s):
            if bx[0] < OX + 0.3 or bx[1] < OY + 0.3 or bx[2] > OX + W - 0.3 or bx[3] > OY + H - 0.3:
                return False
            if hits_hole(bx):
                return False
            for o in placed[s]:
                if min(bx[2], o[2]) - max(bx[0], o[0]) > -GAP and min(bx[3], o[3]) - max(bx[1], o[1]) > -GAP:
                    return False
            return True
        fails = []
        owner = {}
        for r0 in PLAN:
            if PLAN[r0][4] and r0 not in HOLES: owner[tuple(box(fps[r0]))] = r0
        def target(ref):
            # small parts aim at the middle of what they connect to (no GND / +3V3)
            pts = []
            for p in fps[ref].Pads():
                n = p.GetNetname()
                if n in nets and n != '/+3V3':
                    pts += [q.GetPosition() for r2, q in nets[n] if r2 != ref and (r2 not in mov or r2 in done)]
            if not pts:
                return None
            return (pcbnew.ToMM(sum(q.x for q in pts) / len(pts)) - OX, pcbnew.ToMM(sum(q.y for q in pts) / len(pts)) - OY)
        done = set()
        for ref in mov:
            x0, y0, rot, s, _ = PLAN[ref]
            f = fps[ref]
            if ref in PIN_TARGET:
                o_ref, pad_no = PIN_TARGET[ref]
                o = fps[o_ref]
                pp = [p for p in o.Pads() if p.GetNumber() == pad_no][0].GetPosition()
                cx, cy = pcbnew.ToMM(o.GetPosition().x), pcbnew.ToMM(o.GetPosition().y)
                px, py = pcbnew.ToMM(pp.x), pcbnew.ToMM(pp.y)
                dx, dy = px - cx, py - cy
                n = math.hypot(dx, dy) or 1
                # push straight out from the nearest side of the owner
                if abs(dx) > abs(dy):
                    x0, y0 = px + math.copysign(PIN_OUT, dx) - OX, py - OY
                else:
                    x0, y0 = px - OX, py + math.copysign(PIN_OUT, dy) - OY
            done.add(ref)
            rots = [rot] if rot is not None else [0, 90, 180, 270]
            if rot is None:
                ranked = []
                for r_ in rots:
                    put(ref, x0, y0, r_); ranked.append((cost(ref), r_))
                rots = [r_ for _, r_ in sorted(ranked)]
            best = None
            for r_ in rots:
                put(ref, x0, y0, r_)
                bx0 = box(f)
                for ring in range(0, 81):          # 0.25 mm steps out to 20 mm
                    d = ring * 0.25
                    cands = [(0.0, 0.0)] if ring == 0 else \
                        [(dx * 0.25, dy * 0.25) for dx in range(-ring, ring + 1) for dy in (-ring, ring)] + \
                        [(dx * 0.25, dy * 0.25) for dy in range(-ring + 1, ring) for dx in (-ring, ring)]
                    hit = None
                    for dx, dy in sorted(cands, key=lambda c: math.hypot(*c)):
                        bx = [bx0[0] + dx, bx0[1] + dy, bx0[2] + dx, bx0[3] + dy]
                        if free(bx, s):
                            hit = (math.hypot(dx, dy), dx, dy); break
                    if hit:
                        if best is None or hit[0] < best[0] - 0.5:
                            best = (hit[0], r_, hit[1], hit[2])
                        break
            if best is None:
                fails.append(ref); put(ref, x0, y0, rots[0]); continue
            _, r_, dx, dy = best
            put(ref, x0 + dx, y0 + dy, r_)
            placed[s].append(box(f)); owner[tuple(placed[s][-1])] = ref
            if best[0] > 1:
                put(ref, x0, y0, r_); bx = box(f)
                why = []
                if bx[0] < OX + 0.3 or bx[1] < OY + 0.3 or bx[2] > OX + W - 0.3 or bx[3] > OY + H - 0.3: why.append('edge')
                if hits_hole(bx): why.append('hole')
                for o in placed[s]:
                    if min(bx[2], o[2]) - max(bx[0], o[0]) > -GAP and min(bx[3], o[3]) - max(bx[1], o[1]) > -GAP:
                        why.append(owner.get(tuple(o), 'pin') + str([round(v - 100, 1) for v in o]))
                print(f'  {ref} moved {best[0]:.1f} [{round(bx[0]-100,1)},{round(bx[1]-100,1)},{round(bx[2]-100,1)},{round(bx[3]-100,1)}] hits', why)
                put(ref, x0 + dx, y0 + dy, r_)
        return fails

    fails = legal_place()
    print('could not place:', fails)

    bad = 0
    for ref in PLAN:
        if ref not in HOLES and hits_hole(box(fps[ref])):
            print('IN HOLE KEEP-OUT', ref); bad += 1
    for s in ('F', 'B'):
        refs = [r for r in PLAN if side(r) == s and r not in HOLES]
        boxes = {r: box(fps[r]) for r in refs}
        items = [(r, boxes[r]) for r in refs] + ([('pin', o) for o in obst_b] if s == 'B' else [])
        for i, (a, A) in enumerate(items):
            for bref, B in items[i + 1:]:
                if a == 'pin' and bref == 'pin':
                    continue
                if (a in HOLES or a == 'pin') and (bref in HOLES or bref == 'pin'):
                    continue
                if min(A[2], B[2]) > max(A[0], B[0]) and min(A[3], B[3]) > max(A[1], B[1]):
                    print('OVERLAP', s, a, bref, [round(v - 100, 1) for v in (B if a == 'pin' else A)]); bad += 1
    for ref in PLAN:
        L, T, R, B_ = box(fps[ref])
        if ref not in EDGE_OK and (L < OX or T < OY or R > OX + W or B_ > OY + H):
            print('OFF BOARD', ref); bad += 1
    area = {'F': 0, 'B': 0}
    for ref in PLAN:
        L, T, R, B_ = box(fps[ref])
        area[side(ref)] += (R - L) * (B_ - T)
    print('courtyard use: top %.0f%%  bottom %.0f%%' % (100 * area['F'] / (W * H), 100 * area['B'] / (W * H)))
    pcbnew.SaveBoard(dst, b)
    print('problems:', bad)


main(*sys.argv[1:3])
