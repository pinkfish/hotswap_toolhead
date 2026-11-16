# Placement plan for the USB board (BW=19.5, BH=23.5), read by place.py through PLAN_FILE.
# Board mm from the top-left, seen from the top. Two M2 half-hole notches instead of mounting
# holes, diagonally opposite: left edge low, right edge high. The parts sit in the middle 18 mm
# (L to R); the 0.75 mm strip down each side gives the notches' screw-head keep-out room.
#  - USB-C (J5) centred on the top edge, plug pointing up; the JST-SH plug (J2) centred on the
#    bottom edge, plug pointing down, its hold-down pads 0.5 mm in from the edge
#  - the LEDs and their resistors right of the USB-C; RESET on the right edge in the
#    band between the connectors
#  - U6 on the bottom in the middle (U6_AT in run_usb.sh), turned so its USB pins (33/34) face
#    J5; its crystal and decoupling strip (the stack's routed corner, corner_import.py) runs
#    along below it, under J2. Each side's parts follow U6's pins: SWCLK and LED_STAT on its
#    right, the thermistor, switch and fan inputs on its left
#  - top, in the band between the connectors, left to right: the fan FET and gate resistors
#    over J2's fan pins, the thermistor divider and filter, its clamp. Beside J2: the fan's
#    flyback diode by the fan pins (left), the switch filter by the switch pin (right)
#  - bottom: USB ESD and VBUS cap under J5, the +3V3 bulk cap above it; the fan PTC, a CC
#    pull-down and the PT1000 jumper down the left column (4.4 mm wide beside U6's pins); the
#    other CC pull-down, the VBUS cap, the BOOT pads and resistor and the LDO's caps down
#    the right, the LDO below
W2 = W / 2
L, R = 0.75, W - 0.75
# left: between the fan gate resistors and the flyback diode; right: between LED2 and RESET on
# top, between the VBUS cap and the BOOT pads below
NOTCHES = [(0, 16.2), (W, 9.0)]
ESCAPE = {'U6': (0.4, 0.4, 0.4, 0.4)}
PLAN = {
    'J5': (W2, 3.65, 180, 'F', 1),
    # 0.35 mm right of centre and 23.5 mm down, so its pad row clears the corner strip's vias
    # (a via between two 1 mm pitch pads doesn't fit) and its right hold-down pad the GND via by C12
    'J2': (W2 + 0.35, H - 3.3, 0, 'F', 1),
    'SW1': (R - 2.0, 14.0, 90, 'F', 1),
    'U6': (None, None, None, 'B', 1),
    'Y1': (None, None, None, 'B', 1), 'C13': (None, None, None, 'B', 1), 'C14': (None, None, None, 'B', 1),
    'C9': (None, None, None, 'B', 1), 'C11': (None, None, None, 'B', 1), 'C12': (None, None, None, 'B', 1),
    'FB1': (None, None, None, 'B', 1), 'C15': (None, None, None, 'B', 1),
    # ---- bottom
    'U5': (W2, 5.4, 90, 'B', 0), 'C17': (W2 + 6.6, 7.0, 90, 'B', 1),
    # +3V3 bulk cap in the strip between J5's front shell legs and the top edge
    'C10': (W2, 1.3, 0, 'B', 1),
    # left column
    'F2': (L + 1.45, 2.8, 90, 'B', 1), 'R21': (L + 1.2, 6.4, 90, 'B', 1),
    'JP2': (L + 1.5, 9.6, 90, 'B', 1),
    # right column (RESET's peg holes at y 14.0), the LDO in the corner below it
    'R20': (R - 1.4, 3.6, 90, 'B', 1),
    # BOOT pads across the column, +3V3 pad inboard (pad 1 left at 0 on the bottom), as far in
    # as U6 allows, clear of the right notch; their resistor below them, SWCLK pad inboard
    'JP3': (R - 3.1, 10.6, 0, 'B', 1), 'R4': (R - 2.2, 12.6, 180, 'B', 1),
    'C4': (R - 2.15, 15.9, 90, 'B', 1), 'C8': (R - 0.95, 15.9, 90, 'B', 1),
    'U1': (R - 2.2, H - 3.2, 90, 'B', 1),
    # ---- top
    # right of J5, above the CC1 via (usb_pair_pre.py)
    # each LED's resistor beside it, so the right notch fits below LED2
    'R5': (R - 2.6, 2.0, 90, 'F', 1), 'LED1': (R - 1.05, 1.95, 90, 'F', 1), 'LED2': (R - 1.05, 5.05, 90, 'F', 1), 'R6': (R - 2.6, 5.05, 90, 'F', 1),
    'Q3': (L + 2.3, 10.9, 0, 'F', 1), 'R15': (L + 1.0, 13.2, 90, 'F', 0), 'R16': (L + 2.2, 13.2, 90, 'F', 0),
    'D6': (W2 + 2.15, 11.9, 90, 'F', 1),
    # 0.5 mm below J5's courtyard: VBUS and CC1 run along under J5's pad row (usb_pair_pre.py)
    'R17': (W2 - 2.6, 10.2, 0, 'F', 1), 'R18': (W2 - 2.6, 11.55, 0, 'F', 1),
    'R19': (W2 - 0.65, 10.2, 0, 'F', 1), 'C19': (W2 - 0.65, 11.55, 0, 'F', 1),
    'D5': (L + 1.4, H - 3.0, 90, 'F', 0),
    'R22': (R - 2.3, H - 5.4, 90, 'F', 0), 'R23': (R - 1.1, H - 5.4, 90, 'F', 0), 'C20': (R - 1.7, H - 2.6, 0, 'F', 0),
}
