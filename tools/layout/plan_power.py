# Placement plan for the power board (BW=27, BH=H), read by place.py through PLAN_FILE.
# Board mm from the top-left, seen from the top. The power board is the lower board of the
# stack: its top side faces the logic board (11 mm above) and carries the link header J4, the
# load plug J2 and the FETs; the buck and the small parts go underneath.
#  - J4 at the contact positions of the logic board's socket J3 (pin 1 at the top left, odd
#    pins in the left column); tools/check_stack.py checks they line up
#  - J2 centred on the bottom edge, plug pointing down, as on the single board
#  - the heater FET right of J2 by its HEAT_N pin (5), the fan FET and its PTC above J2
ESCAPE = {}
PLAN = {
    'H1': (3.2, H - 3.4, 0, 'F', 1), 'H2': (23.5, H - 3.5, 0, 'F', 1),
    'J4': (21.03, 2.25, 0, 'F', 1),
    'J2': (16.85, H - 11.1, -90, 'F', 1),       # 0.35 mm left of centre, clear of J4's courtyard
    # heater: FET right of J2 under the header, gate driver and its 12 V rail above it
    'Q2': (22.4, H - 8.4, 0, 'F', 0),
    'U7': (16.5, H - 14.5, None, 'F', 0), 'R14': (18.5, H - 15.5, None, 'F', 0),
    'D10': (14.0, H - 15.5, None, 'F', 0), 'C21': (14.0, H - 17.0, None, 'F', 0), 'R13': (12.5, H - 16.0, None, 'F', 0),
    # fan: PTC feeding J2 pin 2 from above, FET and gate parts beside it
    'F2': (11.5, H - 14.0, 0, 'F', 0), 'Q3': (6.0, H - 12.5, None, 'F', 0),
    'R15': (4.0, H - 14.0, None, 'F', 0), 'R16': (4.0, H - 15.5, None, 'F', 0),
    'C2': (16.5, H - 20.0, None, 'F', 0), 'C3': (5.0, H - 18.0, None, 'F', 0),
    # bottom: the buck, the fan flyback diode under J2's fan pins
    'D5': (14.75, H - 6.5, None, 'B', 0),
    'D7': (5.0, 3.0, None, 'B', 0), 'U1': (8.0, 7.0, None, 'B', 0), 'C4': (4.0, 7.5, None, 'B', 0),
    'C5': (8.0, 4.0, None, 'B', 0), 'C6': (10.5, 7.0, None, 'B', 0), 'D9': (11.0, 10.5, None, 'B', 0),
    'L1': (15.0, 8.0, None, 'B', 0), 'C8': (16.0, 3.0, None, 'B', 0),
    'R2': (12.0, 4.0, None, 'B', 0), 'R3': (12.0, 2.5, None, 'B', 0),
}
