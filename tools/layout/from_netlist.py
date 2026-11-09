"""Build an unrouted board from a schematic netlist, taking footprints from a donor board.
    from_netlist.py netlist.net donor.kicad_pcb out.kicad_pcb
netlist.net is `kicad-cli sch export netlist` output. Each part keeps the donor board's
footprint when the donor has that reference with the same footprint (so the hand edits on the
single 27 x 36 board carry over: SW1's jumpered pads, the trimmed silkscreen, JP2's real
footprint, the M2.5 insert holes H1/H2); anything else is loaded from the KiCad library
(Footprint field) or the project library in hardware/footprints. Pads get the netlist's nets,
footprints get the symbol paths, fields and BOM/DNP flags; tracks, zones and drawings are
dropped (place.py draws the outline).
"""
import os
import re
import sys

import pcbnew

net_f, donor_f, out_f = sys.argv[1:4]
HW = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'hardware')
LIBS = [os.environ.get('KICAD_FP_DIR', '/Applications/KiCad/KiCad.app/Contents/SharedSupport/footprints'),
        os.path.join(HW, 'footprints')]
KEEP = ('H1', 'H2')   # board-only footprints (no symbol) kept from the donor


def parse(s):
    toks = re.findall(r'\(|\)|"(?:\\.|[^"\\])*"|[^\s()]+', s)
    stack = [[]]
    for t in toks:
        if t == '(':
            stack.append([])
        elif t == ')':
            x = stack.pop()
            stack[-1].append(x)
        else:
            stack[-1].append(t[1:-1].replace('\\"', '"') if t.startswith('"') else t)
    return stack[0][0]


def kids(node, name):
    return [c for c in node if isinstance(c, list) and c and c[0] == name]


def val(node, name, default=''):
    k = kids(node, name)
    return k[0][1] if k and len(k[0]) > 1 else default


nl = parse(open(net_f).read())
comps = {}
for c in kids(kids(nl, 'components')[0], 'comp'):
    props = {val(p, 'name'): val(p, 'value') for p in kids(c, 'property')}
    comps[val(c, 'ref')] = dict(value=val(c, 'value'), fp=val(c, 'footprint'), tstamp=val(c, 'tstamps'),
                                props=props)
pin_net = {}
for n in kids(kids(nl, 'nets')[0], 'net'):
    for node in kids(n, 'node'):
        pin_net[(val(node, 'ref'), val(node, 'pin'))] = val(n, 'name')

b = pcbnew.LoadBoard(donor_f)
# collect everything first: a Remove() invalidates the board's other item lists
drop = list(b.Groups()) + list(b.GetTracks()) + list(b.Zones()) + list(b.GetDrawings())
for f in b.GetFootprints():
    want = comps.get(f.GetReference())
    if f.GetReference() not in KEEP and (want is None or want['fp'] != f.GetFPIDAsString()):
        drop.append(f)
for item in drop:
    b.Remove(item)
pcbnew.SaveBoard(out_f, b)          # Remove() leaves stale proxies: reload
b = pcbnew.LoadBoard(out_f)
have = {f.GetReference(): f for f in b.GetFootprints()}

nets = {}


def net(name):
    if name not in nets:
        n = b.FindNet(name)
        if n is None:
            n = pcbnew.NETINFO_ITEM(b, name)
            b.Add(n)
        nets[name] = n
    return nets[name]


added = []
for ref, c in sorted(comps.items()):
    f = have.get(ref)
    if f is None:
        lib, name = c['fp'].split(':')
        path = [os.path.join(d, lib + '.pretty') for d in LIBS if os.path.isdir(os.path.join(d, lib + '.pretty'))]
        assert path, 'no library for ' + c['fp']
        f = pcbnew.FootprintLoad(path[0], name)
        assert f, 'no footprint ' + c['fp']
        f.SetFPID(pcbnew.LIB_ID(lib, name))
        f.SetReference(ref)
        f.SetPosition(pcbnew.VECTOR2I_MM(140, 100 + 6 * len(added)))
        b.Add(f)
        added.append(ref)
    f.SetValue(c['value'])
    f.SetPath(pcbnew.KIID_PATH('/' + c['tstamp']))
    f.SetSheetname('Root')
    f.SetSheetfile(c['props'].get('Sheetfile', ''))
    if c['props'].get('LCSC'):
        f.SetField('LCSC', c['props']['LCSC'])
    f.SetDNP('dnp' in c['props'])
    for p in f.Pads():
        name = pin_net.get((ref, p.GetNumber()))
        if name is not None:
            p.SetNet(net(name))
        elif p.GetNumber():
            p.SetNetCode(0)
        p.SetLocalZoneConnection(pcbnew.ZONE_CONNECTION_INHERITED)
for f in b.GetFootprints():
    if f.GetReference() not in comps and f.GetReference() not in KEEP:
        print('extra footprint', f.GetReference())
pcbnew.SaveBoard(out_f, b)
print(len(comps), 'parts;', 'new from the library:', added)
