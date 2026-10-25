"""Place footprints on the floorplan from the design spec.

Run in KiCad's PCB editor: Tools > Scripting Console, then
    exec(open('/path/to/place_footprints.py').read())
Parts in FLOORPLAN go onto the board; the remaining passives are
staged in a grid to the right of the board, grouped by function.
"""
import pcbnew

OX, OY = 100.0, 100.0
PLAN = {
    'C1': (10.0, 4.5, 0, 'F'),
    'C2': (14.5, 16.0, 0, 'F'),
    'C3': (14.5, 13.5, 90, 'F'),
    'C8': (31.5, 17.0, 0, 'F'),
    'D1': (10.5, 17.5, 0, 'F'),
    'D4': (7.5, 16.0, 0, 'F'),
    'D5': (29.0, 6.0, 90, 'F'),
    'D6': (29.0, 16.0, 0, 'F'),
    'F1': (10.5, 21.5, 0, 'F'),
    'F2': (30.5, 2.5, 0, 'F'),
    'J1': (5.0, 19.5, 90, 'F'),
    'J2': (17.5, 2.5, 0, 'F'),
    'J3': (25.0, 2.0, 0, 'F'),
    'J5': (38.5, 4.5, 270, 'F'),
    'JP2': (31.0, 12.0, 0, 'F'),
    'L1': (35.5, 20.5, 0, 'F'),
    'Q1': (15.0, 20.5, 0, 'F'),
    'Q2': (17.5, 7.5, 0, 'F'),
    'Q3': (25.0, 6.5, 0, 'F'),
    'R13': (20.5, 9.5, 0, 'F'),
    'R15': (22.5, 9.0, 0, 'F'),
    'SW1': (40.0, 18.0, 270, 'F'),
    'SW2': (40.0, 21.5, 270, 'F'),
    'U1': (31.5, 20.0, 0, 'F'),
    'U3': (10.0, 11.5, 0, 'F'),
    'U5': (35.5, 4.5, 0, 'F'),
    'U6': (24.0, 15.5, 0, 'F'),
    'Y1': (17.0, 14.5, 90, 'F'),
    'C10': (54.0, 10.0, 0, 'F'),
    'C11': (62.0, 10.0, 0, 'F'),
    'C12': (66.0, 10.0, 0, 'F'),
    'C13': (70.0, 10.0, 0, 'F'),
    'C14': (74.0, 10.0, 0, 'F'),
    'C15': (78.0, 10.0, 0, 'F'),
    'C16': (74.0, 15.0, 0, 'F'),
    'C17': (58.0, 20.0, 0, 'F'),
    'C18': (54.0, 30.0, 0, 'F'),
    'C19': (62.0, 35.0, 0, 'F'),
    'C20': (58.0, 40.0, 0, 'F'),
    'C4': (58.0, 5.0, 0, 'F'),
    'C5': (62.0, 5.0, 0, 'F'),
    'C6': (66.0, 5.0, 0, 'F'),
    'C9': (50.0, 10.0, 0, 'F'),
    'D2': (50.0, 0.0, 0, 'F'),
    'D3': (54.0, 5.0, 0, 'F'),
    'D7': (50.0, 5.0, 0, 'F'),
    'D9': (70.0, 5.0, 0, 'F'),
    'FB1': (58.0, 10.0, 0, 'F'),
    'JP1': (70.0, 15.0, 0, 'F'),
    'LED1': (90.0, 10.0, 0, 'F'),
    'LED2': (98.0, 10.0, 0, 'F'),
    'R1': (54.0, 0.0, 0, 'F'),
    'R10': (62.0, 15.0, 0, 'F'),
    'R11': (66.0, 15.0, 0, 'F'),
    'R12': (78.0, 15.0, 0, 'F'),
    'R14': (50.0, 25.0, 0, 'F'),
    'R16': (50.0, 30.0, 0, 'F'),
    'R17': (50.0, 35.0, 0, 'F'),
    'R18': (54.0, 35.0, 0, 'F'),
    'R19': (58.0, 35.0, 0, 'F'),
    'R2': (74.0, 5.0, 0, 'F'),
    'R20': (50.0, 20.0, 0, 'F'),
    'R21': (54.0, 20.0, 0, 'F'),
    'R22': (50.0, 40.0, 0, 'F'),
    'R23': (54.0, 40.0, 0, 'F'),
    'R3': (78.0, 5.0, 0, 'F'),
    'R4': (82.0, 10.0, 0, 'F'),
    'R5': (86.0, 10.0, 0, 'F'),
    'R6': (94.0, 10.0, 0, 'F'),
    'R7': (50.0, 15.0, 0, 'F'),
    'R8': (54.0, 15.0, 0, 'F'),
    'R9': (58.0, 15.0, 0, 'F'),
}

board = pcbnew.GetBoard()
missing = []
for ref, (x, y, rot, side) in PLAN.items():
    fp = board.FindFootprintByReference(ref)
    if fp is None:
        missing.append(ref)
        continue
    pos = pcbnew.VECTOR2I(pcbnew.FromMM(OX + x), pcbnew.FromMM(OY + y))
    if (side == 'B') != fp.IsFlipped():
        fp.Flip(fp.GetPosition(), False)
    fp.SetPosition(pos)
    fp.SetOrientationDegrees(rot)
pcbnew.Refresh()
print('Placed', len(PLAN) - len(missing), 'footprints; not found:', missing)
