"""Place footprints on the floorplan from the design spec.

Run in KiCad's PCB editor: Tools > Scripting Console, then
    exec(open('/path/to/place_footprints.py').read())
Parts in FLOORPLAN go onto the board; the remaining passives are
staged in a grid to the right of the board, grouped by function.
"""
import pcbnew

OX, OY = 100.0, 100.0
PLAN = {
    'C1': (15.75, 15.9, 0, 'F'),
    'C10': (4, 31, 0, 'B'),
    'C11': (19.92, 19.98, -90, 'B'),
    'C12': (20.94, 19.98, -90, 'B'),
    'C13': (18.9, 22.3, -90, 'B'),
    'C14': (14.1, 21.9, 90, 'B'),
    'C15': (13.95, 19.1, -90, 'B'),
    'C16': (9.9, 20.7, 0, 'B'),
    'C17': (25, 3, 0, 'B'),
    'C19': (11, 22.4, 180, 'B'),
    'C2': (24.8, 21.35, 0, 'F'),
    'C20': (5.6, 19.95, 0, 'F'),
    'C3': (6.6, 28.8, 0, 'F'),
    'C4': (29.3, 20.9, 90, 'B'),
    'C5': (26.4, 23.2, 180, 'B'),
    'C6': (23.6, 20.3, -90, 'B'),
    'C8': (24.8, 18.6, 0, 'F'),
    'C9': (18.9, 19.93, -90, 'B'),
    'D1': (18, 4.6, 90, 'B'),
    'D2': (3.45, 2.75, 0, 'B'),
    'D3': (25.4, 11, 180, 'B'),
    'D4': (9, 14.3, 90, 'B'),
    'D5': (16.75, 31.1, 90, 'B'),
    'D6': (11.8, 21.5, 0, 'F'),
    'D7': (26.4, 16.45, 180, 'B'),
    'D9': (23, 31.5, -90, 'B'),
    'F1': (14.7, 4.6, 90, 'B'),
    'F2': (17.4, 21.5, 0, 'F'),
    'FB1': (21.96, 19.98, 90, 'B'),
    'J1': (8.4, 7.27, 180, 'F'),
    'J2': (19.25, 24.9, -90, 'F'),
    'J5': (25, 3.65, 180, 'F'),
    'JP1': (9.6, 16.6, 90, 'F'),
    'JP2': (4.8, 33, 0, 'F'),
    'JP3': (21.2, 11.9, 0, 'F'),
    'L1': (25.6, 26.8, 0, 'B'),
    'LED1': (24.55, 11, 0, 'F'),
    'LED2': (24.55, 13, 0, 'F'),
    'Q1': (9.7, 3.9, 0, 'B'),
    'Q2': (24.2, 26.4, 180, 'F'),
    'Q3': (7.2, 24.6, 0, 'F'),
    'R1': (1.5, 6, 90, 'B'),
    'R11': (9.6, 12.95, 90, 'F'),
    'R13': (27.6, 26, 90, 'F'),
    'R14': (27.6, 28.2, 90, 'F'),
    'R15': (3.5, 23.4, 0, 'F'),
    'R16': (3.5, 24.8, 0, 'F'),
    'R17': (9.4, 23.6, 0, 'B'),
    'R18': (2, 28.6, 90, 'F'),
    'R19': (12.65, 22.6, 90, 'B'),
    'R2': (25.9, 13.3, 0, 'B'),
    'R20': (27.9, 4.5, 90, 'B'),
    'R21': (22.1, 4.5, 90, 'B'),
    'R22': (1.4, 19.95, 0, 'F'),
    'R23': (3.5, 19.95, 0, 'F'),
    'R3': (25.9, 14.4, 180, 'B'),
    'R4': (21.85, 14.2, -90, 'F'),
    'R5': (26.7, 10.9, 90, 'F'),
    'R6': (26.7, 13.5, 90, 'F'),
    'SW1': (29, 13.4, 90, 'F'),
    'U1': (25.9, 20.3, -90, 'B'),
    'U3': (9.05, 18.2, 180, 'B'),
    'U5': (25, 7.2, 90, 'B'),
    'U6': (18.8, 14.1, 90, 'B'),
    'Y1': (16.5, 20.9, -90, 'B'),
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
