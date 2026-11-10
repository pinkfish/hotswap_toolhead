# Placement plan for the USB board (BW=22, BH=30), read by place.py through PLAN_FILE.
# Board mm from the top-left, seen from the top.
#  - USB-C (J5) centred on the top edge, plug pointing up; the JST-PH plug (J2) centred on the
#    bottom edge, plug pointing down. The two M2.5 holes sit at the side edges between them
#  - RESET on the right edge beside the USB-C, the LEDs in the corner left of it
#  - U6 on the bottom in the middle (U6_AT in run_usb.sh), turned so its USB pins (33/34) face
#    J5; its crystal and decoupling strip (the stack's routed corner, corner_import.py) runs
#    along below it. J2's 5 mm long top-side pads must stay clear of the strip's vias, which
#    sets the board's height
#  - top, in the band between the connectors: BOOT pads, the PT1000 jumper and the thermistor
#    divider and filter
#  - bottom: USB ESD and VBUS cap under J5, CC pull-downs left of it; the fan FET, flyback diode
#    and gate resistors in the left column under J2's fan pins; the LDO and the switch filter in
#    the right column; the fan PTC and thermistor clamp below the corner strip
ESCAPE = {'U6': (0.4, 0.4, 0.4, 0.4)}
PLAN = {
    'H1': (3.2, 12.7, 0, 'F', 1), 'H2': (W - 3.2, 12.7, 0, 'F', 1),
    'J5': (W / 2, 3.65, 180, 'F', 1),
    # hold-down pads 0.5 mm in from the edge; 0.53 mm left of centre so the corner strip's GND via
    # under it falls in the gap between pins 3 and 4
    'J2': (W / 2 - 0.53, H - 5.1, 0, 'F', 1),
    'SW1': (W - 2.0, 4.4, 90, 'F', 1),
    'U6': (None, None, None, 'B', 1),
    'Y1': (None, None, None, 'B', 1), 'C13': (None, None, None, 'B', 1), 'C14': (None, None, None, 'B', 1),
    'C9': (None, None, None, 'B', 1), 'C11': (None, None, None, 'B', 1), 'C12': (None, None, None, 'B', 1),
    'FB1': (None, None, None, 'B', 1), 'C15': (None, None, None, 'B', 1),
    # ---- bottom
    'U5': (W / 2, 5.4, 90, 'B', 0), 'C17': (W - 4.4, 7.6, 90, 'B', 0),
    'R20': (4.4, 6.6, 90, 'B', 0), 'R21': (3.4, 6.6, 90, 'B', 0),
    # fan, left column
    'Q3': (2.9, 17.8, None, 'B', 0), 'D5': (2.0, H - 3.4, 90, 'B', 0),
    'R15': (4.9, H - 4.6, 90, 'B', 0), 'R16': (4.9, H - 2.4, 90, 'B', 0),
    # below the corner strip, past the end of J2's pads (no vias may go under those)
    'F2': (8.6, H - 1.8, 0, 'B', 0), 'D6': (12.8, H - 2.0, None, 'B', 0),
    # LDO and switch filter, right column
    'U1': (W - 3.4, 18.6, 90, 'B', 0), 'C4': (W - 0.9, 17.2, 90, 'B', 0), 'C8': (W - 0.9, 19.6, 90, 'B', 0),
    'C10': (W - 6.0, 22.4, 0, 'B', 0),
    'R22': (W - 5.0, H - 1.4, 0, 'B', 0), 'R23': (W - 2.6, H - 1.4, 0, 'B', 0), 'C20': (W - 0.9, H - 3.6, 90, 'B', 0),
    # ---- top
    'LED1': (1.6, 2.6, 90, 'F', 0), 'R5': (1.6, 5.6, 90, 'F', 0),
    'LED2': (3.6, 2.6, 90, 'F', 0), 'R6': (3.6, 5.6, 90, 'F', 0),
    'JP3': (8.0, 10.4, 0, 'F', 0), 'R4': (8.0, 12.2, 0, 'F', 0),
    'JP2': (W / 2, 14.4, 0, 'F', 0),
    # 0.5 mm below J5's courtyard: VBUS and CC1 run along under J5's pad row (usb_pair_pre.py)
    'R17': (11.6, 10.2, 0, 'F', 0), 'R18': (11.6, 11.3, 0, 'F', 0),
    'R19': (13.9, 10.2, 0, 'F', 0), 'C19': (13.9, 11.3, 0, 'F', 0),
}
