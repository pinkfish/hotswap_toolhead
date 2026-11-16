"""pour_clear.py board.kicad_pcb - take other nets' copper out of the power pours.
Freerouting treats a pre-route pour (a zone named '... pour', can_pre.py) as a plane it may
cross, so its tracks and vias of other nets can cut the pour in two. This removes every
unlocked track or via of another net that comes within the clearance of a pour on its layer
(a via on any layer); the maze loop then reroutes those connections round the pours, which
maze.py treats as obstacles.
"""
import sys

import pcbnew

mm = pcbnew.FromMM
b = pcbnew.LoadBoard(sys.argv[1])
CLR = 0.3
pours = [z for z in b.Zones() if not z.GetIsRuleArea() and z.GetZoneName().endswith(' pour')]
kill = []
for t in b.GetTracks():
    if t.IsLocked():
        continue
    via = t.GetClass() == 'PCB_VIA'
    for z in pours:
        if z.GetNetname() == t.GetNetname() or not (via or t.GetLayer() == z.GetLayer()):
            continue
        if via:
            hit = z.Outline().Collide(t.GetPosition(), mm(CLR) + t.GetWidth(z.GetLayer()) // 2)
        else:
            hit = z.Outline().Collide(pcbnew.SEG(t.GetStart(), t.GetEnd()), mm(CLR) + t.GetWidth() // 2)
        if hit:
            kill.append(t)
            break
for t in kill:
    b.Remove(t)
pcbnew.ZONE_FILLER(b).Fill(b.Zones())
pcbnew.SaveBoard(sys.argv[1], b)
print('pour_clear: removed', len(kill), 'tracks and vias from the power pours')
