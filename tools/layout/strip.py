"""Copy a board with its tracks, vias and zones removed and pad zone connections reset,
as the starting point for run_layout.sh.   strip.py in.kicad_pcb out.kicad_pcb"""
import sys

import pcbnew

b = pcbnew.LoadBoard(sys.argv[1])
for f in b.GetFootprints():
    for p in f.Pads():
        p.SetLocalZoneConnection(pcbnew.ZONE_CONNECTION_INHERITED)
for t in list(b.GetTracks()):
    b.Remove(t)
for z in list(b.Zones()):
    b.Remove(z)
pcbnew.SaveBoard(sys.argv[2], b)
print('stripped', sys.argv[2])
