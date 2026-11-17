# CAN toolhead stack – KiCad projects

`tools/gen_kicad.py` generates both schematics from `tools/design.py`, the netlist. The PCBs are routed. The projects open in KiCad 8 or newer; they were routed and checked in KiCad 10.

## What's here

| File | Contents |
| --- | --- |
| `toolhead_logic.kicad_pro`, `.kicad_sch`, `.kicad_pcb`, `.kicad_dru` | The logic board (upper): 46 parts. Power input, MCU, CAN, USB, the plug J2, fan, thermistor, switch, the link socket J6. 25 × 26 mm, 4 layers, two M2 edge notches |
| `toolhead_power.kicad_pro`, `.kicad_sch`, `.kicad_pcb`, `.kicad_dru` | The power board (lower): 19 parts. The heater plug J3, heater FET and gate driver, 3.3 V buck, the link header J7. Same outline and notches |
| `toolhead_logic-bom-jlcpcb.csv`, `toolhead_power-bom-jlcpcb.csv`, `bom_jlcpcb.csv` | BOMs in JLCPCB's upload format, per board and for both together. The solder-jumper pads (JP1–JP3) are left out; every other part is placed |
| `panel/`, `panel6/`, `panel4/` | The panels to order: 9, 6 or 4 logic/power pairs, built by `../tools/make_panel.sh` |
| `fp-lib-table`, `footprints/` | Project footprint library: Q2's AOS DFN 3 × 3 footprint |

Netclasses (both boards): Power 0.8 / 0.3 mm, Fan 0.4 / 0.3 mm, Supply and USB 0.3 / 0.2 mm. The design rules add 0.8 mm minimum on the high-current nets, 0.3 mm clearance on the 24 V nets, the USB pair and the fan current.

`tools/verify.py` re-parses both schematics and rebuilds the netlists from pin and label positions: every pin matches `tools/design.py`, no pin is left dangling, and J6 and J7 carry the same net on every pin. `tools/check_stack.py` checks the routed boards: same outline and notches, and every J7 pin under its J6 contact.

## Layout

| Board | Layer | What's on it |
| --- | --- | --- |
| Logic | F.Cu | J1, J2, J5; F1, D1, F2; Q3, D5, R15, R16; LED1/LED2 with R5/R6. VIN_RAW and +24V pours. GND fill |
| Logic | B.Cu | U6 with Y1, FB1 and C9, C11–C15; CAN (U3, D4, R11, JP1, C16); J6; U5, C17, D3; C1; JP3 with R4, C10; the thermistor network and switch filter; SW1. +24V and GND pours on J6. GND fill |
| Power | F.Cu | J7, J3, Q2, U7 with R13, D10, C21, R14; C2; the buck (U1, L1, D9, D7, C4–C6, C8, R2, R3). +24V, HEAT_N and GND pours. GND fill |
| Power | B.Cu | GND fill; J7's pin ends |
| Both | In1 / In2 | Solid GND / signals |

- **Reference designators:** most bottom-side ones are on B.Fab rather than the silkscreen, because there is no room for them. They still appear on assembly drawings.

## Check against datasheets

- **J1 (JST S6B-XH-SM4-TB):** seen from the top with the plug opening at the top edge, pin 1 is on the right. 1–2 +24V, 3–4 GND, 5 CAN-H, 6 CAN-L.
- **J2 (JST SM06B-SRSS-TB):** plug opening at the bottom edge, pin 1 on the left. 1 FAN+, 2 FAN−, 3 TH_SIG, 4 thermistor GND, 5 SENS, 6 GND.
- **J5 (JST SM04B-SRSS-TB):** plug opening at the left edge, pin 1 at the top. 1 VBUS, 2 D−, 3 D+, 4 GND.
- **J3 (JST S4B-XH-SM4-TB, power board):** plug opening at the bottom edge, pin 1 on the left. 1–2 HEAT− (Q2's drain), 3–4 +24V.
- **J6/J7 (the link):** 1–2 +24V, 3, 4 and 6 GND, 5 VIN_LOGIC, 7 HEAT_PWM, 8 +3V3.
- **U1 (LMR16006XDDC):** 1 CB, 2 GND, 3 FB, 4 SHDN, 5 VIN, 6 SW.
- **U3 (TCAN3414DRBR):** 1 TXD, 2 GND, 3 VDD, 4 RXD, 5 SHDN (open), 6 CANL, 7 CANH, 8 STB (GND).
- **U7 (UCC27517DBVR):** 1 VDD, 2 GND, 3 IN+, 4 IN−, 5 OUT.
- **U6 STM32G0B1 pinout:** VREF+ 5, VDD/VDDA 6, VSS/VSSA 7, PB0/PB1 19/20, PB12/PB13 24/25, PA11/12 33/34, PA14/PA15 36/37, PD0 38, PB3 42. Confirm against ST DS13560.
- **Crystal Y1:** 20 pF load with 33 pF caps. Check the oscillator's gain margin (ST AN2867) on the first board.

## Net names

| Net | What it is |
| --- | --- |
| `VIN_RAW` | 24 V from J1, before F1 |
| `+24V` | After F1: the fan, the link to the heater and D7 |
| `HEAT_N` | Q2's drain, the heater's low side |
| `VIN_LOGIC` | The buck's input: +24V through D7 or VBUS through D3 |
| `GATE_12V` | U7's zener-clamped supply |
| `HEAT_PWM` | PD0 to U7, across the link |
| `VBUS` | USB 5 V from J5 |
| `+3V3` | The buck's output, across the link |
| `VREFP` | The ferrite-filtered ADC reference and thermistor pull-up |
| `CAN_H` / `CAN_L` | The bus |
| `FAN_P` / `FAN_N` | The fan + after F2, and Q3's drain |
| `TH_SIG` / `TH_ADC` | The thermistor, before and after its filter |
| `SENS` / `SENS_IN` | The switch, before and after its filter |

## Fab outputs

`../tools/fab.sh` exports `../gerber/logic/` and `../gerber/power/` with `kicad-cli`: 4-layer gerbers, drill files, the BOM and the CPL. `tools/jlc_cpl.py` writes each CPL by fitting each part's own JLCPCB footprint onto its pads. The panels are in `../gerber/panel*/`. `../gerber/README.md` says which files to upload.
