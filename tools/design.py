"""Single source of truth for the 24 V CAN heater/fan controller.

Every part lists its symbol style, footprint (KiCad standard library name),
value, LCSC number and a {pin_number: net} map. Pins not listed are
no-connect. The generator builds the schematic, the PCB starter file and the
BOM from this file, so edit connections here, not in the outputs.
"""

# ---------------------------------------------------------------------------
# Symbol pin layouts for multi-pin parts: (left pins, right pins),
# each pin is (number, name).
# ---------------------------------------------------------------------------
STM32_PINS = {
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
                                  32, 33, 34, 35, 36, 37, 42, 43, 44, 45, 46, 47, 48]],
)

# Buck: TI LMR16006X (60 V, 0.6 A, 0.7 MHz), SOT-23-6 "DDC" package.
# Pinout per TI datasheet: 1 CB, 2 GND, 3 FB, 4 SHDN, 5 VIN, 6 SW.
BUCK_LAYOUT = (
    [(5, "VIN"), (4, "SHDN"), (2, "GND")],
    [(1, "CB"), (6, "SW"), (3, "FB")],
)
CAN_LAYOUT = (
    [(1, "TXD"), (4, "RXD"), (8, "STBY"), (5, "PIN5_CHECK")],
    [(3, "VDD"), (7, "CANH"), (6, "CANL"), (2, "GND")],
)
USBLC6_LAYOUT = ([(1, "IO1"), (6, "IO1"), (2, "GND")], [(3, "IO2"), (4, "IO2"), (5, "VBUS")])
FET_LAYOUT = ([(4, "G"), (1, "S"), (2, "S"), (3, "S")], [(5, "D")])
SOT3_LAYOUT = ([(1, "1"), (2, "2")], [(3, "3")])
BAT54S_LAYOUT = ([(1, "A1"), (2, "K2")], [(3, "K1/A2")])
TC2030_LAYOUT = ([(1, "VCC"), (2, "SWDIO"), (3, "NRST")], [(4, "SWCLK"), (5, "GND"), (6, "SWO")])
XT30_LAYOUT = ([(1, "P+"), (2, "P-")], [(3, "S1"), (4, "S2")])
CONN2_LAYOUT = ([(1, "1"), (2, "2")], [])
CONN4_LAYOUT = ([(1, "1"), (2, "2"), (3, "3"), (4, "4")], [])
CONN6_LAYOUT = ([(1, "FAN+"), (2, "FAN-"), (3, "THERM"), (4, "TGND"), (5, "SENS"), (6, "GND")], [])
# USB-C 16-pin receptacle (USB 2.0): both rows of D+/D- and VBUS/GND, CC per row.
USBC_LAYOUT = (
    [("A4", "VBUS"), ("A9", "VBUS"), ("B4", "VBUS"), ("B9", "VBUS"), ("A5", "CC1"), ("B5", "CC2"),
     ("A8", "SBU1"), ("B8", "SBU2")],
    [("A6", "D+"), ("B6", "D+"), ("A7", "D-"), ("B7", "D-"), ("A1", "GND"), ("A12", "GND"),
     ("B1", "GND"), ("B12", "GND"), ("SH", "SHIELD")],
)

# Footprints (KiCad 8 standard libraries). "" = assign after choosing part.
FP = {
    "R0603": "Resistor_SMD:R_0603_1608Metric",
    "R0805": "Resistor_SMD:R_0805_2012Metric",
    "C0603": "Capacitor_SMD:C_0603_1608Metric",
    "C0805": "Capacitor_SMD:C_0805_2012Metric",
    "C1206": "Capacitor_SMD:C_1206_3216Metric",
    "CPEL": "Capacitor_SMD:CP_Elec_6.3x7.7",
    "L0603": "Inductor_SMD:L_0603_1608Metric",
    "L4040": "Inductor_SMD:L_Taiyo-Yuden_NR-40xx",
    "LED0603": "LED_SMD:LED_0603_1608Metric",
    "SMA": "Diode_SMD:D_SMA",
    "SMB": "Diode_SMD:D_SMB",
    "SOD123": "Diode_SMD:D_SOD-123",
    "SOT23": "Package_TO_SOT_SMD:SOT-23",
    "SOT236": "Package_TO_SOT_SMD:SOT-23-6",
    "SOIC8": "Package_SO:SOIC-8_3.9x4.9mm_P1.27mm",
    "LQFP48": "Package_QFP:LQFP-48_7x7mm_P0.5mm",
    "PPAK1212": "Package_SO:Vishay_PowerPAK_1212-8_Single",
    "PPAKSO8": "Package_SO:PowerPAK_SO-8_Single",
    "XTAL5032": "Crystal:Crystal_SMD_5032-2Pin_5.0x3.2mm",
    "F1206": "Fuse:Fuse_1206_3216Metric",
    "F1812": "Fuse:Fuse_1812_4532Metric",
    "SW": "Button_Switch_SMD:SW_SPST_TL3342",
    "SJ": "Jumper:SolderJumper-2_P1.3mm_Open_RoundedPad1.0x1.5mm",
    "HDR2": "Connector_PinHeader_2.54mm:PinHeader_1x02_P2.54mm_Vertical",
    "GH6H": "Connector_JST:JST_GH_SM06B-GHS-TB_1x06-1MP_P1.25mm_Horizontal",
    "USBC16": "Connector_USB:USB_C_Receptacle_HRO_TYPE-C-31-M-12",
    "NANOFIT2": "Connector_Molex:Molex_Nano-Fit_105313-xx02_1x02_P2.50mm_Horizontal",
    "TC2030": "Connector:Tag-Connect_TC2030-IDC-NL_2x03_P1.27mm_Vertical",
}


def P(ref, kind, value, fp, nets, lcsc="", dnp=False, block="", layout=None):
    return dict(ref=ref, kind=kind, value=value, fp=FP.get(fp, fp), nets=nets,
                lcsc=lcsc, dnp=dnp, block=block, layout=layout)


def two(ref, kind, value, fp, n1, n2, **kw):
    return P(ref, kind, value, fp, {1: n1, 2: n2}, **kw)


# Diodes and LEDs follow the KiCad footprint convention: pad 1 = cathode.
PARTS = [
    # ---------------- Power input ----------------
    P("J1", "box", "XT30PW(2+2)-M.G.B", "hotswap_toolhead:XT30PW-2+2-M",
      {1: "VIN_RAW", 2: "GND", 3: "CAN_S1", 4: "CAN_S2"},
      lcsc="C19268030", block="Power input", layout=XT30_LAYOUT),
    two("F1", "R", "6.3A fast", "F1206", "VIN_RAW", "VIN_F", block="Power input"),
    two("D1", "D", "SMBJ33CA", "SMB", "VIN_F", "GND", block="Power input"),
    P("Q1", "box", "P-FET 60V >=8A", "PPAKSO8",
      {1: "+24V", 2: "+24V", 3: "+24V", 4: "Q1_G", 5: "VIN_F"},
      block="Power input", layout=FET_LAYOUT),
    two("D2", "D", "12V zener", "SOD123", "+24V", "Q1_G", block="Power input"),
    two("R1", "R", "10k", "R0603", "Q1_G", "GND", block="Power input"),
    two("C1", "CP", "47uF 50V 105C", "CPEL", "+24V", "GND", block="Power input"),
    two("C2", "C", "10uF 50V X5R", "C1206", "+24V", "GND", lcsc="C13585", block="Power input"),
    two("C3", "C", "10uF 50V X5R", "C1206", "+24V", "GND", lcsc="C13585", block="Power input"),
    # ---------------- Logic supply ----------------
    two("D7", "D", "SS210", "SMA", "VIN_LOGIC", "+24V", lcsc="C14996", block="Logic supply"),
    two("D3", "D", "SS210", "SMA", "VIN_LOGIC", "VBUS", lcsc="C14996", block="Logic supply"),
    two("C4", "C", "10uF 50V X5R", "C1206", "VIN_LOGIC", "GND", lcsc="C13585", block="Logic supply"),
    two("C5", "C", "100nF", "C0603", "VIN_LOGIC", "GND", lcsc="C14663", block="Logic supply"),
    P("U1", "box", "LMR16006XDDC", "SOT236",
      {5: "VIN_LOGIC", 4: "VIN_LOGIC", 2: "GND", 1: "BUCK_BOOT", 6: "BUCK_SW", 3: "BUCK_FB"},
      block="Logic supply", layout=BUCK_LAYOUT),
    two("C6", "C", "100nF", "C0603", "BUCK_BOOT", "BUCK_SW", lcsc="C14663", block="Logic supply"),
    two("D9", "D", "SS210", "SMA", "BUCK_SW", "GND", lcsc="C14996", block="Logic supply"),
    two("L1", "L", "22uH (per datasheet)", "L4040", "BUCK_SW", "+3V3", block="Logic supply"),
    two("C8", "C", "22uF 25V X5R", "C1206", "+3V3", "GND", lcsc="C12891", block="Logic supply"),
    two("R2", "R", "FB top (datasheet)", "R0603", "+3V3", "BUCK_FB", block="Logic supply"),
    two("R3", "R", "10k", "R0603", "BUCK_FB", "GND", block="Logic supply"),
    # ---------------- MCU ----------------
    P("U6", "box", "STM32G0B1CBT7", "LQFP48",
      {4: "+3V3", 5: "VREFP", 6: "+3V3", 7: "GND", 8: "OSC_IN", 9: "OSC_OUT",
       10: "NRST", 11: "FAN_PWM", 12: "SENS_IN", 14: "TH_ADC", 19: "CAN_RX", 20: "CAN_TX",
       25: "HEAT_PWM", 33: "USB_D_N", 34: "USB_D_P", 35: "SWDIO", 36: "SWCLK",
       44: "LED_STAT"},
      block="MCU", layout=STM32_LAYOUT),
    two("C9", "C", "100nF", "C0603", "+3V3", "GND", lcsc="C14663", block="MCU"),
    two("C10", "C", "10uF 25V X5R", "C0805", "+3V3", "GND", lcsc="C15850", block="MCU"),
    two("FB1", "L", "600R@100MHz", "L0603", "+3V3", "VREFP", lcsc="C1002", block="MCU"),
    two("C11", "C", "1uF", "C0603", "VREFP", "GND", lcsc="C15849", block="MCU"),
    two("C12", "C", "100nF", "C0603", "VREFP", "GND", lcsc="C14663", block="MCU"),
    two("Y1", "R", "8MHz 20pF", "XTAL5032", "OSC_IN", "OSC_OUT", lcsc="C115962", block="MCU"),
    two("C13", "C", "33pF C0G", "C0603", "OSC_IN", "GND", lcsc="C1663", block="MCU"),
    two("C14", "C", "33pF C0G", "C0603", "OSC_OUT", "GND", lcsc="C1663", block="MCU"),
    two("C15", "C", "100nF", "C0603", "NRST", "GND", lcsc="C14663", block="MCU"),
    two("SW1", "R", "RESET", "SW", "NRST", "GND", block="MCU"),
    two("SW2", "R", "BOOT", "SW", "+3V3", "BOOT_SW", block="MCU"),
    two("R4", "R", "1k", "R0603", "BOOT_SW", "SWCLK", block="MCU"),
    P("J6", "box", "TC2030 SWD", "TC2030",
      {1: "+3V3", 2: "SWDIO", 3: "NRST", 4: "SWCLK", 5: "GND"}, block="MCU", layout=TC2030_LAYOUT),
    two("R5", "R", "1k", "R0603", "+3V3", "LED1_A", block="MCU"),
    two("LED1", "D", "green", "LED0603", "GND", "LED1_A", block="MCU"),
    two("R6", "R", "1k", "R0603", "LED_STAT", "LED2_A", block="MCU"),
    two("LED2", "D", "blue", "LED0603", "GND", "LED2_A", block="MCU"),
    # ---------------- CAN ----------------
    two("R7", "R", "0R", "R0603", "CAN_S1", "CAN_H", block="CAN"),
    two("R8", "R", "0R", "R0603", "CAN_S2", "CAN_L", block="CAN"),
    two("R9", "R", "0R", "R0603", "CAN_S1", "CAN_L", dnp=True, block="CAN"),
    two("R10", "R", "0R", "R0603", "CAN_S2", "CAN_H", dnp=True, block="CAN"),
    P("D4", "box", "NUP2105L", "SOT23", {1: "CAN_H", 2: "CAN_L", 3: "GND"},
      block="CAN", layout=SOT3_LAYOUT),
    two("R11", "R", "120R", "R0805", "CAN_H", "CAN_TERM", lcsc="C17437", block="CAN"),
    two("JP1", "R", "TERM", "SJ", "CAN_TERM", "CAN_L", block="CAN"),
    P("U3", "box", "MAX33012E (check pin 5)", "SOIC8",
      {1: "CAN_TX", 2: "GND", 3: "+3V3", 4: "CAN_RX", 5: "CAN_P5", 6: "CAN_L", 7: "CAN_H", 8: "GND"},
      block="CAN", layout=CAN_LAYOUT),
    two("C16", "C", "100nF", "C0603", "+3V3", "GND", lcsc="C14663", block="CAN"),
    two("R12", "R", "0R", "R0603", "CAN_P5", "+3V3", dnp=True, block="CAN"),
    # ---------------- USB ----------------
    P("J5", "box", "USB-C (HRO TYPE-C-31-M-12)", "USBC16",
      {"A4": "VBUS", "A9": "VBUS", "B4": "VBUS", "B9": "VBUS", "A5": "USB_CC1", "B5": "USB_CC2",
       "A6": "USB_D_P", "B6": "USB_D_P", "A7": "USB_D_N", "B7": "USB_D_N",
       "A1": "GND", "A12": "GND", "B1": "GND", "B12": "GND", "SH": "GND"},
      lcsc="C165948", block="USB", layout=USBC_LAYOUT),
    # 5.1k pull-downs on CC1/CC2 so a USB-C host or charger turns VBUS on.
    two("R20", "R", "5.1k", "R0603", "USB_CC1", "GND", lcsc="C23186", block="USB"),
    two("R21", "R", "5.1k", "R0603", "USB_CC2", "GND", lcsc="C23186", block="USB"),
    P("U5", "box", "USBLC6-2SC6", "SOT236",
      {1: "USB_D_N", 6: "USB_D_N", 2: "GND", 3: "USB_D_P", 4: "USB_D_P", 5: "VBUS"},
      block="USB", layout=USBLC6_LAYOUT),
    two("C17", "C", "10uF 25V X5R", "C0805", "VBUS", "GND", lcsc="C15850", block="USB"),
    # ---------------- Heater ----------------
    P("J2", "box", "Heater (Nano-Fit 2)", "NANOFIT2", {1: "+24V", 2: "HEAT_N"},
      block="Heater", layout=CONN2_LAYOUT),
    P("Q2", "box", "N-FET 60V <=30mR@2.5V", "PPAK1212",
      {1: "GND", 2: "GND", 3: "GND", 4: "HEAT_G", 5: "HEAT_N"},
      block="Heater", layout=FET_LAYOUT),
    two("R13", "R", "10k", "R0603", "HEAT_PWM", "HEAT_G", block="Heater"),
    two("R14", "R", "10k", "R0603", "HEAT_PWM", "GND", block="Heater"),
    # ---------------- Fan ----------------
    two("F2", "R", "PTC 0.75A hold 30V", "F1812", "+24V", "FAN_P", block="Fan"),
    # One latching 6-pin plug for fan, thermistor and a 2-wire switch sensor.
    P("J3", "box", "Fan/therm/sensor (JST-GH 6)", "GH6H",
      {1: "FAN_P", 2: "FAN_N", 3: "TH_SIG", 4: "GND", 5: "SENS", 6: "GND"},
      block="Fan", layout=CONN6_LAYOUT),
    P("Q3", "box", "N-FET 60V <=30mR@2.5V", "PPAK1212",
      {1: "GND", 2: "GND", 3: "GND", 4: "FAN_G", 5: "FAN_N"},
      block="Fan", layout=FET_LAYOUT),
    two("D5", "D", "SS210", "SMA", "FAN_P", "FAN_N", lcsc="C14996", block="Fan"),
    two("R15", "R", "1k", "R0603", "FAN_PWM", "FAN_G", block="Fan"),
    two("R16", "R", "10k", "R0603", "FAN_PWM", "GND", block="Fan"),
    two("C18", "C", "100nF 50V", "C0603", "FAN_P", "FAN_N", lcsc="C14663", dnp=True, block="Fan"),
    # ---------------- Thermistor ----------------
    two("R17", "R", "4.7k 0.1% 25ppm", "R0603", "VREFP", "TH_SIG", block="Thermistor"),
    two("R18", "R", "4.12k 0.1% 25ppm", "R0603", "VREFP", "JP2_A", block="Thermistor"),
    P("JP2", "box", "NTC/PT1000", "HDR2", {1: "JP2_A", 2: "TH_SIG"},
      block="Thermistor", layout=CONN2_LAYOUT),
    two("R19", "R", "1k", "R0603", "TH_SIG", "TH_ADC", block="Thermistor"),
    two("C19", "C", "100nF", "C0603", "TH_ADC", "GND", lcsc="C14663", block="Thermistor"),
    P("D6", "box", "BAT54S", "SOT23", {1: "GND", 2: "+3V3", 3: "TH_ADC"},
      block="Thermistor", layout=BAT54S_LAYOUT),
    # ---------------- Switch sensor (endstop / runout, switch to GND) ----------------
    two("R22", "R", "10k", "R0603", "+3V3", "SENS", block="Sensor"),
    two("R23", "R", "1k", "R0603", "SENS", "SENS_IN", block="Sensor"),
    two("C20", "C", "100nF", "C0603", "SENS_IN", "GND", lcsc="C14663", block="Sensor"),
]

# Only LCSC numbers checked against JLCPCB's basic list are filled in;
# pick basic 0603 1k/10k in the JLCPCB part search when ordering.
for p in PARTS:
    if p["kind"] == "R" and p["fp"].endswith("R_0603_1608Metric") and not p["lcsc"]:
        p["lcsc"] = {"0R": "C21189"}.get(p["value"], "")

BLOCK_ORDER = ["Power input", "Logic supply", "MCU", "CAN", "USB", "Heater", "Fan", "Thermistor", "Sensor"]
