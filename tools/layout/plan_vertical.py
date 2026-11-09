# Placement plan for the single board with vertical connectors (BW=27, BH=H), read by place.py
# through PLAN_FILE. Board mm from the top-left, seen from the top.
#  - J1 (vertical XT30, power and CAN) along the top edge, left: + pin at the left, CAN pins at
#    the right end; USB-C (J5, vertical) stood on end top right, so a plug's overmould clears J1
#  - J2 (vertical Nano-Fit) at the bottom centre between the mounting holes, heater column on the
#    right (pins 1/5 at x 17.1), as on the 27 x 36 board
#  - U6 on the bottom at rotation 90 as on the 27 x 36 board (CAN pins left, USB up, HEAT_PWM
#    right, crystal corner below it): corner_import.py places it and the corner at U6_AT
#  - bottom: power input under J1's + pin (fuse, reverse-polarity FET, TVS), the CAN transceiver
#    between it and U6's CAN pins, the thermistor clamp and pull-ups below, USB VBUS parts, the
#    heater FET, its gate driver and 24 V cap on the right
#  - top: the buck in the band below J1, USB ESD between J1 and J5, LEDs, BOOT pads and CAN
#    termination over U6, the PT1000 jumper and sensor filters above J2's sensor pins, the
#    fan fuse left of J2, the fan FET right of it, above H2
ESCAPE = {'U6': (0.4, 0.4, 0.4, 0.4)}
PLAN = {
    'H1': (3.2, H - 3.4, 0, 'F', 1), 'H2': (23.5, H - 3.5, 0, 'F', 1),
    'J1': (8.6, 3.2, 0, 'F', 1),
    'J5': (23.6, 5.2, 90, 'F', 1),
    'J2': (17.1, H - 5.04, 270, 'F', 1),
    'SW1': (25.0, 13.6, 90, 'F', 1),
    'U6': (None, None, None, 'B', 1),
    'Y1': (None, None, None, 'B', 1), 'C13': (None, None, None, 'B', 1), 'C14': (None, None, None, 'B', 1),
    'C9': (None, None, None, 'B', 1), 'C11': (None, None, None, 'B', 1), 'C12': (None, None, None, 'B', 1),
    'FB1': (None, None, None, 'B', 1), 'C15': (None, None, None, 'B', 1),
    # ---- bottom
    # power input: fuse beside J1's + pin, the FET below, drain (VIN_F) left, source right
    'F1': (1.55, 2.75, 90, 'B', 1), 'Q1': (4.0, 8.4, 180, 'B', 1),
    'D1': (1.6, 13.5, 90, 'B', 0), 'D2': (5.0, 12.6, 0, 'B', 0), 'R1': (7.2, 13.8, None, 'B', 0),
    'C1': (4.6, 15.6, 0, 'B', 0), 'C3': (4.6, 18.0, 0, 'B', 0),
    # CAN transceiver between the FET and U6's CAN pins, under J1's CAN pins
    'U3': (9.8, 8.1, None, 'B', 1), 'C16': (9.8, 5.6, None, 'B', 0),
    # thermistor clamp, pull-ups and filter cap, switch-sensor cap, fan flyback: below U3, left of the corner
    'D6': (9.0, 16.4, None, 'B', 0), 'R17': (9.0, 12.2, None, 'B', 0), 'R18': (9.0, 13.6, None, 'B', 0),
    'C19': (9.0, 19.4, None, 'B', 0), 'D5': (7.6, 19.6, None, 'B', 0), 'C10': (1.6, 18.4, None, 'B', 0),
    # USB: CC pull-downs between J5's shell legs, VBUS cap and OR diode on the right
    'R20': (23.6, 4.2, 0, 'B', 0), 'R21': (23.6, 6.4, 0, 'B', 0),
    'C17': (23.6, 11.0, None, 'B', 0), 'D3': (22.2, 16.6, 90, 'B', 0), 'D7': (1.6, 13.8, 90, 'F', 0),
    'C2': (25.4, H - 16.2, 90, 'B', 0), 'R13': (25.6, 11.4, None, 'B', 0),
    # ---- top
    # buck in the band below J1
    'C4': (1.6, 9.2, 90, 'F', 0), 'U1': (4.8, 8.6, None, 'F', 0), 'L1': (9.2, 8.8, 0, 'F', 0),
    'D9': (4.8, 12.4, None, 'F', 0), 'C8': (9.2, 12.4, 0, 'F', 0), 'C5': (2.0, 12.6, None, 'F', 0),
    'C6': (6.6, 11.0, None, 'F', 0), 'R2': (12.2, 10.6, None, 'F', 0), 'R3': (12.2, 12.0, None, 'F', 0),
    # USB ESD between J1 and J5, BOOT pads and resistor, LEDs, CAN ESD and termination over U6
    'U5': (18.4, 3.2, None, 'F', 0), 'D4': (14.4, 7.8, None, 'F', 0),
    'R11': (14.6, 10.8, None, 'F', 0), 'JP1': (14.6, 13.4, None, 'F', 0),
    'JP3': (18.6, 8.0, None, 'F', 0), 'R4': (20.6, 9.4, None, 'F', 0),
    'LED1': (18.2, 11.0, 0, 'F', 0), 'LED2': (18.2, 12.6, 0, 'F', 0),
    'R5': (20.8, 11.0, None, 'F', 0), 'R6': (20.8, 12.6, None, 'F', 0),
    # PT1000 jumper, thermistor series R, switch-sensor parts above J2's sensor pins
    'JP2': (6.6, 15.4, 0, 'F', 0), 'R19': (11.0, 15.6, None, 'F', 0),
    'R22': (1.4, 14.6, None, 'F', 0), 'R23': (1.4, 16.0, None, 'F', 0), 'C20': (12.6, 15.6, None, 'F', 0),
    # fan: fuse left of J2 above H1, FET and gate parts right of J2 above H2
    'F2': (4.0, H - 8.2, 0, 'F', 0), 'Q3': (22.0, H - 8.6, None, 'F', 0),
    'R15': (21.0, H - 11.6, None, 'F', 0), 'R16': (25.4, H - 8.0, None, 'F', 0),
    # heater on the bottom right, below SW1's pegs: FET with its drain toward J2's heater pins,
    # gate driver below it, the 12 V rail parts and the 24 V cap beside them
    'Q2': (22.8, H - 12.6, None, 'B', 0), 'U7': (23.0, H - 8.4, 90, 'B', 0),
    'R14': (20.9, H - 9.6, None, 'B', 0), 'D10': (25.8, H - 11.0, None, 'B', 0), 'C21': (25.8, H - 13.2, None, 'B', 0),
}
