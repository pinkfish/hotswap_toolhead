# Placement plan for the stack's power board (BW=25, BH=26), read by place.py through PLAN_FILE.
# Board mm from the top-left, seen from the top. The lower board: its top side faces the logic
# board 11 mm above and carries the link header J7, under the logic board's socket J6 contact for
# contact (check_stack.py).
#  - J3 (heater, JST-XH 4) on the bottom edge, plug pointing down: HEAT_N pins 1-2 on the left,
#    +24V pins 3-4 on the right
#  - Q2 over J3's HEAT_N pins, drain down; its gate driver U7 and 12 V rail left of it; the +24V
#    strip from J7's +24V pins down to J3's (stack_power_pre.py); the buck in the top-left corner
#  - notches as on the logic board (plan_logic.py)
W2 = W / 2
ESCAPE = {}   # no MCU here
EDGE_OK = {'J3'}
NOTCHES = [(0, 22.5), (W, 7.0)]
PLAN = {
    'J3': (W2, H - 6.0, 0, 'F', 1),
    # under the logic board's J6 (17.0, 5.6, 90, bottom): its contacts sit 1.27 mm in from the pad
    # rows, pin 1 at (20.81, 4.33), pin 2 below it, pin 3 to its left: the header turned 270
    'J7': (17.0 + 3.81, 5.6 - 1.27, 270, 'F', 1),
    'Q2': (W2 - 2.5, 11.0, 270, 'F', 1),
    'U7': (W2 - 6.6, 11.5, 0, 'F', 0), 'R13': (W2 - 9.0, 9.5, 0, 'F', 0), 'D10': (W2 - 9.0, 11.0, 0, 'F', 0),
    'C21': (W2 - 9.0, 12.5, 0, 'F', 0), 'R14': (W2 - 6.6, 14.2, 0, 'F', 0),
    'C2': (W2 + 6.5, 12.5, 90, 'F', 0),
    # buck in the top-left corner
    # C6 (boot cap) right above U1, across its CB (1) and SW (6) pins
    'L1': (3.0, 3.6, 0, 'F', 0), 'U1': (7.0, 3.8, 0, 'F', 1), 'D9': (3.0, 7.6, 0, 'F', 0),
    # (Q2's GND via rows go above its source pins, x 8.5-12, y 7-9: keep them clear)
    'C8': (10.5, 2.6, 90, 'F', 0), 'C4': (7.0, 6.0, 0, 'F', 0), 'C5': (10.2, 5.4, 0, 'F', 0),
    'C6': (7.0, 1.5, 0, 'F', 1), 'R2': (1.4, 9.8, 90, 'F', 0), 'R3': (2.6, 9.8, 90, 'F', 0),
    'D7': (13.0, 8.0, 90, 'F', 0),
}
