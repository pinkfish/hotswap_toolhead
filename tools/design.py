"""Single source of truth for the 24 V CAN heater/fan controller.

Every part lists its symbol style, footprint (KiCad standard library name),
value, LCSC number and a {pin_number: net} map. Pins not listed are
no-connect. The generator builds the schematics and the BOMs from this file,
so edit connections here, not in the outputs.

The controller is two stacked boards joined by a 2x6 2.54 mm board-to-board
link (LINK): the logic board (power and CAN input, protection, MCU, USB,
thermistor and switch inputs) on top, and the power board (3.3 V buck, heater
and fan drivers, the load plug) under it. Each part's board is BOARD_OF[block]
unless the part sets board=. Net names are shared across the link, except the
thermistor return (TH_RTN on the power board), which is a GND pin of its own
on the logic board, so heater current in the link's GND pins doesn't shift the
thermistor reading.
"""

# ---------------------------------------------------------------------------
# Symbol pin layouts for multi-pin parts: (left pins, right pins),
# each pin is (number, name).
# ---------------------------------------------------------------------------
STM32_PINS = {
    49: "EP",
    1: "PC13", 2: "PC14", 3: "PC15", 4: "VBAT", 5: "VREF+", 6: "VDD/VDDA",
    7: "VSS/VSSA", 8: "PF0-OSC_IN", 9: "PF1-OSC_OUT", 10: "PF2-NRST",
    11: "PA0", 12: "PA1", 13: "PA2", 14: "PA3", 15: "PA4", 16: "PA5",
    17: "PA6", 18: "PA7", 19: "PB0", 20: "PB1", 21: "PB2", 22: "PB10",
    23: "PB11", 24: "PB12", 25: "PB13", 26: "PB14", 27: "PB15", 28: "PA8",
    29: "PA9", 30: "PC6", 31: "PC7", 32: "PA10", 33: "PA11", 34: "PA12",
    35: "PA13", 36: "PA14-BOOT0", 37: "PA15", 38: "PD0", 39: "PD1",
    40: "PD2", 41: "PD3", 42: "PB3", 43: "PB4", 44: "PB5", 45: "PB6",
    46: "PB7", 47: "PB8", 48: "PB9",
}
STM32_LAYOUT = (
    [(n, STM32_PINS[n]) for n in [4, 5, 6, 7, 8, 9, 10, 1, 2, 3, 30, 31,
                                  38, 39, 40, 41, 15, 16, 17, 18, 21, 22, 23, 24]],
    [(n, STM32_PINS[n]) for n in [11, 12, 13, 14, 19, 20, 25, 26, 27, 28, 29,
                                  32, 33, 34, 35, 36, 37, 42, 43, 44, 45, 46, 47, 48, 49]],
)

# Buck: TI LMR16006X (60 V, 0.6 A, 0.7 MHz), SOT-23-6 "DDC" package.
# Pinout per TI datasheet: 1 CB, 2 GND, 3 FB, 4 SHDN, 5 VIN, 6 SW.
BUCK_LAYOUT = (
    [(5, "VIN"), (4, "SHDN"), (2, "GND")],
    [(1, "CB"), (6, "SW"), (3, "FB")],
)
CAN_LAYOUT = (
    [(1, "TXD"), (4, "RXD"), (8, "STB"), (5, "SHDN")],
    [(3, "VDD"), (7, "CANH"), (6, "CANL"), (2, "GND"), (9, "EP")],
)
USBLC6_LAYOUT = ([(1, "IO1"), (6, "IO1"), (2, "GND")], [(3, "IO2"), (4, "IO2"), (5, "VBUS")])
FET_LAYOUT = ([(4, "G"), (1, "S"), (2, "S"), (3, "S")], [(5, "D")])
SOT3_LAYOUT = ([(1, "1"), (2, "2")], [(3, "3")])
SOT23FET_LAYOUT = ([(1, "G"), (2, "S")], [(3, "D")])
# TI UCC27517 low-side gate driver, SOT-23-5 "DBV": 1 VDD, 2 GND, 3 IN+, 4 IN-, 5 OUT.
GATEDRV_LAYOUT = ([(1, "VDD"), (3, "IN+"), (4, "IN-")], [(5, "OUT"), (2, "GND")])
XTAL4_LAYOUT = ([(1, "X1"), (2, "GND")], [(3, "X2"), (4, "GND")])
BAT54S_LAYOUT = ([(1, "A1"), (2, "K2")], [(3, "K1/A2")])
XT30_LAYOUT = ([(1, "P+"), (2, "P-")], [(3, "S1"), (4, "S2")])
CONN2_LAYOUT = ([(1, "1"), (2, "2")], [])
CONN4_LAYOUT = ([(1, "1"), (2, "2"), (3, "3"), (4, "4")], [])
# 2x4 plug: each 2-wire load on one column (pins n and n+4 side by side).
# Board-to-board link, 2x6: odd pins one row, even pins the other.
CONN12_LAYOUT = ([(n, str(n)) for n in (1, 3, 5, 7, 9, 11)], [(n, str(n)) for n in (2, 4, 6, 8, 10, 12)])
CONN8_LAYOUT = ([(1, "HEAT+"), (5, "HEAT-"), (2, "FAN+"), (6, "FAN-")],
                [(3, "THERM"), (7, "TGND"), (4, "SENS"), (8, "GND")])
# USB-C 16-pin receptacle (USB 2.0): both rows of D+/D- and VBUS/GND, CC per row.
USBC_LAYOUT = (
    [("A4", "VBUS"), ("A9", "VBUS"), ("B4", "VBUS"), ("B9", "VBUS"), ("A5", "CC1"), ("B5", "CC2"),
     ("A8", "SBU1"), ("B8", "SBU2")],
    [("A6", "D+"), ("B6", "D+"), ("A7", "D-"), ("B7", "D-"), ("A1", "GND"), ("A12", "GND"),
     ("B1", "GND"), ("B12", "GND"), ("SH", "SHIELD")],
)

# Link pin: (logic-board net, power-board net). 3 A contacts: two for +24V (2.35 A each with a
# 100 W heater and the fan), three for the return; TH_RTN is the thermistor's own return, a GND
# pin on the logic board.
LINK = {
    1: ("+24V", "+24V"), 2: ("+24V", "+24V"),
    3: ("GND", "GND"), 4: ("GND", "GND"),
    5: ("VIN_LOGIC", "VIN_LOGIC"), 6: ("+3V3", "+3V3"),
    7: ("GND", "GND"), 8: ("HEAT_PWM", "HEAT_PWM"),
    9: ("FAN_PWM", "FAN_PWM"), 10: ("SENS", "SENS"),
    11: ("TH_SIG", "TH_SIG"), 12: ("GND", "TH_RTN"),
}

# Footprints (KiCad 8 standard libraries). "" = assign after choosing part.
FP = {
    "R0402": "Resistor_SMD:R_0402_1005Metric",
    "R0603": "Resistor_SMD:R_0603_1608Metric",
    "R0805": "Resistor_SMD:R_0805_2012Metric",
    "C0402": "Capacitor_SMD:C_0402_1005Metric",
    "C0603": "Capacitor_SMD:C_0603_1608Metric",
    "C0805": "Capacitor_SMD:C_0805_2012Metric",
    "C1206": "Capacitor_SMD:C_1206_3216Metric",
    "L0402": "Inductor_SMD:L_0402_1005Metric",
    "L4040": "Inductor_SMD:L_Taiyo-Yuden_NR-40xx",
    "LED0603": "LED_SMD:LED_0603_1608Metric",
    "SMA": "Diode_SMD:D_SMA",
    "SMB": "Diode_SMD:D_SMB",
    "SOD123F": "Diode_SMD:D_SOD-123F",
    "SOD123": "Diode_SMD:D_SOD-123",
    "SOT23": "Package_TO_SOT_SMD:SOT-23",
    "SOT235": "Package_TO_SOT_SMD:SOT-23-5",
    "SOT236": "Package_TO_SOT_SMD:SOT-23-6",
    "SOD523": "Diode_SMD:D_SOD-523",
    "VSON8": "Package_SON:VSON-8-1EP_3x3mm_P0.65mm_EP1.65x2.4mm",
    "QFN48": "Package_DFN_QFN:QFN-48-1EP_7x7mm_P0.5mm_EP5.6x5.6mm",  # ST UFQFPN48
    "DFN3X3FET": "hotswap_toolhead:AOS_DFN-8-1EP_3x3mm_P0.65mm",
    "PPAKSO8": "Package_SO:PowerPAK_SO-8_Single",
    "XTAL3225": "Crystal:Crystal_SMD_3225-4Pin_3.2x2.5mm",
    "F1206": "Fuse:Fuse_1206_3216Metric",
    "F1812": "Fuse:Fuse_1812_4532Metric",
    "SW": "Button_Switch_SMD:SW_SPST_EVQP7C",  # side-push, 3.5 x 2.9 mm
    "SJ": "Jumper:SolderJumper-2_P1.3mm_Open_RoundedPad1.0x1.5mm",
    "HDR2": "Connector_PinHeader_1.27mm:PinHeader_1x02_P1.27mm_Vertical_SMD_Pin1Right",
    "NANOFIT8": "Connector_Molex:Molex_Nano-Fit_105314-xx08_2x04_P2.50mm_Horizontal",
    "USBC16": "Connector_USB:USB_C_Receptacle_HRO_TYPE-C-31-M-12",
    "SOCKET12": "Connector_PinSocket_2.54mm:PinSocket_2x06_P2.54mm_Vertical_SMD",
    "HEADER12": "Connector_PinHeader_2.54mm:PinHeader_2x06_P2.54mm_Vertical",
}


def P(ref, kind, value, fp, nets, lcsc="", dnp=False, block="", layout=None, board=None):
    return dict(ref=ref, kind=kind, value=value, fp=FP.get(fp, fp), nets=nets,
                lcsc=lcsc, dnp=dnp, block=block, layout=layout, board=board)


def two(ref, kind, value, fp, n1, n2, **kw):
    return P(ref, kind, value, fp, {1: n1, 2: n2}, **kw)


# Diodes and LEDs follow the KiCad footprint convention: pad 1 = cathode.
PARTS = [
    # ---------------- Power input ----------------
    P("J1", "box", "XT30PW(2+2)-M.G.B", "hotswap_toolhead:XT30PW-2+2-M",
      {1: "VIN_RAW", 2: "GND", 3: "CAN_H", 4: "CAN_L"},
      lcsc="C19268030", block="Power input", layout=XT30_LAYOUT),
    two("F1", "R", "8A 1206 fuse (0458008.DR)", "F1206", "VIN_RAW", "VIN_F", lcsc="C187562", block="Power input"),
    two("D1", "D", "SMF33CA", "SOD123F", "VIN_F", "GND", lcsc="C19077520", block="Power input"),
    P("Q1", "box", "SQJ461EP-T1_GE3", "PPAKSO8",
      {1: "+24V", 2: "+24V", 3: "+24V", 4: "Q1_G", 5: "VIN_F"},
      lcsc="C3279500", block="Power input", layout=FET_LAYOUT),
    two("D2", "D", "MMSZ5242B 12V", "SOD123", "+24V", "Q1_G", lcsc="C19077426", block="Power input"),
    two("R1", "R", "10k", "R0402", "Q1_G", "GND", block="Power input"),
    two("C1", "C", "10uF 50V X5R", "C1206", "+24V", "GND", lcsc="C13585", block="Power input"),
    # C2 and C3 sit by the heater and fan FETs, on the power board
    two("C2", "C", "10uF 50V X5R", "C1206", "+24V", "GND", lcsc="C13585", block="Power input", board="power"),
    two("C3", "C", "10uF 50V X5R", "C1206", "+24V", "GND", lcsc="C13585", block="Power input", board="power"),
    # ---------------- Logic supply ----------------
    two("D7", "D", "DSK110 100V 1A", "SOD123F", "VIN_LOGIC", "+24V", lcsc="C22466354", block="Logic supply"),
    # D3 stays by the USB-C on the logic board; VIN_LOGIC crosses the link to the buck
    two("D3", "D", "DSK110 100V 1A", "SOD123F", "VIN_LOGIC", "VBUS", lcsc="C22466354", block="Logic supply", board="logic"),
    two("C4", "C", "10uF 50V X5R", "C1206", "VIN_LOGIC", "GND", lcsc="C13585", block="Logic supply"),
    two("C5", "C", "100nF", "C0603", "VIN_LOGIC", "GND", lcsc="C14663", block="Logic supply"),
    P("U1", "box", "LMR16006XDDC", "SOT236",
      {5: "VIN_LOGIC", 4: "VIN_LOGIC", 2: "GND", 1: "BUCK_BOOT", 6: "BUCK_SW", 3: "BUCK_FB"},
      lcsc="C87080", block="Logic supply", layout=BUCK_LAYOUT),
    two("C6", "C", "100nF", "C0402", "BUCK_BOOT", "BUCK_SW", lcsc="C1525", block="Logic supply"),
    two("D9", "D", "DSK110 100V 1A", "SOD123F", "BUCK_SW", "GND", lcsc="C22466354", block="Logic supply"),
    two("L1", "L", "22uH 1.2A (FNR4030S220MT)", "L4040", "BUCK_SW", "+3V3", lcsc="C167883", block="Logic supply"),
    two("C8", "C", "22uF 25V X5R", "C1206", "+3V3", "GND", lcsc="C12891", block="Logic supply"),
    # VOUT = 0.765 V x (1 + R2/R3) = 3.29 V
    two("R2", "R", "33k", "R0402", "+3V3", "BUCK_FB", lcsc="C25779", block="Logic supply"),
    two("R3", "R", "10k", "R0402", "BUCK_FB", "GND", block="Logic supply"),
    # ---------------- MCU ----------------
    P("U6", "box", "STM32G0B1CBU6", "QFN48",
      {4: "+3V3", 5: "VREFP", 6: "+3V3", 7: "GND", 8: "OSC_IN", 9: "OSC_OUT",
       10: "NRST", 19: "CAN_RX", 20: "CAN_TX", 24: "TH_ADC", 25: "SENS_IN", 28: "FAN_PWM",
       33: "USB_D_N", 34: "USB_D_P", 36: "SWCLK",
       44: "LED_STAT", 48: "HEAT_PWM", 49: "GND"},
      lcsc="C5270156", block="MCU", layout=STM32_LAYOUT),
    two("C9", "C", "100nF", "C0402", "+3V3", "GND", lcsc="C1525", block="MCU"),
    two("C10", "C", "10uF 25V X5R", "C0805", "+3V3", "GND", lcsc="C15850", block="MCU"),
    two("FB1", "L", "600R@100MHz", "L0402", "+3V3", "VREFP", lcsc="C76884", block="MCU"),
    two("C11", "C", "1uF", "C0402", "VREFP", "GND", lcsc="C52923", block="MCU"),
    two("C12", "C", "100nF", "C0402", "VREFP", "GND", lcsc="C1525", block="MCU"),
    P("Y1", "box", "8MHz 20pF 3225", "XTAL3225", {1: "OSC_IN", 2: "GND", 3: "OSC_OUT", 4: "GND"},
      lcsc="C2682774", block="MCU", layout=XTAL4_LAYOUT),
    two("C13", "C", "33pF C0G", "C0402", "OSC_IN", "GND", lcsc="C1562", block="MCU"),
    two("C14", "C", "33pF C0G", "C0402", "OSC_OUT", "GND", lcsc="C1562", block="MCU"),
    two("C15", "C", "100nF", "C0402", "NRST", "GND", lcsc="C1525", block="MCU"),
    two("SW1", "R", "RESET", "SW", "NRST", "GND", lcsc="C388883", block="MCU"),
    # BOOT is rarely needed (blank chips enter DFU anyway, Katapult is entered by
    # double-tapping RESET): two pads to short with tweezers instead of a button.
    two("JP3", "R", "BOOT", "SJ", "+3V3", "BOOT_SW", block="MCU"),
    two("R4", "R", "1k", "R0402", "BOOT_SW", "SWCLK", block="MCU"),
    two("R5", "R", "1k", "R0402", "+3V3", "LED1_A", block="MCU"),
    two("LED1", "D", "yellow-green", "LED0603", "GND", "LED1_A", lcsc="C2289", block="MCU"),
    two("R6", "R", "100R", "R0402", "LED_STAT", "LED2_A", lcsc="C25076", block="MCU"),
    two("LED2", "D", "blue", "LED0603", "GND", "LED2_A", lcsc="C2288", block="MCU"),
    # ---------------- CAN ----------------
    # J1 pin 3 = CAN_H, pin 4 = CAN_L, wired straight through (no swap option).
    # TCAN3414 pin 5 is SHDN (high = off, internal pull-down): left open.
    P("D4", "box", "NUP2105L", "SOT23", {1: "CAN_H", 2: "CAN_L", 3: "GND"},
      lcsc="C14486", block="CAN", layout=SOT3_LAYOUT),
    two("R11", "R", "120R", "R0805", "CAN_H", "CAN_TERM", lcsc="C17437", block="CAN"),
    two("JP1", "R", "TERM", "SJ", "CAN_TERM", "CAN_L", block="CAN"),
    P("U3", "box", "TCAN3414DRBR", "VSON8",
      {1: "CAN_TX", 2: "GND", 3: "+3V3", 4: "CAN_RX", 6: "CAN_L", 7: "CAN_H", 8: "GND", 9: "GND"},
      lcsc="C31542495", block="CAN", layout=CAN_LAYOUT),
    two("C16", "C", "100nF", "C0402", "+3V3", "GND", lcsc="C1525", block="CAN"),
    # ---------------- USB ----------------
    P("J5", "box", "USB-C (HRO TYPE-C-31-M-12)", "USBC16",
      {"A4": "VBUS", "A9": "VBUS", "B4": "VBUS", "B9": "VBUS", "A5": "USB_CC1", "B5": "USB_CC2",
       "A6": "USB_D_P", "B6": "USB_D_P", "A7": "USB_D_N", "B7": "USB_D_N",
       "A1": "GND", "A12": "GND", "B1": "GND", "B12": "GND", "SH": "GND"},
      lcsc="C165948", block="USB", layout=USBC_LAYOUT),
    # 5.1k pull-downs on CC1/CC2 so a USB-C host or charger turns VBUS on.
    two("R20", "R", "5.1k", "R0402", "USB_CC1", "GND", lcsc="C25905", block="USB"),
    two("R21", "R", "5.1k", "R0402", "USB_CC2", "GND", lcsc="C25905", block="USB"),
    P("U5", "box", "USBLC6-2SC6", "SOT236",
      {1: "USB_D_N", 6: "USB_D_N", 2: "GND", 3: "USB_D_P", 4: "USB_D_P", 5: "VBUS"},
      lcsc="C7519", block="USB", layout=USBLC6_LAYOUT),
    two("C17", "C", "10uF 25V X5R", "C0805", "VBUS", "GND", lcsc="C15850", block="USB"),
    # ---------------- Heater ----------------
    # One latching 2x4 right-angle plug for heater, fan, thermistor and a
    # 2-wire switch sensor (7.5 A per contact).
    P("J2", "box", "Heater/fan/therm/sensor (Nano-Fit 2x4)", "NANOFIT8",
      {1: "+24V", 5: "HEAT_N", 2: "FAN_P", 6: "FAN_N", 3: "TH_SIG", 7: "TH_RTN", 4: "SENS", 8: "GND"},
      lcsc="C841208", block="Heater", layout=CONN8_LAYOUT),
    # 60 V, 9.5 mR max at 10 V. No 40-60 V FET at JLCPCB is rated below a 4.5 V
    # gate, so U7 drives it from a 12 V zener rail instead of the 3.3 V MCU pin.
    P("Q2", "box", "AON7264E", "DFN3X3FET",
      {1: "GND", 2: "GND", 3: "GND", 4: "HEAT_G", 5: "HEAT_N"},
      lcsc="C431191", block="Heater", layout=FET_LAYOUT),
    # Non-inverting (IN- to GND). UVLO and the input pull-downs hold OUT low
    # while the MCU is in reset or the 24 V is off.
    P("U7", "box", "UCC27517DBVR", "SOT235",
      {1: "GATE_12V", 2: "GND", 3: "HEAT_PWM", 4: "GND", 5: "HEAT_G"},
      lcsc="C99395", block="Heater", layout=GATEDRV_LAYOUT),
    # 12 V gate-drive rail from the buck input (24 V less D7's drop): about 1.1-1.7 mA
    # at 24-30 V, under 1 mA of it for U7. On USB alone it sits below U7's UVLO.
    two("R13", "R", "10k", "R0402", "VIN_LOGIC", "GATE_12V", block="Heater"),
    two("D10", "D", "BZX585-C12 12V", "SOD523", "GATE_12V", "GND", lcsc="C455018", block="Heater"),
    two("C21", "C", "1uF", "C0402", "GATE_12V", "GND", lcsc="C52923", block="Heater"),
    two("R14", "R", "10k", "R0402", "HEAT_PWM", "GND", block="Heater"),
    # ---------------- Fan ----------------
    two("F2", "R", "PTC 0.75A 33V (JK-mSMD075-33)", "F1812", "+24V", "FAN_P", lcsc="C369169", block="Fan"),
    P("Q3", "box", "WST6066A", "SOT23",
      {1: "FAN_G", 2: "GND", 3: "FAN_N"},
      lcsc="C148352", block="Fan", layout=SOT23FET_LAYOUT),
    two("D5", "D", "DSK110 100V 1A", "SOD123F", "FAN_P", "FAN_N", lcsc="C22466354", block="Fan"),
    two("R15", "R", "1k", "R0402", "FAN_PWM", "FAN_G", block="Fan"),
    two("R16", "R", "10k", "R0402", "FAN_PWM", "GND", block="Fan"),
    # ---------------- Thermistor ----------------
    two("R17", "R", "4.7k 0.1% 25ppm", "R0402", "VREFP", "TH_SIG", lcsc="C281778", block="Thermistor"),
    two("R18", "R", "4.12k 0.1% 25ppm", "R0402", "VREFP", "JP2_A", lcsc="C852812", block="Thermistor"),
    # 1.27 mm SMD header; the 1.27 mm shunt (C150949) is fitted by hand.
    # Pin1Right is the header's real leg stagger (JLCPCB footprint C41375972); the shunt is
    # symmetric, so pin 1 is TH_SIG to keep each net's pad on its side
    P("JP2", "box", "NTC/PT1000", "HDR2", {1: "TH_SIG", 2: "JP2_A"},
      lcsc="C41375972", block="Thermistor", layout=CONN2_LAYOUT),
    two("R19", "R", "1k", "R0402", "TH_SIG", "TH_ADC", block="Thermistor"),
    two("C19", "C", "100nF", "C0402", "TH_ADC", "GND", lcsc="C1525", block="Thermistor"),
    P("D6", "box", "BAT54S", "SOT23", {1: "GND", 2: "+3V3", 3: "TH_ADC"},
      lcsc="C7420333", block="Thermistor", layout=BAT54S_LAYOUT),
    # ---------------- Switch sensor (endstop / runout, switch to GND) ----------------
    two("R22", "R", "10k", "R0402", "+3V3", "SENS", block="Sensor"),
    two("R23", "R", "1k", "R0402", "SENS", "SENS_IN", block="Sensor"),
    two("C20", "C", "100nF", "C0402", "SENS_IN", "GND", lcsc="C1525", block="Sensor"),
    # ---------------- Board-to-board link ----------------
    # SMD socket on the logic board's underside, through-hole header on the power board's top;
    # 8.5 mm socket + 2.5 mm header spacer = 11 mm between the boards (M2.5 x 11 standoffs)
    P("J3", "box", "Link socket 2x6 (HC-PM254-8.5H-2x6PS)", "SOCKET12",
      {n: nets[0] for n, nets in LINK.items()}, lcsc="C22373947", block="Link", layout=CONN12_LAYOUT, board="logic"),
    P("J4", "box", "Link header 2x6 (HX PZ2.54-2x6P ZZ)", "HEADER12",
      {n: nets[1] for n, nets in LINK.items()}, lcsc="C32713279", block="Link", layout=CONN12_LAYOUT, board="power"),
]

# LCSC numbers were checked against JLCPCB's part search (stock and type) in
# October 2026; 0402 0R/1k/10k get JLCPCB basic parts.
for p in PARTS:
    if p["kind"] == "R" and p["fp"].endswith("R_0402_1005Metric") and not p["lcsc"]:
        p["lcsc"] = {"0R": "C17168", "1k": "C11702", "10k": "C25744"}.get(p["value"], "")

BLOCK_ORDER = ["Power input", "Logic supply", "MCU", "CAN", "USB", "Heater", "Fan", "Thermistor", "Sensor", "Link"]
BOARD_OF = {"Power input": "logic", "Logic supply": "power", "MCU": "logic", "CAN": "logic", "USB": "logic",
            "Heater": "power", "Fan": "power", "Thermistor": "logic", "Sensor": "logic"}
# board: KiCad project name in hardware/, title
BOARDS = {"logic": ("toolhead_logic", "24V CAN heater/fan controller - logic board"),
          "power": ("toolhead_power", "24V CAN heater/fan controller - power board")}
for p in PARTS:
    p["board"] = p["board"] or BOARD_OF[p["block"]]


def parts(board):
    return [p for p in PARTS if p["board"] == board]
