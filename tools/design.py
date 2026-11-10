"""Single source of truth for the USB toolhead board.

Every part lists its symbol style, footprint (KiCad standard library name),
value, LCSC number and a {pin_number: net} map. Pins not listed are
no-connect. The generator builds the schematic and the BOM from this file,
so edit connections here, not in the outputs.

One board, powered and connected by USB-C alone: the STM32G0B1 runs Klipper
over USB, from a 3.3 V LDO on VBUS. It reads a thermistor and a switch sensor
and drives a 5 V fan from VBUS; the three share one 6-pin JST-SH plug. There is
no heater output, no 24 V and no CAN: the heater is wired straight to the
printer's mainboard. This is the two-board 24 V CAN stack (branch `stack`)
with the power input, CAN, heater and link taken out; parts it shares with the
stack's logic board keep their references, so their routed footprints carry
over (tools/layout/from_netlist.py).
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

# LDO: Microne ME6211C33, SOT-23-5: 1 VIN, 2 GND, 3 CE, 4 NC, 5 VOUT.
LDO_LAYOUT = ([(1, "VIN"), (3, "CE"), (2, "GND")], [(5, "VOUT"), (4, "NC")])
USBLC6_LAYOUT = ([(1, "IO1"), (6, "IO1"), (2, "GND")], [(3, "IO2"), (4, "IO2"), (5, "VBUS")])
SOT23FET_LAYOUT = ([(1, "G"), (2, "S")], [(3, "D")])
XTAL4_LAYOUT = ([(1, "X1"), (2, "GND")], [(3, "X2"), (4, "GND")])
BAT54S_LAYOUT = ([(1, "A1"), (2, "K2")], [(3, "K1/A2")])
CONN2_LAYOUT = ([(1, "1"), (2, "2")], [])
# 1x6 plug: fan pair, thermistor pair, switch pair.
CONN6_LAYOUT = ([(1, "FAN+"), (2, "FAN-"), (3, "THERM")], [(4, "TGND"), (5, "SENS"), (6, "GND")])
# USB-C 16-pin receptacle (USB 2.0): both rows of D+/D- and VBUS/GND, CC per row.
USBC_LAYOUT = (
    [("A4", "VBUS"), ("A9", "VBUS"), ("B4", "VBUS"), ("B9", "VBUS"), ("A5", "CC1"), ("B5", "CC2"),
     ("A8", "SBU1"), ("B8", "SBU2")],
    [("A6", "D+"), ("B6", "D+"), ("A7", "D-"), ("B7", "D-"), ("A1", "GND"), ("A12", "GND"),
     ("B1", "GND"), ("B12", "GND"), ("SH", "SHIELD")],
)

# Footprints (KiCad 8 standard libraries). "" = assign after choosing part.
FP = {
    "R0402": "Resistor_SMD:R_0402_1005Metric",
    "C0402": "Capacitor_SMD:C_0402_1005Metric",
    "C0805": "Capacitor_SMD:C_0805_2012Metric",
    "L0402": "Inductor_SMD:L_0402_1005Metric",
    "LED0603": "LED_SMD:LED_0603_1608Metric",
    "SOD123F": "Diode_SMD:D_SOD-123F",
    "SOT23": "Package_TO_SOT_SMD:SOT-23",
    "SOT235": "Package_TO_SOT_SMD:SOT-23-5",
    "SOT236": "Package_TO_SOT_SMD:SOT-23-6",
    "QFN48": "Package_DFN_QFN:QFN-48-1EP_7x7mm_P0.5mm_EP5.6x5.6mm",  # ST UFQFPN48
    "XTAL3225": "Crystal:Crystal_SMD_3225-4Pin_3.2x2.5mm",
    "F1206": "Fuse:Fuse_1206_3216Metric",
    "SW": "Button_Switch_SMD:SW_SPST_EVQP7C",  # side-push, 3.5 x 2.9 mm
    "SJ": "Jumper:SolderJumper-2_P1.3mm_Open_RoundedPad1.0x1.5mm",
    "SH6": "Connector_JST:JST_SH_SM06B-SRSS-TB_1x06-1MP_P1.00mm_Horizontal",
    "USBC16": "Connector_USB:USB_C_Receptacle_HRO_TYPE-C-31-M-12",
}


def P(ref, kind, value, fp, nets, lcsc="", dnp=False, block="", layout=None, board=None):
    return dict(ref=ref, kind=kind, value=value, fp=FP.get(fp, fp), nets=nets,
                lcsc=lcsc, dnp=dnp, block=block, layout=layout, board=board)


def two(ref, kind, value, fp, n1, n2, **kw):
    return P(ref, kind, value, fp, {1: n1, 2: n2}, **kw)


# Diodes and LEDs follow the KiCad footprint convention: pad 1 = cathode.
PARTS = [
    # ---------------- Logic supply ----------------
    # VBUS straight to a 3.3 V LDO; the logic draws under 50 mA, about 0.1 W in U1
    P("U1", "box", "ME6211C33M5G-N", "SOT235",
      {1: "VBUS", 3: "VBUS", 2: "GND", 5: "+3V3"},
      lcsc="C82942", block="Logic supply", layout=LDO_LAYOUT),
    two("C4", "C", "1uF", "C0402", "VBUS", "GND", lcsc="C52923", block="Logic supply"),
    two("C8", "C", "1uF", "C0402", "+3V3", "GND", lcsc="C52923", block="Logic supply"),
    # ---------------- MCU ----------------
    # The 512 KB CEU6 (C2829190): same pinout and package as the stack's 128 KB CBU6,
    # which JLCPCB had only 6 of in November 2026. The crystal is required: Klipper's STM32G0
    # code clocks USB from the PLL, and the internal oscillator is outside USB's 0.25%.
    # Fan, switch and status LED are on the pins nearest their parts (Klipper drives a fan or
    # reads a switch on any GPIO): fan PB13 at the corner by the thermistor's PB12, status LED
    # PA15 next to SWCLK, switch PB8 down the side facing J2's switch pin.
    P("U6", "box", "STM32G0B1CEU6", "QFN48",
      {4: "+3V3", 5: "VREFP", 6: "+3V3", 7: "GND", 8: "OSC_IN", 9: "OSC_OUT",
       10: "NRST", 24: "TH_ADC", 25: "FAN_PWM",
       33: "USB_D_N", 34: "USB_D_P", 36: "SWCLK",
       37: "LED_STAT", 47: "SENS_IN", 49: "GND"},
      lcsc="C2829190", block="MCU", layout=STM32_LAYOUT),
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
    # ---------------- Plug ----------------
    # One 1x6 1 mm JST-SH, right-angle SMD (1 A per contact, 28-32 AWG): fan, thermistor,
    # switch. A third of the PH's footprint, which set the 22 x 30 board's size
    P("J2", "box", "Fan/therm/sensor (JST SH 1x6 SM06B-SRSS-TB)", "SH6",
      {1: "FAN_P", 2: "FAN_N", 3: "TH_SIG", 4: "GND", 5: "SENS", 6: "GND"},
      lcsc="C160405", block="Plug", layout=CONN6_LAYOUT),
    # ---------------- Fan (5 V from VBUS) ----------------
    # 0.5 A hold at 25 C, about 0.33 A at 70 C: a 5 V fan of 0.3 A or less, which a USB 2.0
    # port (0.5 A) can supply with the logic
    two("F2", "R", "PTC 0.5A 16V (BSMD1206-050-16V)", "F1206", "VBUS", "FAN_P", lcsc="C883124", block="Fan"),
    P("Q3", "box", "WST6066A", "SOT23",
      {1: "FAN_G", 2: "GND", 3: "FAN_N"},
      lcsc="C148352", block="Fan", layout=SOT23FET_LAYOUT),
    two("D5", "D", "DSK110 100V 1A", "SOD123F", "FAN_P", "FAN_N", lcsc="C22466354", block="Fan"),
    two("R15", "R", "1k", "R0402", "FAN_PWM", "FAN_G", block="Fan"),
    two("R16", "R", "10k", "R0402", "FAN_PWM", "GND", block="Fan"),
    # ---------------- Thermistor ----------------
    two("R17", "R", "4.7k 0.1% 25ppm", "R0402", "VREFP", "TH_SIG", lcsc="C281778", block="Thermistor"),
    two("R18", "R", "4.12k 0.1% 25ppm", "R0402", "VREFP", "JP2_A", lcsc="C852812", block="Thermistor"),
    # Solder jumper: open for a 100k NTC (4.7k pull-up), bridged for a PT1000 (R18 in
    # parallel, 2.2k)
    two("JP2", "R", "NTC/PT1000", "SJ", "TH_SIG", "JP2_A", block="Thermistor"),
    two("R19", "R", "1k", "R0402", "TH_SIG", "TH_ADC", block="Thermistor"),
    two("C19", "C", "100nF", "C0402", "TH_ADC", "GND", lcsc="C1525", block="Thermistor"),
    P("D6", "box", "BAT54S", "SOT23", {1: "GND", 2: "+3V3", 3: "TH_ADC"},
      lcsc="C7420333", block="Thermistor", layout=BAT54S_LAYOUT),
    # ---------------- Switch sensor (endstop / runout, switch to GND) ----------------
    two("R22", "R", "10k", "R0402", "+3V3", "SENS", block="Sensor"),
    two("R23", "R", "1k", "R0402", "SENS", "SENS_IN", block="Sensor"),
    two("C20", "C", "100nF", "C0402", "SENS_IN", "GND", lcsc="C1525", block="Sensor"),
]

# LCSC numbers were checked against JLCPCB's part search (stock and type) in
# November 2026; 0402 0R/1k/10k get JLCPCB basic parts.
for p in PARTS:
    if p["kind"] == "R" and p["fp"].endswith("R_0402_1005Metric") and not p["lcsc"]:
        p["lcsc"] = {"0R": "C17168", "1k": "C11702", "10k": "C25744"}.get(p["value"], "")

BLOCK_ORDER = ["Logic supply", "MCU", "USB", "Plug", "Fan", "Thermistor", "Sensor"]
# board: KiCad project name in hardware/, title
BOARDS = {"usb": ("toolhead_usb", "USB toolhead board - fan, thermistor and switch")}
for p in PARTS:
    p["board"] = p["board"] or "usb"


def parts(board):
    return [p for p in PARTS if p["board"] == board]
