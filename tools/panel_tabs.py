"""panel_tabs.py in.kicad_pcb out.kicad_pcb - add KiKit tab annotations where both neighbours are clear.
Top/bottom edges carry J1/J5 and J2 overhangs, so the tabs sit in the only windows
free on both sides of each gap: x 15.6-17.9 (top and bottom) and y 20.0-22.5 (left and right, bite holes kept off J1, D6 and JP3)."""
import sys, pcbnew
mm = pcbnew.FromMM; O = 100.0
import kikit, os
LIB = os.path.join(os.path.dirname(kikit.__file__), 'resources', 'kikit.pretty')
b = pcbnew.LoadBoard(sys.argv[1])
TABS = [  # origin 0.5 mm outside the edge (KiKit grows the tab from there), orientation points into the board, width
    ('KT1', 16.95, -0.5, 270, 1.6),    # top
    ('KT2', 16.95, 35.5, 90, 1.6),    # bottom
    ('KT3', -0.5, 21.3, 0, 2.0),      # left
    ('KT4', 31.5, 21.3, 180, 2.0),   # right
]
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
