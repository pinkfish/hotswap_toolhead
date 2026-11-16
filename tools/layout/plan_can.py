# Placement plan for the CAN board (BW=27, BH=34), read by place.py through PLAN_FILE.
# Board mm from the top-left, seen from the top. Two M2 half-hole notches, diagonally opposite.
#  - J1 (24 V + CAN in, JST-XH 6) on the top edge, plug pointing up: +24V pins on the right,
#    CAN on the left over U6's CAN pins; J3 (heater, XH 4) bottom right and J2 (fan, thermistor,
#    switch, SH 6) bottom left, plugs pointing down; J5 (USB, SH 4) on the left edge
#  - top: the fuse under J1's +24V pins and the +24V strip straight down to J3's +24V pins;
#    the heater FET above J3's HEAT_N pins with its gate driver left of it; the buck down the
#    left; LEDs and RESET right of the strip
#  - bottom: U6 in the middle (U6_AT in run_can.sh) with its crystal and decoupling corner
#    below it; CAN and USB ESD under J1; the thermistor and switch filters by J2
W2 = W / 2
ESCAPE = {'U6': (0.4, 0.4, 0.4, 0.4)}
EDGE_OK = {'J1', 'J2', 'J3', 'J5', 'SW1'}
NOTCHES = [(0, H - 9.5), (W, 5.5)]
PLAN = {
    # ---- connectors
    'J1': (W2, 6.0, 180, 'F', 1),
    'J3': (W - 8.45, H - 6.0, 0, 'F', 1),
    'J2': (5.05, H - 3.3, 0, 'F', 1),
    'J5': (3.3, 15.0, 270, 'F', 1),
    # RESET high and the LEDs below it, so both side edges are clear at y 18.9-22 for the
    # panel's lower mouse bites (panel_tabs.py)
    'SW1': (W - 2.0, 15.6, 90, 'F', 1),
    'U6': (None, None, None, 'B', 1),
    'Y1': (None, None, None, 'B', 1), 'C13': (None, None, None, 'B', 1), 'C14': (None, None, None, 'B', 1),
    'C9': (None, None, None, 'B', 1), 'C11': (None, None, None, 'B', 1), 'C12': (None, None, None, 'B', 1),
    'FB1': (None, None, None, 'B', 1), 'C15': (None, None, None, 'B', 1),
    # ---- top, in the band between J1 and J3: the fuse under J1's +24V pins, the +24V strip
    # down to J3's +24V pins, the heater FET over J3's HEAT_N pins with its driver and 12 V
    # rail left of it; LEDs and RESET on the right edge
    # (can_pre.py pours the path from these pads: keep them fixed). D1 points its +24V
    # pad into the strip, its GND pad away from it
    'F1': (W2 + 5.0, 13.4, 0, 'F', 1), 'D1': (W2 + 3.0, 15.9, 180, 'F', 1),
    # drain pad down, over J3's HEAT_N pins
    # right of J3's HEAT_N pins' centre, so the drain clears U6's corner vias underneath
    # (corner_import.py): a GND via would take the drain's net and clash with the VBAT via
    'Q2': (W2 + 4.1, 19.7, 270, 'F', 1),
    # U7's OUT pad clear of U6's corner +3V3 via at (W2 + 0.1, 19.0) underneath
    'U7': (W2 - 2.6, 19.8, 0, 'F', 1), 'R13': (W2 - 4.6, 15.0, 0, 'F', 0), 'D10': (W2 - 4.6, 16.4, 0, 'F', 0),
    # C21 left of the GND return's column
    'C21': (W2 - 4.6, 17.8, 0, 'F', 0), 'R14': (W2 - 5.4, 20.0, 90, 'F', 0),
    'LED1': (W - 1.3, 20.2, 90, 'F', 0), 'LED2': (W - 2.7, 20.2, 90, 'F', 0),
    # ---- bottom
    # CAN under J1's CAN pins
    'U3': (6.5, 6.0, 0, 'B', 0), 'D4': (3.0, 8.5, 0, 'B', 0), 'R11': (9.8, 8.8, 0, 'B', 0),
    'JP1': (3.0, 4.5, 90, 'B', 0), 'C16': (9.0, 4.0, 0, 'B', 0),
    # BOOT pads and resistor by SWCLK (pin 36), +3V3 bulk, under J1's right half
    'JP3': (W2 + 6.0, 6.5, 0, 'B', 0), 'R4': (W2 + 6.0, 8.6, 0, 'B', 0), 'C10': (W2 + 2.0, 8.0, 0, 'B', 0),
    # USB ESD and VBUS by J5, the thermistor network below it
    'U5': (4.0, 13.0, 90, 'B', 0), 'C17': (4.5, 16.0, 0, 'B', 0), 'D3': (5.0, 17.6, 0, 'B', 0),
    'R17': (3.0, 19.4, 0, 'B', 0), 'R18': (3.0, 20.6, 0, 'B', 0), 'JP2': (1.4, 22.2, 90, 'B', 0),
    'R19': (5.6, 19.4, 0, 'B', 0), 'C19': (5.6, 20.6, 0, 'B', 0), 'D6': (5.3, 22.6, 0, 'B', 0),
    # right of U6: LED resistors and the switch filter
    'R5': (W - 3.5, 12.0, 0, 'B', 0), 'R6': (W - 3.5, 13.2, 0, 'B', 0),
    'R22': (W - 3.5, 15.5, 0, 'B', 0), 'R23': (W - 3.5, 16.7, 0, 'B', 0), 'C20': (W - 3.5, 17.9, 0, 'B', 0),
    # the 24 V bulk caps under the strip
    'C1': (W - 5.5, 14.5, 90, 'B', 0), 'C2': (W - 5.5, 21.0, 90, 'B', 0),
    # under J2: the fan driver
    'F2': (4.6, 31.0, 0, 'B', 0), 'Q3': (5.0, 27.4, 0, 'B', 0), 'D5': (8.6, 30.6, 90, 'B', 0),
    'R15': (2.0, 27.4, 90, 'B', 0), 'R16': (7.6, 26.6, 90, 'B', 0),
    # under J3: the buck
    'L1': (W - 3.2, 29.5, 0, 'B', 0), 'U1': (W - 8.0, 29.0, 0, 'B', 0), 'D9': (W - 7.0, 32.4, 0, 'B', 0),
    'C8': (W - 3.2, 25.6, 0, 'B', 0), 'C4': (W - 12.0, 29.5, 90, 'B', 0), 'C5': (W - 10.4, 26.6, 0, 'B', 0),
    'C6': (W - 8.0, 26.6, 0, 'B', 0), 'R2': (W - 6.0, 26.0, 0, 'B', 0), 'R3': (W - 6.0, 27.0, 0, 'B', 0),
    'D7': (W - 13.5, 32.4, 0, 'B', 0),
}
