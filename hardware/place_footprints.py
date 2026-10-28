"""Place footprints on the floorplan from the design spec.

Run in KiCad's PCB editor: Tools > Scripting Console, then
    exec(open('/path/to/place_footprints.py').read())
Parts in FLOORPLAN go onto the board; the remaining passives are
staged in a grid to the right of the board, grouped by function.
"""
import pcbnew

OX, OY = 100.0, 100.0
PLAN = {
    'C1': (17.6, 14.6, 0, 'F'),
    'C10': (20.1, 29.65, 0, 'B'),
    'C11': (18.62, 26.28, 270, 'B'),
    'C12': (19.64, 26.28, 270, 'B'),
    'C13': (17.6, 28.6, 270, 'B'),
    'C14': (12.8, 28.2, 90, 'B'),
    'C15': (12.65, 25.4, 270, 'B'),
    'C16': (6.95, 18.2, 270, 'B'),
    'C17': (25, 3, 0, 'B'),
    'C19': (17.2, 30.6, 90, 'B'),
    'C2': (24.8, 21.2, 0, 'F'),
    'C20': (5.6, 19.95, 0, 'F'),
    'C3': (24.8, 23.7, 0, 'F'),
    'C4': (20.75, 12.3, 0, 'B'),
    'C5': (17.5, 9.4, 90, 'B'),
    'C6': (13.2, 14.25, 90, 'B'),
    'C8': (25.05, 18.6, 0, 'F'),
    'C9': (17.6, 26.23, 270, 'B'),
    'D1': (18, 4.6, 90, 'B'),
    'D2': (3.45, 2.75, 0, 'B'),
    'D3': (25.4, 11, 0, 'B'),
    'D4': (9, 14.3, 90, 'B'),
    'D5': (1.5, 28.2, 90, 'B'),
    'D6': (28.9, 22.9, 270, 'F'),
    'D7': (20.6, 9.4, 0, 'B'),
    'D9': (20.6, 14.85, 0, 'B'),
    'F1': (14.7, 4.6, 90, 'B'),
    'F2': (5.85, 28.1, 0, 'B'),
    'FB1': (20.66, 26.28, 90, 'B'),
    'J1': (8.4, 7.27, 180, 'F'),
    'J2': (10.6, 21.9, 270, 'F'),
    'J5': (25, 3.65, 180, 'F'),
    'JP1': (9.6, 16.6, 90, 'F'),
    'JP2': (20, 30, 0, 'F'),
    'JP3': (29.6, 18.3, 90, 'F'),
    'L1': (25.2, 15.9, 0, 'B'),
    'LED1': (24, 11, 0, 'F'),
    'LED2': (24, 13, 0, 'F'),
    'Q1': (9.7, 3.9, 0, 'B'),
    'Q2': (15.1, 25.75, 180, 'F'),
    'Q3': (14.65, 30.1, 90, 'F'),
    'R1': (1.5, 6, 90, 'B'),
    'R11': (9.6, 12.95, 90, 'F'),
    'R13': (18, 23.4, 90, 'F'),
    'R14': (19.2, 23.4, 90, 'F'),
    'R15': (10.3, 26.7, 0, 'B'),
    'R16': (8.35, 31.6, 0, 'B'),
    'R17': (21.6, 26.9, 90, 'F'),
    'R18': (22.8, 26.9, 90, 'F'),
    'R19': (16, 30.6, 90, 'B'),
    'R2': (12.75, 11.25, 0, 'B'),
    'R20': (27.9, 4.5, 90, 'B'),
    'R21': (22.1, 4.5, 90, 'B'),
    'R22': (1.4, 19.95, 0, 'F'),
    'R23': (3.5, 19.95, 0, 'F'),
    'R3': (12.75, 12.5, 0, 'B'),
    'R4': (28.6, 18.3, 90, 'B'),
    'R5': (28.3, 10.6, 90, 'B'),
    'R6': (28.3, 15.15, 90, 'B'),
    'SW1': (29, 13.4, 90, 'F'),
    'U1': (16.2, 12.9, 0, 'B'),
    'U3': (10, 18.2, 0, 'B'),
    'U5': (25, 7.2, 90, 'B'),
    'U6': (17.5, 20.4, 90, 'B'),
    'Y1': (15.2, 27.2, 270, 'B'),
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
