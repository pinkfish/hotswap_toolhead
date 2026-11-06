# Placement plan for the logic board (BW=27, BH=H), read by place.py through PLAN_FILE.
# Board mm from the top-left, seen from the top. The logic board is the upper board of the
# stack: its top side faces out (connectors, button, LEDs, jumpers), its bottom side faces the
# power board, 11 mm below, and carries the link socket J3.
#  - J1 (XT30, power and CAN) on the top edge, left, with the power input under it exactly as on
#    the 27 x 36 board, so power_pre.py's pours (NARROW) still fit
#  - J3 (link socket) under the top-right corner: J1's pins block the top-left of the bottom
#    side, and the power board's J2 fills its bottom centre, so the link can only go there
#  - USB-C on the bottom edge between the mounting holes, plug pointing down
#  - RESET on the left edge below J1 (its pegs would hit J3 on the right)
#  - U6 turned so each side faces what it connects to (QFN-48 at rotation 0 on the bottom, seen
#    from the top): pins 1-12 (NRST, crystal, VDD, VREF+) face left, to the crystal, decoupling and
#    RESET; 13-24 (TH_ADC, SENS_IN, FAN_PWM, CAN) face up; 25-36 (USB, SWCLK) face right, down to
#    J5; 37-48 (LED_STAT, HEAT_PWM) face down
#  - the thermistor and switch-sensor filters on top over J3's sensor pins (the top side's right
#    half is free: J3 is on the bottom), the CAN transceiver under J1's CAN pins
ESCAPE = {'U6': (0.5, 0.4, 0.6, 0.4)}
PLAN = {
    'H1': (3.2, H - 3.4, 0, 'F', 1), 'H2': (23.5, H - 3.5, 0, 'F', 1),
    'J1': (8.15, 7.27, 180, 'F', 1),
    'J5': (13.5, H - 3.65, 0, 'F', 1),
    # turned so pin 1 (+24V) is at the top and the thermistor pins 11/12 at the bottom;
    # the power board's header J4 sits at the same contact positions (check_stack.py)
    'J3': (22.3, 8.6, 180, 'B', 1),
    'SW1': (2.0, 14.0, 270, 'F', 1),
    # power input under J1 (as on the 27 x 36 board)
    'Q1': (9.45, 3.9, 0, 'B', 1), 'F1': (14.45, 4.6, 90, 'B', 1), 'D1': (10.08, 8.95, -90, 'B', 1),
    'D2': (3.2, 2.75, 0, 'B', 1), 'R1': (1.25, 6.0, 90, 'B', 1),
    # bulk 24 V cap over J3's +24V pins, inside the In2 +24V strip
    'C1': (21.5, 2.6, 0, 'F', 0),
    # MCU in the middle of the bottom side, below J1's pins, between J5's shell legs, with the
    # 27 x 36 board's routed corner (crystal, load caps, NRST cap, VDD / VREF+ decoupling, FB1) turned with
    # it to its left: corner_import.py places them before place.py runs
    'U6': (None, None, None, 'B', 1),
    'Y1': (None, None, None, 'B', 1), 'C13': (None, None, None, 'B', 1), 'C14': (None, None, None, 'B', 1),
    'C9': (None, None, None, 'B', 1), 'C11': (None, None, None, 'B', 1), 'C12': (None, None, None, 'B', 1),
    'FB1': (None, None, None, 'B', 1), 'C15': (None, None, None, 'B', 1),
    # the +3V3 bulk cap below the corner
    'C10': (6.0, 20.0, None, 'B', 0),
    # CAN: transceiver under J1's CAN pins (CAN_H/CAN_L up to them, TX/RX facing down), ESD on top
    # beside them, termination on top below J1
    'U3': (2.4, 10.7, 90, 'B', 1), 'D4': (5.8, 12.9, 90, 'F', 1),
    'R11': (8.0, 12.4, None, 'F', 0), 'JP1': (6.2, 15.0, 90, 'F', 0), 'C16': (4.75, 9.2, 90, 'B', 1),
    # USB: ESD right of U6 under J3's bottom end (usb_stack_pre.py routes the pair to it), CC
    # pull-downs and VBUS parts on top above J5
    'U5': (20.95, 18.8, 0, 'B', 1),
    'R20': (11.6, 16.9, 90, 'F', 0), 'R21': (15.4, 16.9, 90, 'F', 0),
    'C17': (23.6, 18.6, None, 'B', 0), 'D3': (21.35, 18.6, 0, 'F', 1),
    # BOOT pads and their resistor on top right of U6's SWCLK pin
    'JP3': (18.6, 13.6, 0, 'F', 0), 'R4': (17.4, 16.4, -90, 'F', 1),
    # LEDs on top, lower left, between RESET and J5
    'LED1': (5.6, 17.6, 0, 'F', 0), 'LED2': (5.6, 19.2, 0, 'F', 0),
    'R5': (8.2, 17.6, None, 'F', 0), 'R6': (8.2, 19.2, None, 'F', 0),
    # thermistor: pull-ups, PT1000 header, series R, clamp and filter cap on top by J3 pin 11;
    # switch sensor: pull-up, series R and cap on top by J3 pin 10
    'JP2': (22.0, 15.4, 0, 'F', 0), 'R17': (19.0, 11.4, None, 'F', 0), 'R18': (21.0, 11.4, None, 'F', 0),
    'R19': (17.6, 9.8, None, 'F', 0), 'D6': (20.2, 8.4, None, 'F', 0), 'C19': (17.6, 7.6, None, 'F', 0),
    'R22': (25.2, 10.0, 90, 'F', 0), 'R23': (23.4, 10.0, 90, 'F', 0), 'C20': (23.6, 7.4, None, 'F', 0),
}
