"""current_solve.py net.json AMPS "SRC" "SINK" [png] : DC current flow in one net's copper
(exported by export_net.py), solved as a resistor grid on a 0.05 mm raster (RES).
SRC / SINK: comma-separated pads, REF:NUM (all pads of that number). The source pads are held at
one potential, the sink pads at 0; the result is scaled to AMPS total. Reports per layer the
peak current per mm of width (smoothed over 0.5 mm) and where, the dissipation, and each via's and
plated hole's current; png: each layer's current density, white at 6 A/mm.
Copper: outer 35 um (1 oz), inner INNER_UM (default 17.5, JLCPCB's 0.5 oz default), barrels
PLATE_UM (default 18); JLCPCB 1.6 mm 4-layer stack: 0.21 mm outer-inner, 1.07 mm core."""
import json, os, sys
import numpy as np
import scipy.sparse as sp
import scipy.sparse.linalg as spl
from PIL import Image, ImageDraw

RHO = 1.72e-5                # copper at 20 C, ohm * mm
H = float(os.environ.get('RES', '0.05'))   # grid mm
INNER = float(os.environ.get('INNER_UM', '17.5')) * 1e-3
OUTER = float(os.environ.get('OUTER_UM', '35')) * 1e-3
PLATE = float(os.environ.get('PLATE_UM', '18')) * 1e-3
d = json.load(open(sys.argv[1]))
I_TOT = float(sys.argv[2])
order = d['order']
th = {l: (OUTER if i in (0, len(order) - 1) else INNER) for i, l in enumerate(order)}
gap = [0.21, 1.07, 0.21] if len(order) == 4 else [1.5]
x0, y0, x1, y1 = d['bbox']
W, Hh = int((x1 - x0) / H) + 2, int((y1 - y0) / H) + 2


def raster(polys):
    im = Image.new('L', (W, Hh), 0)
    dr = ImageDraw.Draw(im)
    for outline, holes in polys:
        dr.polygon([((x - x0) / H, (y - y0) / H) for x, y in outline], fill=1)
    for outline, holes in polys:
        for h in holes:
            dr.polygon([((x - x0) / H, (y - y0) / H) for x, y in h], fill=0)
    return np.array(im, bool)


masks = {l: raster(d['layers'][l]) for l in order}
# a hole cut out of one polygon may be filled by another (a track over a pour hole): redraw all
# outlines last so overlaps stay copper
for l in order:
    for outline, holes in d['layers'][l]:
        im = Image.new('L', (W, Hh), 0)
        ImageDraw.Draw(im).polygon([((x - x0) / H, (y - y0) / H) for x, y in outline], fill=1)
        m = np.array(im, bool)
        for h in holes:
            im2 = Image.new('L', (W, Hh), 0)
            ImageDraw.Draw(im2).polygon([((x - x0) / H, (y - y0) / H) for x, y in h], fill=1)
            m &= ~np.array(im2, bool)
        masks[l] |= m
idx = {}
n = 0
for l in order:
    k = -np.ones((Hh, W), int)
    c = masks[l].sum()
    k[masks[l]] = np.arange(n, n + c)
    idx[l] = k
    n += c
rows, cols, vals = [], [], []


def g(a, b, c):
    rows.extend([a, b, a, b]); cols.extend([a, b, b, a]); vals.extend([c, c, -c, -c])


for l in order:
    k = idx[l]
    G = th[l] / RHO            # sheet conductance (S per square)
    for dy, dx in ((0, 1), (1, 0)):
        a = k[:Hh - dy, :W - dx]; b = k[dy:, dx:]
        m = (a >= 0) & (b >= 0)
        p, q = a[m], b[m]
        rows.extend(np.r_[p, q, p, q]); cols.extend(np.r_[p, q, q, p])
        vals.extend(np.r_[np.full(len(p), G), np.full(len(p), G), np.full(len(p), -G), np.full(len(p), -G)])
# barrels: vias and plated holes join the cells under their pad on each layer
barrels = [dict(kind='via', x=v['x'], y=v['y'], drill=v['drill'], r=v['dia'] / 2, layers=order) for v in d['vias']]
barrels += [dict(kind='%s:%s' % (p['ref'], p['num']), x=p['x'], y=p['y'], drill=p['drill'], r=p['drill'] / 2 + 0.15,
                 layers=p['layers']) for p in d['pads'] if p['drill'] > 0]
yy, xx = np.mgrid[0:Hh, 0:W]
extra = []
for bi, bb in enumerate(barrels):
    cx, cy = (bb['x'] - x0) / H, (bb['y'] - y0) / H
    disk = (xx - cx) ** 2 + (yy - cy) ** 2 <= (bb['r'] / H) ** 2
    nodes = []
    for l in order:
        if l not in bb['layers']:
            nodes.append(None); continue
        cells = idx[l][disk & (idx[l] >= 0)]
        if len(cells) == 0:
            nodes.append(None); continue
        hub = n; n += 1
        for c in cells:
            g(hub, c, 50.0)
        nodes.append(hub)
    bb['nodes'] = nodes
    gb = np.pi * bb['drill'] * PLATE / RHO      # S*mm: divide by length
    last = None
    for li, nd in enumerate(nodes):
        if nd is None:
            continue
        if last is not None:
            L = sum(gap[last:li])
            g(nodes[last], nd, gb / L)
        last = li
A = sp.csr_matrix((vals, (rows, cols)), shape=(n, n))


def term(spec):
    out = set()
    for s in spec.split(','):
        ref, num = s.split(':')
        for p in d['pads']:
            if p['ref'] == ref and p['num'] == num:
                for l, shp in p['shapes'].items():
                    m = raster(shp)
                    out |= set(idx[l][m & (idx[l] >= 0)].tolist())
    return np.array(sorted(out))


src, snk = term(sys.argv[3]), term(sys.argv[4])
assert len(src) and len(snk), 'no terminal cells'
fixed = np.zeros(n, bool); fixed[src] = True; fixed[snk] = True
V = np.zeros(n); V[src] = 1.0
free = ~fixed
# drop copper islands not joined to a terminal (singular otherwise)
ncomp, lab = sp.csgraph.connected_components(A, directed=False)
live = np.isin(lab, np.unique(lab[np.r_[src, snk]]))
free &= live
Aff = A[free][:, free]
rhs = -A[free][:, fixed] @ V[fixed]
V[free] = spl.spsolve(Aff.tocsc(), rhs)
Iin = (A[src] @ V).sum()
scale = I_TOT / Iin
V *= scale
Vdrop = V[src].mean()
print('%s: %.2f A from %s to %s: %.1f mOhm, %.0f mV, %.0f mW in total' %
      (d['net'], I_TOT, sys.argv[3], sys.argv[4], Vdrop / I_TOT * 1e3, Vdrop * 1e3, Vdrop * I_TOT * 1e3))
# current per mm of width on each layer, smoothed over 0.5 mm
k5 = max(1, int(round(0.5 / H)))
ker = np.ones((k5, k5)) / k5 ** 2
from scipy.signal import convolve2d
report = []
pic = []
for l in order:
    k = idx[l]
    G = th[l] / RHO
    vm = np.full((Hh, W), np.nan); vm[k >= 0] = V[k[k >= 0]]
    gx = np.zeros((Hh, W)); gy = np.zeros((Hh, W))
    a, b = vm[:, :-1], vm[:, 1:]
    dx = np.where(np.isnan(a) | np.isnan(b), 0, (b - a) / H)
    gx[:, :-1] += dx / 2; gx[:, 1:] += dx / 2
    a, b = vm[:-1], vm[1:]
    dy = np.where(np.isnan(a) | np.isnan(b), 0, (b - a) / H)
    gy[:-1] += dy / 2; gy[1:] += dy / 2
    J = G * np.hypot(gx, gy)          # A per mm of width
    J[k < 0] = 0
    Js = convolve2d(J, ker, mode='same')
    P = (G * (gx ** 2 + gy ** 2) * H * H)[k >= 0].sum()
    iy, ix = np.unravel_index(np.argmax(Js), Js.shape)
    over = (Js > (3.0 if th[l] >= 0.03 else 3.0 * th[l] / 0.035)).sum() * H * H
    report.append((l, Js.max(), x0 + ix * H - 100, y0 + iy * H - 100, P * 1e3, over))
    pic.append(J)
for l, jm, x, y, p, over in report:
    lim = 3.0 if th[l] >= 0.03 else 3.0 * th[l] / 0.035
    print('  %-6s %4.0f um: peak %.2f A/mm at (%.2f, %.2f), %.0f mW; %.2f mm2 above %.1f A/mm' %
          (l, th[l] * 1e3, jm, x, y, p, over, lim))
for bb in barrels:
    nd = [x for x in bb['nodes'] if x is not None]
    if len(nd) < 2:
        continue
    # current through the barrel = largest current between consecutive hubs
    cur = 0
    nodes = [(li, x) for li, x in enumerate(bb['nodes']) if x is not None]
    gb = np.pi * bb['drill'] * PLATE / RHO
    for (la, a), (lb, b) in zip(nodes, nodes[1:]):
        cur = max(cur, abs(V[a] - V[b]) * gb / sum(gap[la:lb]))
    if cur > float(os.environ.get('VIA_SHOW', '0.3')):
        print('  %-8s %.2f mm drill at (%.2f, %.2f): %.2f A' % (bb['kind'], bb['drill'], bb['x'] - 100, bb['y'] - 100, cur))
if len(sys.argv) > 5:
    ims = [Image.fromarray((np.clip(j / 6.0, 0, 1) * 255).astype(np.uint8)).convert('RGB') for j in pic]
    out = Image.new('RGB', (W * len(ims) + 10 * (len(ims) - 1), Hh), 'white')
    for i, im in enumerate(ims):
        out.paste(im, (i * (W + 10), 0))
    out.save(sys.argv[5])
