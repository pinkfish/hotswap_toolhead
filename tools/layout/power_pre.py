"""High-current copper that the autorouter must not touch.
    power_pre.py board.kicad_pcb            (before routing)
    power_pre.py board.kicad_pcb --post     (after routing)
Before routing: B.Cu +24V pour on Q1's source pins with a via array to the In2
+24V plane, and rule areas reserving room for the VIN_RAW and VIN_F pours.
After routing (--post): those rule areas become the VIN_RAW / VIN_F pours.
"""
import sys

import pcbnew

mm = pcbnew.FromMM
path = sys.argv[1]
post = '--post' in sys.argv
b = pcbnew.LoadBoard(path)
O = 100.0
B = pcbnew.B_Cu
# net: outline (board mm) of the bottom-side pours
POURS = {
    # J1 pin 1 to F1 pad 1, stepping down past Q1's drain pins
    '/VIN_RAW': [(13.4, 5.0), (15.9, 5.0), (15.9, 10.4), (11.4, 10.4), (11.4, 6.6), (13.4, 6.6)],
    # F1 pad 2 to Q1's drain, with a branch round D1's GND pad to D1 pad 1
    '/VIN_F': [(8.4, 0.6), (16.8, 0.6), (16.8, 4.9), (18.9, 4.9), (18.9, 7.6), (16.2, 7.6),
               (16.2, 4.7), (8.4, 4.7)],
    '/+24V': [(5.2, 2.95), (7.7, 2.95), (7.7, 7.0), (5.2, 7.0)],
}
PLANE_VIAS = {'/+24V': [(5.75, 4.4), (5.75, 5.5), (5.6, 6.55), (6.7, 6.55)]}


def P(x, y):
    return pcbnew.VECTOR2I(mm(O + x), mm(O + y))


def outline(z, pts):
    o = z.Outline()
    o.NewOutline()
    for x, y in pts:
        o.Append(mm(O + x), mm(O + y))


def pour(net, pts):
    z = pcbnew.ZONE(b)
    z.SetLayer(B)
    z.SetNet(b.FindNet(net))
    z.SetAssignedPriority(3)
    z.SetLocalClearance(mm(0.3))
    z.SetMinThickness(mm(0.25))
    z.SetPadConnection(pcbnew.ZONE_CONNECTION_FULL)
    z.SetIslandRemovalMode(pcbnew.ISLAND_REMOVAL_MODE_ALWAYS)
    z.SetZoneName(net.strip('/') + ' pour')
    outline(z, pts)
    b.Add(z)


if not post:
    # +24V pour is placed now (the router never needs that corner)
    pour('/+24V', POURS['/+24V'])
    have = [t.GetPosition() for t in b.GetTracks() if t.GetClass() == 'PCB_VIA']
    for net, pts in PLANE_VIAS.items():
        for x, y in pts:
            # a fanout via may already sit here
            if any((h - P(x, y)).EuclideanNorm() < mm(0.9) for h in have):
                continue
            v = pcbnew.PCB_VIA(b)
            v.SetPosition(P(x, y))
            v.SetWidth(mm(0.6))
            v.SetDrill(mm(0.3))
            v.SetNet(b.FindNet(net))
            v.SetLocked(True)
            b.Add(v)
    # reserve the VIN pours
    for net in ('/VIN_RAW', '/VIN_F'):
        z = pcbnew.ZONE(b)
        z.SetIsRuleArea(True)
        ls = pcbnew.LSET()
        ls.AddLayer(B)
        z.SetLayerSet(ls)
        z.SetDoNotAllowTracks(True)
        z.SetDoNotAllowVias(True)
        z.SetDoNotAllowZoneFills(False)
        z.SetDoNotAllowPads(False)
        z.SetDoNotAllowFootprints(False)
        z.SetZoneName(net.strip('/') + ' reserved')
        outline(z, POURS[net])
        b.Add(z)
else:
    stale = [z for z in b.Zones() if z.GetIsRuleArea() and z.GetZoneName().endswith(' reserved')]
    for z in stale:
        b.Remove(z)
    pcbnew.SaveBoard(path, b)
    b = pcbnew.LoadBoard(path)
    for net in ('/VIN_RAW', '/VIN_F'):
        pour(net, POURS[net])
    # tracks the router drew for these nets inside the pours are redundant but harmless
pcbnew.ZONE_FILLER(b).Fill(b.Zones())
pcbnew.SaveBoard(path, b)
print('power', 'post' if post else 'pre', 'done')
