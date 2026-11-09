"""JP3 BOM flag to match the symbol; Q2 source pins 1-3 joined by a bar and connected solid to
the GND pours (they carry the 3 A heater return). Each only where the board has the part (the
logic board has JP1/JP3, the power board Q2).   misc_pre.py board.kicad_pcb"""
import sys, pcbnew
mm = pcbnew.FromMM
b = pcbnew.LoadBoard(sys.argv[1])
jp1, jp3 = b.FindFootprintByReference('JP1'), b.FindFootprintByReference('JP3')
if jp1 and jp3:
    jp3.SetExcludedFromBOM(jp1.IsExcludedFromBOM())
    jp3.SetExcludedFromPosFiles(jp1.IsExcludedFromPosFiles())
q2 = b.FindFootprintByReference('Q2')
if q2:
    ps = {p.GetNumber(): p for p in q2.Pads()}
    t = pcbnew.PCB_TRACK(b); t.SetStart(ps['1'].GetPosition()); t.SetEnd(ps['3'].GetPosition())
    t.SetWidth(mm(0.4)); t.SetLayer(b.GetLayerID('B.Cu') if q2.IsFlipped() else pcbnew.F_Cu)
    t.SetNet(ps['1'].GetNet()); t.SetLocked(True); b.Add(t)
    for n in '123':
        ps[n].SetLocalZoneConnection(pcbnew.ZONE_CONNECTION_FULL)
pcbnew.SaveBoard(sys.argv[1], b)
print('misc pre done')
