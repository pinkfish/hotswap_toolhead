"""Last DRC clean-up.
    finalize.py in.kicad_pcb drc.json out.kicad_pcb
- pads reported as starved thermals get a solid zone connection
- dangling vias (escape vias the router ended up not using) are removed; their
  stubs stay, since the route usually continues from the via position on that layer
"""
import json
import sys

import pcbnew

src, drcf, dst = sys.argv[1:4]
b = pcbnew.LoadBoard(src)
d = json.load(open(drcf))
starved = set()
dangling = []
for v in d['violations']:
    if v['type'] == 'starved_thermal':
        for i in v['items']:
            if 'pad' in i['description'].lower() and 'Zone' not in i['description']:
                starved.add((round(i['pos']['x'], 3), round(i['pos']['y'], 3)))
    if v['type'] == 'via_dangling':
        i = v['items'][0]
        dangling.append(pcbnew.VECTOR2I(pcbnew.FromMM(i['pos']['x']), pcbnew.FromMM(i['pos']['y'])))
n = 0
for f in b.GetFootprints():
    for p in f.Pads():
        q = p.GetPosition()
        if (round(pcbnew.ToMM(q.x), 3), round(pcbnew.ToMM(q.y), 3)) in starved:
            p.SetLocalZoneConnection(pcbnew.ZONE_CONNECTION_FULL)
            n += 1
            print('solid', f.GetReference(), p.GetNumber())
kill = []
for pos in dangling:
    for v in b.GetTracks():
        if v.GetClass() == 'PCB_VIA' and (v.GetPosition() - pos).EuclideanNorm() < 1000:
            kill.append(v)
print('pads made solid', n, 'removed', len(kill))
for t in kill:
    b.Remove(t)
pcbnew.ZONE_FILLER(b).Fill(b.Zones())
pcbnew.SaveBoard(dst, b)
