"""undangle.py board.kicad_pcb - delete track stubs with a dangling end, and the near-zero-length
scraps Freerouting's session import leaves (under 0.02 mm), repeatedly, then refill.
A stub whose removal would open a connection stays: KiCad calls some tracks dangling that DRC
still counts as joined (an end just off a pad's centre, a via part-way along a track)."""
import sys, pcbnew
b = pcbnew.LoadBoard(sys.argv[1]); n = 0; keep = set()


def opened():
    b.BuildConnectivity()
    return b.GetConnectivity().GetUnconnectedCount(False)


while True:
    base = opened(); c = b.GetConnectivity()
    dead = [t for t in b.GetTracks() if t.GetClass() == 'PCB_TRACK' and t.m_Uuid.AsString() not in keep
            and (c.TestTrackEndpointDangling(t, False) or t.GetLength() < pcbnew.FromMM(0.02))]
    if not dead: break
    for t in dead:
        copy = pcbnew.Cast_to_PCB_TRACK(t.Duplicate())   # re-adding a removed track crashes
        name, length = t.GetNetname(), round(pcbnew.ToMM(t.GetLength()), 3)
        b.Delete(t)
        if opened() > base:
            b.Add(copy); keep.add(copy.m_Uuid.AsString())
            continue
        print('removed', name, length); n += 1
pcbnew.ZONE_FILLER(b).Fill(b.Zones())
pcbnew.SaveBoard(sys.argv[1], b)
print('dangling tracks removed', n, 'kept', len(keep))
