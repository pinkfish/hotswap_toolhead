"""Grid maze router for the connections an autorouter left open.
    maze.py board.kicad_pcb drc.json [out.kicad_pcb]
Reads KiCad DRC json 'unconnected_items', routes each pair on F/In2/B with
A* on a 0.05 mm grid (real pad shapes, netclass clearances, hole and edge
clearance, through vias), adds the tracks/vias and refills zones. ORDER: nets to route first;
ONLY: route just these nets; LOCK: lock what's routed (comma-separated net names).
"""
import heapq
import os
import json
import math
import sys

import pcbnew

mm, tomm = pcbnew.FromMM, pcbnew.ToMM
src, drcf = sys.argv[1:3]
out = sys.argv[3] if len(sys.argv) > 3 else src
b = pcbnew.LoadBoard(src)
G = 0.05                       # grid pitch, mm
# routable layers: In2 only when it isn't a plane
LAYERS = [pcbnew.F_Cu, pcbnew.In2_Cu, pcbnew.B_Cu]
if b.GetLayerType(pcbnew.In2_Cu) == pcbnew.LT_POWER:
    LAYERS.remove(pcbnew.In2_Cu)
HV = {'/VIN_RAW', '/VIN_F', '/+24V', '/HEAT_N', '/FAN_N', '/FAN_P'}
VIA_D, VIA_DRILL = 0.6, 0.3
HOLE_CLR, EDGE_CLR, MARGIN = 0.25, 0.5, 0.03
VIA_COST, DIAG = 25, math.sqrt(2)
WIDTH = {'/+3V3': 0.25, '/USB_D_P': 0.25, '/USB_D_N': 0.25,
         # net-class widths, so a maze route never undercuts the high-current DRC rules
         '/+24V': 0.8, '/VIN_RAW': 0.8, '/VIN_F': 0.8, '/HEAT_N': 0.8, '/FAN_N': 0.4, '/FAN_P': 0.4,
         '/VBUS': 0.3}
e = b.GetBoardEdgesBoundingBox()
EX0, EY0, EX1, EY1 = (tomm(v) for v in (e.GetLeft(), e.GetTop(), e.GetRight(), e.GetBottom()))


def clr(net):
    return 0.3 if net in HV else 0.2


def copper_items():
    """(net, layerset, shape getter, hole shape or None, bbox)"""
    items = []
    for f in b.GetFootprints():
        for p in f.Pads():
            hole = p.GetEffectiveHoleShape() if p.GetDrillSize().x > 0 else None
            items.append((p.GetNetname(), p, hole))
    for t in b.GetTracks():
        hole = t.GetEffectiveHoleShape() if t.GetClass() == 'PCB_VIA' else None
        items.append((t.GetNetname(), t, hole))
    return items


KILLED = set()      # uuids of tracks/vias ripped up this run
SOFT = bool(os.environ.get('SOFT'))
ONLY = {n for n in os.environ.get('ONLY', '').split(',') if n}   # route just these nets
LOCK = bool(os.environ.get('LOCK'))       # lock what's routed (hard nets routed before Freerouting)
SOFT_COST = 60


def ready_items():
    out = []
    for net, it, hole in copper_items():
        u = it.m_Uuid.AsString()
        if u in KILLED:
            continue
        rip = u if it.GetClass() in ('PCB_TRACK', 'PCB_VIA', 'PCB_ARC') and not it.IsLocked() else None
        shapes = {}
        for L in LAYERS + [pcbnew.In1_Cu, pcbnew.In2_Cu]:
            if it.IsOnLayer(L) or (it.GetClass() == 'PCB_VIA'):
                shapes[L] = it.GetEffectiveShape(L)
        bb = it.GetBoundingBox()
        out.append((net, shapes, hole, (tomm(bb.GetLeft()), tomm(bb.GetTop()), tomm(bb.GetRight()), tomm(bb.GetBottom())), rip))
    # non-GND copper zones (e.g. the HEAT_N pour) are obstacles too
    for z in b.Zones():
        if z.GetIsRuleArea() or z.GetNetname() == '/GND':
            continue
        L = z.GetLayer()
        if L not in LAYERS:
            continue
        bb = z.GetBoundingBox()
        out.append((z.GetNetname(), {L: z.Outline()}, None,
                    (tomm(bb.GetLeft()), tomm(bb.GetTop()), tomm(bb.GetRight()), tomm(bb.GetBottom())), None))
    return out


keepouts = [z for z in b.Zones() if z.GetIsRuleArea()]


class Grid:
    def __init__(self, x0, y0, x1, y1):
        self.x0, self.y0 = max(x0, EX0), max(y0, EY0)
        self.nx = int((min(x1, EX1) - self.x0) / G) + 1
        self.ny = int((min(y1, EY1) - self.y0) / G) + 1

    def pt(self, i, j):
        return self.x0 + i * G, self.y0 + j * G

    def cells(self, bx0, by0, bx1, by1):
        i0 = max(0, int(math.floor((bx0 - self.x0) / G)))
        j0 = max(0, int(math.floor((by0 - self.y0) / G)))
        i1 = min(self.nx - 1, int(math.ceil((bx1 - self.x0) / G)))
        j1 = min(self.ny - 1, int(math.ceil((by1 - self.y0) / G)))
        for j in range(j0, j1 + 1):
            for i in range(i0, i1 + 1):
                yield i, j


def V(x, y):
    return pcbnew.VECTOR2I(mm(x), mm(y))


def build(g, net, items, w, soft=False):
    """Blocked-cell grids.  With soft=True, unlocked tracks/vias of other nets
    don't block: their cells go into soft maps (cell -> uuids) instead."""
    n = g.nx * g.ny
    track = {L: bytearray(n) for L in LAYERS}        # 1 = blocked for a track
    via = bytearray(n)                                # 1 = blocked for a via
    stk = {L: {} for L in LAYERS}
    svia = {}
    vr = VIA_D / 2
    for onet, shapes, hole, (bx0, by0, bx1, by1), rip in items:
        if onet == net and onet != '':
            continue
        c = max(clr(net), clr(onet)) + MARGIN
        for L, sh in shapes.items():
            for rad, grid, smap in ((w / 2, track.get(L), stk.get(L)), (vr, via, svia)):
                if grid is None:
                    continue
                r = c + rad
                for i, j in g.cells(bx0 - r, by0 - r, bx1 + r, by1 + r):
                    k = j * g.nx + i
                    if grid[k]:
                        continue
                    if sh.Collide(V(*g.pt(i, j)), mm(r)):
                        if soft and rip:
                            smap.setdefault(k, set()).add(rip)
                        else:
                            grid[k] = 1
        if hole is not None and not (soft and rip):
            # copper-to-hole and hole-to-hole clearance
            for rad, grids in ((w / 2, list(track.values())), (vr, [via])):
                r = HOLE_CLR + rad + MARGIN
                for i, j in g.cells(bx0 - r, by0 - r, bx1 + r, by1 + r):
                    if hole.Collide(V(*g.pt(i, j)), mm(r)):
                        for grid in grids:
                            grid[j * g.nx + i] = 1
    # board edge and keep-outs
    for i in range(g.nx):
        for j in range(g.ny):
            x, y = g.pt(i, j)
            d = min(x - EX0, EX1 - x, y - EY0, EY1 - y)
            k = j * g.nx + i
            if d < EDGE_CLR + w / 2 + MARGIN:
                for L in LAYERS:
                    track[L][k] = 1
            if d < EDGE_CLR + vr + MARGIN:
                via[k] = 1
    for z in keepouts:
        bb = z.GetBoundingBox()
        r = vr + 0.05
        for i, j in g.cells(tomm(bb.GetLeft()) - r, tomm(bb.GetTop()) - r, tomm(bb.GetRight()) + r, tomm(bb.GetBottom()) + r):
            p = V(*g.pt(i, j))
            if z.GetDoNotAllowVias() and z.Outline().Collide(p, mm(vr)):
                via[j * g.nx + i] = 1
            if z.GetDoNotAllowTracks():
                for L in LAYERS:
                    if z.IsOnLayer(L) and z.Outline().Collide(p, mm(w / 2)):
                        track[L][j * g.nx + i] = 1
    return track, via, stk, svia


def find_item(desc, x, y, net):
    """Locate the board item a DRC description refers to."""
    best, bd = None, 1e9
    P = V(x, y)
    for f in b.GetFootprints():
        for p in f.Pads():
            if p.GetNetname() != net:
                continue
            if desc.startswith(('Pad', 'PTH pad', 'NPTH pad')) and f' of {f.GetReference()}' in desc:
                d = (p.GetPosition() - P).EuclideanNorm()
                if d < bd:
                    best, bd = p, d
    if best is None:
        for t in b.GetTracks():
            if t.GetNetname() != net:
                continue
            for L in LAYERS:
                if t.IsOnLayer(L):
                    d = 0 if t.GetEffectiveShape(L).Collide(P, mm(0.05)) else 1e9
                    if d < bd:
                        best, bd = t, d
    return best


def on(it, L):
    return it.GetClass() == 'PCB_VIA' or it.IsOnLayer(L)


def cluster(it):
    """Every same-net pad/track/via copper-connected to it (zones ignored)."""
    net = it.GetNetname()
    pool = [p for f in b.GetFootprints() for p in f.Pads() if p.GetNetname() == net]
    pool += [t for t in b.GetTracks() if t.GetNetname() == net]
    got, todo = [it], [it]
    ids = {it.m_Uuid.AsString()}
    while todo:
        a = todo.pop()
        for c in pool:
            u = c.m_Uuid.AsString()
            if u in ids:
                continue
            for L in LAYERS + [pcbnew.In1_Cu]:
                if on(a, L) and on(c, L) and a.GetEffectiveShape(L).Collide(c.GetEffectiveShape(L), 0):
                    ids.add(u)
                    got.append(c)
                    todo.append(c)
                    break
    return got


def item_cells(g, it):
    s = set()
    for part in cluster(it):
        bb = part.GetBoundingBox()
        for L in LAYERS:
            if not on(part, L):
                continue
            sh = part.GetEffectiveShape(L)
            for i, j in g.cells(tomm(bb.GetLeft()), tomm(bb.GetTop()), tomm(bb.GetRight()), tomm(bb.GetBottom())):
                if sh.Collide(V(*g.pt(i, j)), 0):
                    s.add((LAYERS.index(L), i, j))
    return s


def astar(g, track, via, starts, goals, stk=None, svia=None):
    stk = stk or {L: {} for L in LAYERS}
    svia = svia or {}
    smaps = [stk[L] for L in LAYERS]
    gx = [(i, j) for _, i, j in goals]
    cx = sum(i for i, _ in gx) / len(gx)
    cy = sum(j for _, j in gx) / len(gx)
    nx = g.nx
    best = {}
    heap = []
    for s in starts:
        best[s] = 0
        heapq.heappush(heap, (0, 0, s, None))
    prev = {}
    tgrid = [track[L] for L in LAYERS]
    while heap:
        f, cost, node, par = heapq.heappop(heap)
        if node in prev:
            continue
        prev[node] = par
        if node in goals:
            path = []
            while node is not None:
                path.append(node)
                node = prev[node]
            return path[::-1]
        l, i, j = node
        for di, dj in ((1, 0), (-1, 0), (0, 1), (0, -1), (1, 1), (1, -1), (-1, 1), (-1, -1)):
            ni, nj = i + di, j + dj
            if not (0 <= ni < nx and 0 <= nj < g.ny):
                continue
            nn = (l, ni, nj)
            if tgrid[l][nj * nx + ni] and nn not in goals:
                continue
            if di and dj and (tgrid[l][j * nx + ni] or tgrid[l][nj * nx + i]) and nn not in goals:
                continue
            nc = cost + (DIAG if di and dj else 1)
            if nj * nx + ni in smaps[l]:
                nc += SOFT_COST
            if nc < best.get(nn, 1e18):
                best[nn] = nc
                h = math.hypot(ni - cx, nj - cy)
                heapq.heappush(heap, (nc + h, nc, nn, node))
        if not via[j * nx + i]:
            vextra = SOFT_COST * 3 if j * nx + i in svia else 0
            for nl in range(len(LAYERS)):
                if nl == l:
                    continue
                nn = (nl, i, j)
                if tgrid[nl][j * nx + i] and nn not in goals:
                    continue
                nc = cost + VIA_COST + vextra + (SOFT_COST if j * nx + i in smaps[nl] else 0)
                if nc < best.get(nn, 1e18):
                    best[nn] = nc
                    heapq.heappush(heap, (nc + math.hypot(i - cx, j - cy), nc, nn, node))
    return None


def smooth(g, run, track, ok, smap=None):
    """Line-of-sight smoothing of one single-layer run of cells."""
    l = run[0][0]
    grid = track[LAYERS[l]]
    smap = smap or {}

    def clear(a, c):
        n = int(max(abs(c[1] - a[1]), abs(c[2] - a[2])) * 2) + 1
        for k in range(n + 1):
            i = round(a[1] + (c[1] - a[1]) * k / n)
            j = round(a[2] + (c[2] - a[2]) * k / n)
            k = j * g.nx + i
            if (grid[k] or not smap.get(k, set()) <= KILLED) and (l, i, j) not in ok:
                return False
        return True

    out, i = [run[0]], 0
    while i < len(run) - 1:
        j = len(run) - 1
        while j > i + 1 and not clear(run[i], run[j]):
            j -= 1
        out.append(run[j])
        i = j
    return out


def commit(g, path, netinfo, w, track, ok, stk=None):
    stk = stk or {L: {} for L in LAYERS}
    """Turn a cell path into tracks and vias."""
    segs, vias = [], []
    run = [path[0]]
    for a, c in zip(path, path[1:]):
        if c[0] != a[0]:
            vias.append(a)
            segs.append(run)
            run = [c]
            continue
        if len(run) >= 2:
            d0 = (run[-1][1] - run[-2][1], run[-1][2] - run[-2][2])
            d1 = (c[1] - a[1], c[2] - a[2])
            if d0 != d1:
                segs.append(run)
                run = [a]
        run.append(c)
    segs.append(run)
    # merge straight runs per layer, then smooth each layer run
    lay, cur = [], []
    for r in segs:
        if cur and r and cur[-1][0] == r[0][0]:
            cur += r[1:] if cur[-1] == r[0] else r
        else:
            if cur:
                lay.append(cur)
            cur = list(r)
    if cur:
        lay.append(cur)
    n = 0
    for r in lay:
        pts = smooth(g, r, track, ok, stk[LAYERS[r[0][0]]])
        for a, c in zip(pts, pts[1:]):
            t = pcbnew.PCB_TRACK(b)
            t.SetStart(V(*g.pt(a[1], a[2])))
            t.SetEnd(V(*g.pt(c[1], c[2])))
            t.SetWidth(mm(w))
            t.SetLayer(LAYERS[a[0]])
            t.SetNet(netinfo)
            t.SetLocked(LOCK)
            b.Add(t)
            n += 1
    for l, i, j in vias:
        v = pcbnew.PCB_VIA(b)
        v.SetPosition(V(*g.pt(i, j)))
        v.SetWidth(mm(VIA_D))
        v.SetDrill(mm(VIA_DRILL))
        v.SetNet(netinfo)
        v.SetLocked(LOCK)
        b.Add(v)
    return n, len(vias)


drc = json.load(open(drcf))
todo = []
for u in drc.get('unconnected_items', []):
    a, c = u['items']
    if 'Zone' in a['description'] or 'Zone' in c['description']:
        continue
    net = a['description'].split('[')[1].split(']')[0]
    if ONLY and net not in ONLY:
        continue
    todo.append((net, a, c))
# nets named in ORDER first (in that order), then short connections first
import os
ORDER = [n for n in os.environ.get('ORDER', '').split(',') if n]
todo.sort(key=lambda t: (ORDER.index(t[0]) if t[0] in ORDER else len(ORDER), math.hypot(t[1]['pos']['x'] - t[2]['pos']['x'], t[1]['pos']['y'] - t[2]['pos']['y'])))

done, failed = [], []
for net, a, c in todo:
    ia = find_item(a['description'], a['pos']['x'], a['pos']['y'], net)
    ic = find_item(c['description'], c['pos']['x'], c['pos']['y'], net)
    tag = f"{net}: {a['description'][:28]} -> {c['description'][:28]}"
    if ia is None or ic is None:
        failed.append(tag + ' (item not found)')
        continue
    # already joined by an earlier route this run?
    b.BuildConnectivity()
    cn = b.GetConnectivity()
    w = WIDTH.get(net, 0.2)
    path = None
    ripped = set()
    for M, soft in ((3.0, False), (6.0, False), (40.0, False), (4.0, True), (10.0, True)):
        if soft and not SOFT:
            continue
        xs = [a['pos']['x'], c['pos']['x']]
        ys = [a['pos']['y'], c['pos']['y']]
        g = Grid(min(xs) - M, min(ys) - M, max(xs) + M, max(ys) + M)
        track, via, stk, svia = build(g, net, ready_items(), w, soft)
        starts, goals = item_cells(g, ia), item_cells(g, ic)
        if not starts or not goals:
            continue
        path = astar(g, track, via, starts, goals, stk, svia)
        if path:
            for k, (l, i, j) in enumerate(path):
                ripped |= stk[LAYERS[l]].get(j * g.nx + i, set())
                if k and path[k - 1][0] != l:
                    ripped |= svia.get(j * g.nx + i, set())
            KILLED.update(ripped)
            break
    if not path:
        failed.append(tag)
        print('FAIL', tag, flush=True)
        continue
    nt, nv = commit(g, path, ia.GetNet(), w, track, starts | goals, stk)
    done.append(tag)
    print('ok  ', tag, f'{nt} tracks {nv} vias', f'(ripped {len(ripped)})' if ripped else '', flush=True)

if KILLED:
    # b.Remove() leaves other SWIG proxies dangling: remove, save, reload
    for t in [t for t in b.GetTracks() if t.m_Uuid.AsString() in KILLED]:
        b.Remove(t)
    pcbnew.SaveBoard(out, b)
    b = pcbnew.LoadBoard(out)
    # drop the stubs the rip-up left hanging, repeatedly
    while True:
        dead = []
        tracks = list(b.GetTracks())
        pads = [p for f in b.GetFootprints() for p in f.Pads()]
        for t in tracks:
            if t.GetClass() == 'PCB_VIA' or t.IsLocked():
                continue
            L = t.GetLayer()
            for end in (t.GetStart(), t.GetEnd()):
                hit = any(p.GetNetname() == t.GetNetname() and p.IsOnLayer(L) and p.GetEffectiveShape(L).Collide(end, 0) for p in pads)
                hit = hit or any(o is not t and o.GetNetname() == t.GetNetname() and (o.GetClass() == 'PCB_VIA' or o.GetLayer() == L)
                                 and o.GetEffectiveShape(L).Collide(end, 0) for o in tracks)
                if not hit:
                    dead.append(t)
                    break
        if not dead:
            break
        for t in dead:
            b.Remove(t)
        pcbnew.SaveBoard(out, b)
        b = pcbnew.LoadBoard(out)
    print('ripped up', len(KILLED))
pcbnew.ZONE_FILLER(b).Fill(b.Zones())
pcbnew.SaveBoard(out, b)
print('routed', len(done), 'failed', len(failed))
for f in failed:
    print('  ', f)
