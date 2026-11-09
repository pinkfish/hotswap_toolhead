# Placement plan for the board with the vertical XT30 and USB-C (BW=27, BH=36 - SHIFT), read by
# place.py through PLAN_FILE. blocks_vertical.py has moved the rest of the 27 x 36 board up with
# its copper (kept here, x None). Board mm from the top-left, seen from the top.
#  - J1 in the top-left corner turned 180 degrees, so its pins sit where the right-angle XT30's
#    did, 6 mm higher: CAN pins left, GND, + pin right; J5 in the top-right corner, its body
#    2.8 mm from J1's so a USB-C plug's overmould (12.35 mm wide at most) clears the XT30 plug
#  - bottom: Q1 under J1's GND pin, below the pins, the TVS below it; the fuse right of the +
#    pin, above U6; the CAN ESD clamp below J1's CAN pins, the gate zener and resistor below it;
#    under J5 the VBUS cap between the shell legs, the CC pull-downs below it, U5 below them, by
#    U6's USB pins, and the USB-to-buck diode right of U5
K = (None, None, None, None, 1)
PLAN = {r: K for r in (
    'U6', 'Y1', 'C9', 'C11', 'C12', 'C13', 'C14', 'C15', 'FB1', 'JP3', 'R4', 'U3', 'C16', 'R11',
    'JP1', 'R2', 'R3', 'D7', 'U1', 'C6', 'C4', 'C5', 'L1', 'D9', 'J2', 'D6', 'D5', 'F2', 'H1', 'H2',
    'C1', 'C2', 'C3', 'C8', 'C10', 'C19', 'C20', 'C21', 'D10', 'JP2', 'LED1', 'LED2', 'Q2', 'Q3',
    'R5', 'R6', 'R13', 'R14', 'R15', 'R16', 'R17', 'R18', 'R19', 'R22', 'R23', 'SW1', 'U7')}
PLAN.update({
    'J1': (7.9, 2.9, 180, 'F', 1),
    'J5': (22.4, 3.3, 180, 'F', 1),
    'Q1': (7.58, 7.75, 0, 'B', 1), 'D1': (9.0, 11.85, 0, 'B', 1),
    'F1': (15.3, 2.6, 90, 'B', 1),
    'D4': (1.95, 6.95, 90, 'B', 1), 'D2': (1.6, 11.6, 90, 'B', 1), 'R1': (3.4, 10.5, 90, 'B', 1),
    'C17': (22.4, 2.4, 90, 'B', 1), 'R20': (21.7, 5.35, 90, 'B', 1), 'R21': (23.1, 5.35, 90, 'B', 1),
    'U5': (21.72, 8.5, 90, 'B', 1), 'D3': (25.35, 8.4, 90, 'B', 0),
})
