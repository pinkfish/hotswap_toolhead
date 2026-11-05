"""Remove moved block copper that conflicts with the new placement.
    declash.py board.kicad_pcb drc.json
Every track or via that DRC reports in a clash (short, clearance, hole clearance, crossing,
keep-out, board edge) is removed, and then any piece of copper left touching no pad (blocks.py's
runs: tracks and vias joined end to end). What still hangs off a pad, like a pin escape whose far
end clashed, stays for the router to carry on from. In a clash between narrow_pre.py's
pre-routes (its group, GROUP) and other tracks or vias, only the other ones go.
"""
import json
import sys

import pcbnew

from blocks import runs

CLASH = {'shorting_items', 'clearance', 'hole_clearance', 'tracks_crossing', 'items_not_allowed',
         'copper_edge_clearance', 'solder_mask_bridge', 'hole_to_hole', 'via_diameter'}
pcb, drcf = sys.argv[1:3]
d = json.load(open(drcf))
b = pcbnew.LoadBoard(pcb)
GROUP = 'narrow pre-routes'
copper = {t.m_Uuid.AsString() for t in b.GetTracks()}
pre = {i.m_Uuid.AsString() for g in b.Groups() if g.GetName() == GROUP for i in g.GetItems()}
bad = set()
for v in d['violations']:
    if v['type'] in CLASH:
        ids = {i['uuid'] for i in v['items']} & copper
        bad |= ids - pre if ids - pre and ids & pre else ids
kill = [t for t in b.GetTracks() if t.m_Uuid.AsString() in bad]
gone = {t.m_Uuid.AsString() for t in kill}
kill += [t for items, refs in runs(b, gone) if not refs for t in items]
for g in [g for g in b.Groups() if g.GetName() == GROUP]:
    g.RemoveAll()
    b.Remove(g)
for t in kill:
    b.Remove(t)
pcbnew.SaveBoard(pcb, b)
print('declash: removed', len(kill), 'tracks and vias')
