"""Silkscreen tidy-up for a dense two-sided board.
    silk.py board.kicad_pcb
- value and other fields off the silkscreen
- references kept on top-side parts (connectors, buttons, LEDs, holes...)
- bottom-side references moved to B.Fab (still on assembly drawings)
"""
import sys

import pcbnew

b = pcbnew.LoadBoard(sys.argv[1])
silk = (pcbnew.F_SilkS, pcbnew.B_SilkS)
moved = kept = 0
for f in b.GetFootprints():
    ref = f.Reference()
    for fld in f.GetFields():
        if fld is ref:
            continue
        if fld.GetLayer() in silk:
            fld.SetVisible(False)
    for g in f.GraphicalItems():
        # extra text items (e.g. %R copies) on silk
        if isinstance(g, pcbnew.PCB_TEXT) and g.GetLayer() in silk:
            g.SetVisible(False)
    if f.IsFlipped():
        ref.SetLayer(pcbnew.B_Fab)
        moved += 1
    else:
        ref.SetLayer(pcbnew.F_SilkS)
        ref.SetTextSize(pcbnew.VECTOR2I(pcbnew.FromMM(0.8), pcbnew.FromMM(0.8)))
        ref.SetTextThickness(pcbnew.FromMM(0.12))
        kept += 1
pcbnew.SaveBoard(sys.argv[1], b)
print('refs kept on top silk', kept, 'moved to B.Fab', moved)
