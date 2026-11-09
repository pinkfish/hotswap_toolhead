"""Move routed blocks of a board to a new outline, keeping each block's own copper.
    blocks.py in.kicad_pcb out.kicad_pcb
Each block in BLOCKS is a set of parts and a move: rotate by `rot` degrees about the first
part's anchor (positive is counter-clockwise as seen from the top, as in KiCad), then shift by
(dx, dy), or put that anchor at `to`. A block's `cut` (old board mm) removes the tracks that
cross that boundary first, so the block keeps its side of a run that went on to another block
(the USB-C data pins' run from U5 on to the MCU). Copper is grouped into runs of tracks and vias joined end
to end (pads end a run). A run moves with its block when every pad it touches belongs to that
block; runs reaching another block or a part in no block, and runs touching no pad (the old GND
stitching), are removed, as are all zones: the router and the pour scripts redo them. Parts in
no block stay where they are for place.py to place. declash.py then removes any kept copper
that conflicts with the new placement.
"""
import os
import subprocess
import sys

import pcbnew

O = 100.0
mm, tomm = pcbnew.FromMM, pcbnew.ToMM

BLOCKS = {
    # XT30 and the power input underneath it, 0.25 mm left (clear of the USB-C); D1 moves between
    # J1's power pins (plan_narrow.py, power_pre.py NARROW)
    'power': dict(refs=['J1', 'Q1', 'F1', 'D2', 'R1'], rot=0, dx=-0.25, dy=0),
    # USB-C on the top edge as before, with the ESD chip, its capacitor and the CC resistors; the
    # data pins' run on to the MCU is cut at the bottom of this box
    'usb': dict(refs=['J5', 'U5', 'C17', 'R20', 'R21'], rot=0, dx=-4.0, dy=0,
                cut=(19.3, -1.0, 31.0, 9.7)),
    # the MCU with its crystal, decoupling, VREF filter and the BOOT pads, and the CAN transceiver,
    # its ESD clamp and the termination left of it: into the old C1 column (CAN into H1's old
    # place), 0.4 mm down so J1's power pin clears U6's top pins. Moving them together keeps the
    # CAN lines and U3's supply as routed.
    'mcu': dict(refs=['U6', 'Y1', 'C9', 'C11', 'C12', 'C13', 'C14', 'C15', 'FB1', 'JP3', 'R4',
                      'D4', 'U3', 'C16', 'R11', 'JP1'], rot=0, dx=-3.3, dy=0.4),
    # the buck converter strip on the right-hand edge
    'buck': dict(refs=['R2', 'R3', 'D7', 'U1', 'C6', 'C4', 'C5', 'L1'], rot=0, dx=-3.75, dy=0),
    # J2 centred on the bottom edge, with the clamps above it
    'j2': dict(refs=['J2', 'D6', 'D5'], rot=0, dx=-2.0, dy=0),
    # the fan fuse above J2, 0.3 mm lower than before so U6's +3V3 vias and NRST run below the MCU
    # keep their room (its +24V via is narrow_pre.py's, clear of Y1 and J2's pins)
    'fuse': dict(refs=['F2'], rot=0, dx=-2.0, dy=0.3),
}
# the USB-C body keep-out, new board mm: usb_pre.py's (20, -0.6)-(30, 6.2) moved with J5
USB_KEEPOUT = [(16.0, -0.6), (26.0, -0.6), (26.0, 6.2), (16.0, 6.2)]
# parts whose footprint changed since the source board: the 47 uF can (C1) is now a 1206
# ceramic, and the holes are M2.5. Same reference, nets by pad number, fields and attributes kept.
KLIB = '/Applications/KiCad/KiCad.app/Contents/SharedSupport/footprints'
SWAP = {'C1': ('Capacitor_SMD', 'C_1206_3216Metric', '10uF 50V X5R', {'LCSC': 'C13585'}),
        'H1': ('MountingHole', 'MountingHole_2.7mm_M2.5_Pad', 'M2.5 isolated', {}),
        'H2': ('MountingHole', 'MountingHole_2.7mm_M2.5_Pad', 'M2.5 isolated', {})}
HOLE_CRTYD_R = 2.75   # the library's 2.95 mm courtyard, cut to the 5.4 mm pad plus 0.05 mm
TRIM = 0.3   # a run reaching outside its block keeps its pieces within this of the block's parts
# the reset switch joins its two pins of each number inside: one of each pair needs a track
JUMPERS = ('SW1',)
# courtyards cut to the pads plus this (mm): the fan fuse's 0.25 mm margin overlaps J2's below it,
# though the 1812 body is inside its pads and J2's housing starts 0.3 mm below them
CRTYD_PADS = {'F2': 0.05}
# library folders by nickname, for SWAP parts outside KiCad's own libraries
LIBDIR = {'hotswap_toolhead': os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                           '../../hardware/footprints/hotswap_toolhead.pretty')}
# BLOCKS_FILE: another layout's blocks, swaps and keep-out (USB_KEEPOUT None for none), in place
# of the ones above
if os.environ.get('BLOCKS_FILE'):
    exec(open(os.environ['BLOCKS_FILE']).read())


def swap_parts(src, dst):
    """Run in a process of its own (blocks.py --swap): after a library footprint load, boards
    loaded later come back as untyped SWIG objects."""
    b = pcbnew.LoadBoard(src)
    io = pcbnew.PCB_IO_KICAD_SEXPR()
    for ref, (lib, name, value, fields) in SWAP.items():
        old = b.FindFootprintByReference(ref)
        if old.GetFPIDAsString() == f"{lib}:{name}":
            continue
        new = io.FootprintLoad(LIBDIR.get(lib, f'{KLIB}/{lib}.pretty'), name)
        new.SetFPID(pcbnew.LIB_ID(lib, name))
        new.SetParent(b)
        new.SetReference(ref)
        new.SetValue(value)
        for k, v in old.GetFieldsText().items():
            if k not in ('Reference', 'Value', 'Footprint'):
                new.SetField(k, fields.get(k, v))
        new.SetAttributes(old.GetAttributes())
        new.SetPath(old.GetPath())
        if lib == 'MountingHole':
            for g in new.GraphicalItems():
                if g.GetLayer() in (pcbnew.F_CrtYd, pcbnew.B_CrtYd) and g.GetShape() == pcbnew.SHAPE_T_CIRCLE:
                    g.SetEnd(g.GetCenter() + pcbnew.VECTOR2I(mm(HOLE_CRTYD_R), 0))
        nets = {p.GetNumber(): p.GetNet() for p in old.Pads()}
        for p in new.Pads():
            if p.GetNumber() in nets:
                p.SetNet(nets[p.GetNumber()])
        if old.GetLayer() == pcbnew.B_Cu:
            new.Flip(new.GetPosition(), False)
        new.SetPosition(old.GetPosition())
        new.SetOrientation(old.GetOrientation())
        b.Remove(old)
        b.Add(new)
    for ref in JUMPERS:
        b.FindFootprintByReference(ref).SetDuplicatePadNumbersAreJumpers(True)
    for ref, m in CRTYD_PADS.items():
        f = b.FindFootprintByReference(ref)
        e = [p.GetBoundingBox() for p in f.Pads()]
        lo = pcbnew.VECTOR2I(min(x.GetLeft() for x in e) - mm(m), min(x.GetTop() for x in e) - mm(m))
        hi = pcbnew.VECTOR2I(max(x.GetRight() for x in e) + mm(m), max(x.GetBottom() for x in e) + mm(m))
        for g in f.GraphicalItems():
            if g.GetLayer() in (pcbnew.F_CrtYd, pcbnew.B_CrtYd) and g.GetShape() == pcbnew.SHAPE_T_RECTANGLE:
                g.SetStart(lo)
                g.SetEnd(hi)
    pcbnew.SaveBoard(dst, b)


def runs(b, skip=()):
    """Copper runs: tracks and vias joined end to end (not through pads), with the parts whose
    pads each run touches. Items whose UUID is in skip are left out."""
    items = [t for t in b.GetTracks() if t.m_Uuid.AsString() not in skip]
    pads = [p for f in b.GetFootprints() for p in f.Pads()]
    parent = list(range(len(items)))

    def find(i):
        while parent[i] != i:
            parent[i] = parent[parent[i]]
            i = parent[i]
        return i

    def pts(t):
        return [t.GetPosition()] if t.GetClass() == 'PCB_VIA' else [t.GetStart(), t.GetEnd()]

    at = {}
    for i, t in enumerate(items):
        for p in pts(t):
            at.setdefault((p.x, p.y), []).append(i)
    for idx in at.values():
        for j in idx[1:]:
            parent[find(j)] = find(idx[0])
    # a via in the middle of a track, or a track end on a via's ring
    vias = [i for i, t in enumerate(items) if t.GetClass() == 'PCB_VIA']
    for i, t in enumerate(items):
        if t.GetClass() == 'PCB_VIA':
            continue
        s = pcbnew.SEG(t.GetStart(), t.GetEnd())
        for j in vias:
            v = items[j]
            if v.GetNetname() == t.GetNetname() and s.Distance(v.GetPosition()) <= v.GetWidth(pcbnew.F_Cu) // 2:
                parent[find(j)] = find(i)
    touch = {}
    for i, t in enumerate(items):
        for p in pts(t):
            for q in pads:
                if q.GetNetname() == t.GetNetname() and q.HitTest(p):
                    touch.setdefault(find(i), set()).add(q.GetParentFootprint().GetReference())
    groups = {}
    for i in range(len(items)):
        groups.setdefault(find(i), []).append(items[i])
    return [(g, touch.get(r, set())) for r, g in groups.items()]


def main(src, dst):
    subprocess.run([sys.executable, __file__, '--swap', src, dst], check=True)
    b = pcbnew.LoadBoard(dst)

    def inbox(p, r):
        x, y = tomm(p.x) - O, tomm(p.y) - O
        return r[0] <= x <= r[2] and r[1] <= y <= r[3]

    cut = [t for t in b.GetTracks() if t.GetClass() != 'PCB_VIA' and
           any(inbox(t.GetStart(), k['cut']) != inbox(t.GetEnd(), k['cut']) for k in BLOCKS.values() if 'cut' in k)]
    fps = {f.GetReference(): f for f in b.GetFootprints()}
    block_of = {r: n for n, k in BLOCKS.items() for r in k['refs']}
    moves = {}
    for name, k in BLOCKS.items():
        a = fps[k['refs'][0]].GetPosition()
        if 'to' in k:
            dx, dy = k['to'][0] - (tomm(a.x) - O), k['to'][1] - (tomm(a.y) - O)
        else:
            dx, dy = k['dx'], k['dy']
        moves[name] = (a, pcbnew.EDA_ANGLE(k['rot'], pcbnew.DEGREES_T), pcbnew.VECTOR2I(mm(dx), mm(dy)))
    # each block's area: its parts' courtyards on both sides, TRIM mm larger
    box = {}
    for name, k in BLOCKS.items():
        e = []
        for ref in k['refs']:
            for ly in (pcbnew.F_CrtYd, pcbnew.B_CrtYd):
                if fps[ref].GetCourtyard(ly).OutlineCount():
                    bb = fps[ref].GetCourtyard(ly).BBox()
                    e.append((bb.GetLeft(), bb.GetTop(), bb.GetRight(), bb.GetBottom()))
        box[name] = (min(a[0] for a in e) - mm(TRIM), min(a[1] for a in e) - mm(TRIM),
                     max(a[2] for a in e) + mm(TRIM), max(a[3] for a in e) + mm(TRIM))

    def within(p, r):
        return r[0] <= p.x <= r[2] and r[1] <= p.y <= r[3]

    def pts(t):
        return [t.GetPosition()] if t.GetClass() == 'PCB_VIA' else [t.GetStart(), t.GetEnd()]

    kept = {n: 0 for n in BLOCKS}
    drop = list(cut)
    cutset = {t.m_Uuid.AsString() for t in cut}
    for items, refs in runs(b, cutset):
        owners = {block_of.get(r) for r in refs}
        whole = len(owners) == 1 and None not in owners
        for t in items:
            # a run within one block moves whole; a run reaching other parts keeps the pieces
            # inside the area of a block it touches (the pin escapes), and loses the rest
            name = next(iter(owners)) if whole else next(
                (n for n in sorted(owners - {None}) if all(within(p, box[n]) for p in pts(t))), None)
            if name is None:
                drop.append(t)
                continue
            c, ang, d = moves[name]
            if ang.AsDegrees():
                t.Rotate(c, ang)
            t.Move(d)
            kept[name] += 1
    for name, k in BLOCKS.items():
        c, ang, d = moves[name]
        for r in k['refs']:
            if ang.AsDegrees():
                fps[r].Rotate(c, ang)
            fps[r].Move(d)
    for t in drop:
        b.Remove(t)
    pcbnew.SaveBoard(dst, b)
    b = pcbnew.LoadBoard(dst)
    for z in list(b.Zones()):
        b.Remove(z)
    # no F.Cu tracks under the USB-C receptacle's body, ahead of its pad row (usb_pre.py's
    # keep-out, moved with the connector); the GND pour may still fill it
    if USB_KEEPOUT:
        k = pcbnew.ZONE(b)
        k.SetIsRuleArea(True)
        ls = pcbnew.LSET()
        ls.AddLayer(pcbnew.F_Cu)
        k.SetLayerSet(ls)
        k.SetDoNotAllowTracks(True)
        k.SetDoNotAllowVias(False)
        k.SetDoNotAllowZoneFills(False)
        k.SetDoNotAllowPads(False)
        k.SetDoNotAllowFootprints(False)
        k.SetZoneName('USB-C body keep-out')
        o = k.Outline()
        o.NewOutline()
        for x, y in USB_KEEPOUT:
            o.Append(mm(O + x), mm(O + y))
        b.Add(k)
    pcbnew.SaveBoard(dst, b)
    print('kept copper per block', kept, 'removed', len(drop))


if __name__ == '__main__':
    if sys.argv[1] == '--swap':
        swap_parts(*sys.argv[2:4])
    else:
        main(*sys.argv[1:3])
