# Placement plan for the 27 mm-wide board (BW=27, BH=36), read by place.py through PLAN_FILE.
# Parts moved as routed blocks by blocks.py are kept where they are (x None). The rest are
# placed here, each at the free spot nearest its target. Board mm from the top-left, seen from
# the top; H is the board height.
K = (None, None, None, None, 1)
PLAN = {r: K for r in (
    'J1', 'Q1', 'F1', 'D2', 'R1',                                  # power input under J1
    'J5', 'U5', 'C17', 'R20', 'R21',                               # USB-C, top edge
    'D4', 'U3', 'C16', 'R11', 'JP1',                               # CAN
    'U6', 'Y1', 'C9', 'C11', 'C12', 'C13', 'C14', 'C15', 'FB1', 'JP3', 'R4',   # MCU
    'R2', 'R3', 'D7', 'U1', 'C6', 'C4', 'C5', 'L1',                # buck, right-hand edge
    'J2', 'F2', 'D6', 'D5')}                                       # J2 and the parts above it
PLAN.update({
    # M2.5 holes in the bottom corners, either side of J2
    'H1': (3.2, H - 3.4, 0, 'F', 1), 'H2': (23.5, H - 3.5, 0, 'F', 1),
    # top: the 10 uF ceramic where the 47 uF can was, between the CAN termination and the BOOT
    # pads, and the 22 uF on the right edge beside the heater FET (below U6, between C1 and F2, is
    # U6's +3V3 vias and NRST run); RESET on the right edge with the LEDs and their resistors beside it; the gate driver
    # above the heater FET, which sits right of J2; on the left edge the fan FET and its gate
    # parts under J1, the sensor filter, then the thermistor jumper and pull-up above H1
    'C1': (11.3, 14.0, 90, 'F', 0), 'C2': (25.2, 26.3, 90, 'F', 0),
    'C8': (17.05, 18.2, 0, 'F', 1),          # above U6's NRST run
    'SW1': (25.0, 13.4, 90, 'F', 1),
    'LED1': (21.6, 11.0, 0, 'F', 0), 'LED2': (21.6, 13.0, 0, 'F', 0),
    # LED resistors in a row below LED2, either side of the GND via right of D7's +24V via: LED2's
    # (R6) left, under the LED_STAT drop, so the anode lanes don't cross (narrow_pre.py); R5 turned
    # so its +3V3 pad faces the strip beside SW1 (between the anode lanes it has no way out)
    'R6': (20.7, 16.85, 0, 'F', 1), 'R5': (22.85, 16.85, 180, 'F', 1),
    'U7': (23.2, 22.4, None, 'F', 0), 'R14': (20.2, 21.6, 90, 'F', 0),
    'Q2': (21.9, 26.4, 180, 'F', 1),
    # the gate rail's 12 V clamp and its capacitor in the free strip right of U7
    'D10': (25.75, 21.0, 90, 'F', 0), 'C21': (25.75, 23.3, 90, 'F', 0),
    'R22': (1.4, 19.95, 0, 'F', 0), 'R23': (3.5, 19.95, 0, 'F', 0), 'C20': (5.6, 19.95, 0, 'F', 0),
    'R15': (1.4, 12.6, 0, 'F', 0), 'R16': (1.4, 13.9, 0, 'F', 0), 'Q3': (3.2, 16.4, None, 'F', 0),
    'JP2': (2.4, 25.8, 90, 'F', 0), 'R18': (5.4, 23.4, 90, 'F', 0), 'C3': (5.6, 27.5, 90, 'F', 0),
    # bottom: D1 between J1's power pins (VIN_F pad up under Q1's drain, power_pre.py NARROW), the
    # USB-to-buck diode, the thermistor filter, the buck catch diode beside H2 (clear of the
    # FAN_P lane, narrow_pre.py), the gate rail's 10k feed and the 10 uF ceramic on the left
    'D1': (10.08, 8.95, 270, 'B', 1), 'D3': (21.4, 11.0, 180, 'B', 0),
    'R17': (7.4, 23.6, 0, 'B', 0), 'C19': (9.0, 22.4, 180, 'B', 0), 'R19': (10.65, 22.6, 90, 'B', 0),
    'D9': (19.55, 32.4, -90, 'B', 1), 'R13': (26.0, 24.2, -90, 'B', 0),
    'C10': (4.0, 27.0, 0, 'B', 0),
})
