# CAN toolhead board – KiCad project

`tools/gen_kicad.py` generates the schematic from `tools/design.py`, the netlist. The PCB is routed. The project opens in KiCad 8 or newer; it was routed and checked in KiCad 10.

## What's here

| File | Contents |
| --- | --- |
| `toolhead_can.kicad_pro` | The project file: open this in KiCad. Netclasses: Power 0.8 / 0.3 mm, Fan 0.4 / 0.3 mm, Supply and USB 0.3 / 0.2 mm |
| `toolhead_can.kicad_sch` | Schematic: 63 parts. Blocks: power input, logic supply, MCU, CAN, USB, heater, the plug, fan, thermistor, switch |
| `toolhead_can.kicad_pcb` | The routed board: 27 × 34 mm, 4 layers, two M2 edge notches |
| `toolhead_can.kicad_dru` | Custom design rules: high-current nets 0.8 mm minimum, 0.3 mm clearance on the 24 V nets, the USB pair, the fan current |
| `toolhead_can-bom-jlcpcb.csv`, `bom_jlcpcb.csv` | The BOM in JLCPCB's upload format (the two are the same). The solder-jumper pads (JP1–JP3) are left out; every other part is placed |
| `panel/`, `panel6/`, `panel4/` | The panels to order: 9, 6 or 4 boards, built by `../tools/make_panel.sh` |
| `fp-lib-table`, `footprints/` | Project footprint library: Q2's AOS DFN 3 × 3 footprint |

`tools/verify.py` re-parses the schematic and rebuilds the netlist from pin and label positions. Every pin matches `tools/design.py`, and no pin is left dangling.

## Layout

| Layer | What's on it |
| --- | --- |
| F.Cu | J1, J3, J2, J5, SW1, LED1/LED2; F1, D1; Q2 with U7 and its 12 V rail (R13, D10, C21, R14). The heater's power path as pours (`tools/layout/can_pre.py`): VIN_RAW, the +24V strip, HEAT_N and the GND return. GND fill |
| In1 | Solid GND |
| In2 | Signals |
| B.Cu | U6 with Y1, FB1 and C9, C11–C15; CAN (U3, D4, R11, JP1, C16) under J1; JP3 with R4, C10; U5, C17, D3 and the thermistor network down the left; R5/R6 and the switch filter right of U6; C1, C2 under the strip; the fan driver (F2, Q3, D5, R15, R16) under J2; the buck (U1, L1, D9, D7, C4–C6, C8, R2, R3) under J3. GND fill |

- **Reference designators:** most bottom-side ones are on B.Fab rather than the silkscreen, because there is no room for them. They still appear on assembly drawings.

## Check against datasheets

- **J1 (JST S6B-XH-SM4-TB):** seen from the top with the plug opening at the top edge, pin 1 is on the right. 1–2 +24V, 3–4 GND, 5 CAN-H, 6 CAN-L.
- **J3 (JST S4B-XH-SM4-TB):** plug opening at the bottom edge, pin 1 on the left. 1–2 HEAT− (Q2's drain), 3–4 +24V.
- **J2 (JST SM06B-SRSS-TB):** plug opening at the bottom edge, pin 1 on the left. 1 FAN+, 2 FAN−, 3 TH_SIG, 4 thermistor GND, 5 SENS, 6 GND.
- **J5 (JST SM04B-SRSS-TB):** plug opening at the left edge, pin 1 at the top. 1 VBUS, 2 D−, 3 D+, 4 GND.
- **U1 (LMR16006XDDC):** 1 CB, 2 GND, 3 FB, 4 SHDN, 5 VIN, 6 SW.
- **U3 (TCAN3414DRBR):** 1 TXD, 2 GND, 3 VDD, 4 RXD, 5 SHDN (open), 6 CANL, 7 CANH, 8 STB (GND).
- **U7 (UCC27517DBVR):** 1 VDD, 2 GND, 3 IN+, 4 IN−, 5 OUT.
- **U6 STM32G0B1 pinout:** VREF+ 5, VDD/VDDA 6, VSS/VSSA 7, PB0/PB1 19/20, PB12/PB13 24/25, PA11/12 33/34, PA14/PA15 36/37, PB3 42, PB9 48. Confirm against ST DS13560.
- **Crystal Y1:** 20 pF load with 33 pF caps. Check the oscillator's gain margin (ST AN2867) on the first board.

## Net names

| Net | What it is |
| --- | --- |
| `VIN_RAW` | 24 V from J1, before F1 |
| `+24V` | After F1: the heater, the fan and D7 |
| `HEAT_N` | Q2's drain, the heater's low side |
| `VIN_LOGIC` | The buck's input: +24V through D7 or VBUS through D3 |
| `GATE_12V` | U7's zener-clamped supply |
| `VBUS` | USB 5 V from J5 |
| `+3V3` | The buck's output |
| `VREFP` | The ferrite-filtered ADC reference and thermistor pull-up |
| `CAN_H` / `CAN_L` | The bus |
| `FAN_P` / `FAN_N` | The fan + after F2, and Q3's drain |
| `TH_SIG` / `TH_ADC` | The thermistor, before and after its filter |
| `SENS` / `SENS_IN` | The switch, before and after its filter |

## Fab outputs

`../tools/fab.sh` exports `../gerber/can/` with `kicad-cli`: 4-layer gerbers, drill files, the BOM and the CPL. `tools/jlc_cpl.py` writes the CPL by fitting each part's own JLCPCB footprint onto its pads. The panels are in `../gerber/panel*/`. `../gerber/README.md` says which files to upload.
