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
    'C16': (6.95, 18.2, 90, 'B'),
    'C17': (25, 3, 0, 'B'),
    'C18': (6.3, 33.4, 0, 'B'),
    'C19': (17.2, 31, 90, 'B'),
    'C2': (25.5, 23.5, 0, 'B'),
    'C20': (4.4, 21.3, 90, 'B'),
    'C3': (25.5, 26.25, 0, 'B'),
    'C4': (20.75, 12.3, 0, 'B'),
    'C5': (17.5, 9.4, 90, 'B'),
    'C6': (13.2, 14.25, 90, 'B'),
    'C8': (25, 20, 0, 'B'),
    'C9': (17.6, 26.23, 270, 'B'),
    'D1': (18, 4.6, 90, 'B'),
    'D2': (3.45, 2.75, 0, 'B'),
    'D3': (25.4, 11, 0, 'B'),
    'D4': (9, 14.8, 90, 'B'),
    'D5': (1.8, 30, 90, 'B'),
    'D6': (19.85, 32.8, 180, 'B'),
    'D7': (20.6, 9.4, 0, 'B'),
    'D9': (20.6, 14.85, 0, 'B'),
    'F1': (14.7, 4.6, 90, 'B'),
    'F2': (6.15, 30.3, 0, 'B'),
    'FB1': (20.66, 26.28, 90, 'B'),
    'J1': (8.4, 7.27, 180, 'F'),
    'J2': (10.6, 23.9, 270, 'F'),
    'J5': (25, 3.65, 180, 'F'),
    'JP1': (9.6, 16.6, 90, 'F'),
    'JP2': (20, 32, 0, 'F'),
    'JP3': (29.6, 18.3, 90, 'F'),
    'L1': (25.2, 15.9, 0, 'B'),
    'LED1': (24, 11, 0, 'F'),
    'LED2': (24, 13, 0, 'F'),
    'Q1': (9.7, 3.9, 0, 'B'),
    'Q2': (15.4, 27.6, 180, 'F'),
    'Q3': (13.6, 31.45, 90, 'B'),
    'R1': (1.5, 6, 90, 'B'),
    'R10': (10.65, 11.7, 90, 'B'),
    'R11': (9.6, 12.95, 90, 'F'),
    'R12': (6.95, 20.6, 90, 'B'),
    'R13': (19.4, 26.2, 180, 'F'),
    'R14': (19.4, 27.5, 0, 'F'),
    'R15': (10.5, 29, 90, 'B'),
    'R16': (10.5, 31, 90, 'B'),
    'R17': (22.35, 27.35, 90, 'B'),
    'R18': (23.8, 28.6, 90, 'B'),
    'R19': (16, 31, 90, 'B'),
    'R2': (12.75, 11.25, 0, 'B'),
    'R20': (27.9, 4.5, 90, 'B'),
    'R21': (22.1, 4.5, 90, 'B'),
    'R22': (1.6, 21.3, 90, 'B'),
    'R23': (3, 21.3, 90, 'B'),
    'R3': (12.75, 12.5, 0, 'B'),
    'R4': (28.6, 18.3, 90, 'B'),
    'R5': (28.3, 10.6, 90, 'B'),
    'R6': (28.3, 15.15, 90, 'B'),
    'R7': (6.9, 11.7, 90, 'B'),
    'R8': (9.4, 11.7, 90, 'B'),
    'R9': (8.15, 11.7, 90, 'B'),
    'SW1': (29, 13.4, 90, 'F'),
    'U1': (16.2, 12.9, 0, 'B'),
    'U3': (10, 18.9, 0, 'B'),
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
