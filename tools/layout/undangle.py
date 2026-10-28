"""undangle.py board.kicad_pcb - delete track stubs with a dangling end, repeatedly, then refill."""
import sys, pcbnew
b = pcbnew.LoadBoard(sys.argv[1]); n = 0
while True:
    b.BuildConnectivity(); c = b.GetConnectivity()
    dead = [t for t in b.GetTracks() if t.GetClass() == 'PCB_TRACK' and c.TestTrackEndpointDangling(t, False)]
    if not dead: break
    for t in dead:
        print('removed', t.GetNetname(), round(pcbnew.ToMM(t.GetLength()), 3))
        b.Delete(t); n += 1
pcbnew.ZONE_FILLER(b).Fill(b.Zones())
pcbnew.SaveBoard(sys.argv[1], b)
print('dangling tracks removed', n)
