"""JP3 BOM flag to match the symbol; Q2 source pins 1-3 joined by a bar.   misc_pre.py board.kicad_pcb"""
import sys, pcbnew
mm = pcbnew.FromMM
b = pcbnew.LoadBoard(sys.argv[1])
jp1, jp3 = b.FindFootprintByReference('JP1'), b.FindFootprintByReference('JP3')
jp3.SetExcludedFromBOM(jp1.IsExcludedFromBOM())
jp3.SetExcludedFromPosFiles(jp1.IsExcludedFromPosFiles())
ps = {p.GetNumber(): p for p in b.FindFootprintByReference('Q2').Pads()}
t = pcbnew.PCB_TRACK(b); t.SetStart(ps['1'].GetPosition()); t.SetEnd(ps['3'].GetPosition())
t.SetWidth(mm(0.4)); t.SetLayer(pcbnew.F_Cu); t.SetNet(ps['1'].GetNet()); t.SetLocked(True); b.Add(t)
pcbnew.SaveBoard(sys.argv[1], b)
print('misc pre done')
