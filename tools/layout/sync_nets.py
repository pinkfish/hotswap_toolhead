"""Give every pad the net the schematic gives it, so pin changes in tools/design.py reach the board.
    sync_nets.py board.kicad_pcb netlist.net
netlist.net is `kicad-cli sch export netlist` output (KiCad s-expression format).
Pads the netlist doesn't mention (mounting holes, NPTH) are left alone.
"""
import re
import sys

import pcbnew

b = pcbnew.LoadBoard(sys.argv[1])
text = open(sys.argv[2]).read()
want = {}
name = ref = None
for line in text[text.index('(nets'):].splitlines():
    m = re.match(r'\s*\((name|ref|pin) "([^"]*)"\)', line)
    if not m:
        continue
    key, val = m.groups()
    if key == 'name':
        name = val
    elif key == 'ref':
        ref = val
    else:
        want[(ref, val)] = name
assert want, 'no nets parsed from ' + sys.argv[2]

nets = {}


def net(name):
    if name not in nets:
        n = b.FindNet(name)
        if n is None:
            n = pcbnew.NETINFO_ITEM(b, name)
            b.Add(n)
        nets[name] = n
    return nets[name]


changed = 0
for f in b.GetFootprints():
    for p in f.Pads():
        name = want.get((f.GetReference(), p.GetNumber()))
        if name is not None and p.GetNetname() != name:
            print('%s.%s: %s -> %s' % (f.GetReference(), p.GetNumber(), p.GetNetname(), name))
            p.SetNet(net(name))
            changed += 1
pcbnew.SaveBoard(sys.argv[1], b)
print('pads re-netted:', changed)
