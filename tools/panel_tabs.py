"""panel_tabs.py in.kicad_pcb out.kicad_pcb - add KiKit tab annotations where both neighbours are clear.
J1 and J5 fill the top edge and J2 (centred, overhanging) the bottom, so no top/bottom window is
clear on both sides of a row gap: the boards are held by side tabs only, two per side, in the
windows clear on both neighbours: y 9.0-10.6 (between J5 and SW1 on the right) and
y 23.2-29.5 (between C4 and H2 on the right, below R22 on the left)."""
import sys, pcbnew
mm = pcbnew.FromMM; O = 100.0
import kikit, os
LIB = os.path.join(os.path.dirname(kikit.__file__), 'resources', 'kikit.pretty')
b = pcbnew.LoadBoard(sys.argv[1])
edges = [d for d in b.GetDrawings() if d.GetLayer() == pcbnew.Edge_Cuts]   # outline geometry, not its line width
W = max(max(d.GetStart().x, d.GetEnd().x) for d in edges) / 1e6 - O
H = max(max(d.GetStart().y, d.GetEnd().y) for d in edges) / 1e6 - O
TABS = [  # origin 0.5 mm outside the edge (KiKit grows the tab from there), orientation points into the board, width
    ('KT1', -0.5, 9.8, 0, 1.4),         # left
    ('KT2', -0.5, 26.3, 0, 2.5),
    ('KT3', W + 0.5, 9.8, 180, 1.4),    # right
    ('KT4', W + 0.5, 26.3, 180, 2.5),
]
print('board %g x %g mm' % (W, H))
for ref, x, y, rot, w in TABS:
    f = pcbnew.FootprintLoad(LIB, 'Tab')
    f.SetFPID(pcbnew.LIB_ID('kikit', 'Tab'))
    f.SetReference(ref)
    for t in f.GraphicalItems():
        if isinstance(t, pcbnew.PCB_TEXT) and t.GetText().startswith('KIKIT:'):
            t.SetText('KIKIT: width: %gmm' % w)
    f.SetPosition(pcbnew.VECTOR2I(mm(O + x), mm(O + y)))
    f.SetOrientationDegrees(rot)
    b.Add(f)
pcbnew.SaveBoard(sys.argv[2], b)
