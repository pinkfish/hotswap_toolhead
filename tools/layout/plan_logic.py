# Placement plan for the stack's logic board (BW=25, BH=26), read by place.py through PLAN_FILE.
# Board mm from the top-left, seen from the top. The upper board: its top side faces out, its
# bottom side faces the power board 11 mm below and carries the link socket J6.
#  - top: J1 (24 V + CAN, JST-XH 6) across the top edge, plug pointing up, +24V pins on the right;
#    J2 (fan, thermistor, switch, SH 6) centred on the bottom edge, plug pointing down; J5 (USB,
#    SH 4) on the left edge. F1 under J1's +24V pins and the fan's PTC (F2) beside it, both in the
#    +24V pour; the fan FET and the LEDs with their resistors in the middle
#  - bottom: U6 with its crystal corner below it (U6_AT); CAN under J1's CAN pins; J6 under J1's
#    right half, clear of the right notch; the USB ESD down the left; C1 under the +24V pour; the
#    thermistor and switch filters right of U6; RESET (side-push) low on the right edge, its
#    pegs clear of the top side's parts
#  - notches: the same on both boards (plan_power.py), right edge high and left edge low
W2 = W / 2
ESCAPE = {'U6': (0.4, 0.4, 0.4, 0.4)}
EDGE_OK = {'J1', 'J2', 'J5', 'SW1'}
NOTCHES = [(0, 22.5), (W, 7.0)]
PLAN = {
    'J1': (W2, 6.0, 180, 'F', 1),
    # 2.5 mm right of centre: its pads clear the MCU corner's +3V3 vias (VBAT/VDD) underneath
    'J2': (W2 + 2.5, H - 3.3, 0, 'F', 1),
    'J5': (3.3, 16.0, 270, 'F', 1),
    'J6': (17.0, 5.6, 90, 'B', 1),
    'SW1': (W - 2.0, 21.6, 90, 'B', 1),
    'U6': (None, None, None, 'B', 1),
    'Y1': (None, None, None, 'B', 1), 'C13': (None, None, None, 'B', 1), 'C14': (None, None, None, 'B', 1),
    'C9': (None, None, None, 'B', 1), 'C11': (None, None, None, 'B', 1), 'C12': (None, None, None, 'B', 1),
    'FB1': (None, None, None, 'B', 1), 'C15': (None, None, None, 'B', 1),
    # ---- top: power input under J1's +24V pins (stack_logic_pre.py pours from these pads)
    # D1's +24V pad (1) up under F1's output pad and F2's (1) at the top, into the +24V pour;
    # C1 underneath (bottom, below) with its +24V pad (1) up into the bottom pour
    'F1': (W2 + 5.0, 13.4, 0, 'F', 1), 'D1': (W2 + 5.0, 15.9, 180, 'F', 1),
    'F2': (W - 3.0, 17.0, 270, 'F', 1), 'C1': (W - 3.0, 15.8, 270, 'B', 1),
    # fan FET, flyback and gate resistors, and the LEDs with their resistors, in the middle
    'Q3': (W2 - 1.0, 17.5, 0, 'F', 0), 'D5': (W2 - 4.5, 17.8, 0, 'F', 0),
    'R15': (W2 + 1.6, 17.5, 90, 'F', 0), 'R16': (W2 + 2.8, 17.5, 90, 'F', 0),
    'LED1': (W2 - 4.0, 13.0, 0, 'F', 0), 'LED2': (W2 - 4.0, 14.4, 0, 'F', 0),
    'R5': (W2 - 1.2, 13.0, 0, 'F', 0), 'R6': (W2 - 1.2, 14.4, 0, 'F', 0),
    # ---- bottom
    'U3': (6.0, 5.0, 0, 'B', 0), 'D4': (2.6, 8.4, 0, 'B', 0), 'R11': (9.5, 8.8, 0, 'B', 0),
    'JP1': (2.4, 3.6, 90, 'B', 0), 'C16': (9.5, 3.0, 0, 'B', 0),
    'U5': (2.2, 14.0, 90, 'B', 0), 'C17': (2.4, 17.6, 90, 'B', 0), 'D3': (2.6, 20.0, 0, 'B', 0),
    # (the +24V via array is under F1 and C1, x 20-22.4, y 10.3-14: keep it clear)
    'JP3': (W - 9.5, 16.0, 0, 'B', 0), 'R4': (W - 9.5, 14.4, 0, 'B', 0), 'C10': (W - 7.4, 12.6, 90, 'B', 0),
    'R17': (W - 7.5, 17.0, 0, 'B', 0), 'R18': (W - 7.5, 18.2, 0, 'B', 0), 'JP2': (W - 9.5, 20.6, 90, 'B', 0),
    'R19': (W - 5.0, 17.0, 0, 'B', 0), 'C19': (W - 5.0, 18.2, 0, 'B', 0), 'D6': (W - 6.0, 21.0, 0, 'B', 0),
    'R22': (W - 7.5, 23.6, 0, 'B', 0), 'R23': (W - 7.5, 24.8, 0, 'B', 0), 'C20': (W - 10.0, 24.2, 90, 'B', 0),
}
