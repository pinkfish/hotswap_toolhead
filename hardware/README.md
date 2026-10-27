# 24 V CAN heater/fan controller – KiCad project

The schematic is generated from `tools/design.py` (the netlist) by `tools/gen_kicad.py`; the PCB is routed. Opens in KiCad 8 or newer (routed and checked in KiCad 10).

## What's here

| File | Contents |
| --- | --- |
| `toolhead.kicad_pro` | Project file – open this in KiCad |
| `toolhead.kicad_sch` | Full schematic: 71 parts, 44 nets, grouped by function. Every pin is tied to its net with a net label, so there are no wires to trace. |
| `toolhead.kicad_pcb` | Routed board: 31 × 35 mm, 4 layers, two M3 insert holes. The generator writes a starter here only if the file is missing |
| `toolhead.kicad_pro` | Project file with the netclasses used for routing: Power 0.8 mm / 0.3 mm, Fan 0.4 / 0.3, Supply and USB 0.3 / 0.2 |
| `toolhead.kicad_dru` | Custom design rules: high-current track widths, 24 V clearance, USB pair |
| `place_footprints.py` | Puts every footprint where it sits on the routed board (only needed when rebuilding a board from scratch) |
| `bom_jlcpcb.csv` | BOM in JLCPCB's upload format; DNP parts and the solder-jumper pads (JP1, JP3) excluded |
| `fp-lib-table`, `footprints/` | Project footprint library: the XT30(2+2) connector (J1) and the AON7264E DFN 3×3 (Q2, land pattern from the LCSC/EasyEDA footprint for C431191) |
| `../tools/` | Generator source: edit `tools/design.py`, then run `python3 tools/gen_kicad.py` and `python3 tools/verify.py` |

The schematic was checked by re-parsing the file and rebuilding the netlist from pin and label positions: every pin matches `tools/design.py`, with no dangling pins.

## Layout

- **Stackup:** F.Cu (connectors, SW1, LEDs, C1, JP1–JP3, Q2, R11, R13, R14; GND pour), In1 solid GND, In2 solid +24V, B.Cu (all other parts; GND pour). Signals route on F.Cu and B.Cu only.
- **Heater current path:** J1 pin 1 → VIN_RAW pour (B.Cu) → F1 → VIN_F pour (B.Cu) → Q1 → +24V pour on Q1's source with a via array → In2 plane → J2 pin 1 → heater → J2 pin 5 → 0.8 mm tracks and a 30 mm² HEAT_N pour on F.Cu → Q2 → source bar and 3 vias → In1 GND plane.
- **MCU corner:** crystal, load caps, VDD/VREF+ decoupling and FB1 sit directly under U6's pins 4–10; +3V3 pins 4 and 6 drop to staggered vias so VREF+ (pin 5) runs straight down to C11/C12. NRST, OSC_OUT and OSC_IN are pre-routed in that order under the pin row, and the crystal's GND pads tie across to each other and to C13/C15.
- **USB-C:** D+ (B6/A6) strapped above the pad row and D− (A7/B7) below it on F.Cu, one via per pair down to U5. The pair then crosses once below U5 (D− on B.Cu between D3's pads) because U6 takes it in the opposite order, and runs on F.Cu to vias beside pins 33/34; C1 sits at y 14.6 to leave room for them.
- **Routing:** USB, the crystal/NRST corner, TH_ADC, HEAT_PWM and the buck's VIN_LOGIC/BUCK_SW links are pre-routed by script; the rest is autorouted (Freerouting 1.9.0) and finished with a scripted maze router, so it is functional rather than hand-tidy. Review the crystal, USB and CAN paths before ordering.
- **DRC:** 0 errors, 0 unconnected and schematic parity clean with the custom rules. The 7 remaining warnings are expected: J1, J2 and J5 silkscreen at the board edge (the connectors sit on it on purpose), and H1/H2 courtyards changed from the library footprint to match the insert keep-out.

Most bottom-side reference designators are on B.Fab rather than the silkscreen (there is no room for them); they still appear on assembly drawings.

## Before ordering

- **U1 (TI LMR16006XDDC, 60 V buck):** footprint `Package_TO_SOT_SMD:SOT-23-6`, pins 1 CB, 2 GND, 3 FB, 4 SHDN, 5 VIN, 6 SW. It is non-synchronous, so D9 (DSK110) is its catch diode from SW to GND. L1 = 22 µH (FNR4030S220MT); R2 = 33 kΩ over R3 = 10 kΩ gives 3.29 V (V_FB = 0.765 V).
- **J1 (XT30PW(2+2)-M.G.B, LCSC C19268030):** footprint is in `footprints/hotswap_toolhead.pretty/XT30PW-2+2-M.kicad_mod`. Check its pad numbers against the datasheet before ordering: 1 = power +, 2 = power −, 3 = signal S1, 4 = signal S2, so +24V doesn't end up on the wrong pin.

## Check against datasheets

- **Q1 PowerPAK and Q2 DFN footprints:** KiCad's PowerPAK SO-8 `_Single` footprint (Q1) and the project's AOS DFN 3×3 footprint (Q2) both have 5 pads (1–3 source, 4 gate, 5 drain tab), and the symbols match that. Q3 is a SOT-23 (1 G, 2 S, 3 D).

- **U6 STM32G0B1 pinout:** from the G0 LQFP-48 pinout (VREF+ pin 5, VDD/VDDA 6, VSS/VSSA 7, PB0/PB1 19/20, PA11/12 33/34, PB9 48). Confirm against ST DS13560.
- **U3 CAN transceiver (TCAN3414DRBR, VSON-8):** pin 5 is SHDN (high = shutdown, internal pull-down) and is left open. R12 (DNP) would tie it to +3V3 and switch the transceiver off, so never fit it. A TCAN3413 (pin 5 = VIO) would need R12 fitted.
- **Crystal Y1:** 20 pF load with 33 pF caps – check oscillator gain margin (ST AN2867) on the first board.

## Net names

`+24V` load rail, `VIN_RAW`/`VIN_F` before and after the fuse, `VIN_LOGIC` buck input (24 V or USB), `+3V3`, `VREFP` (ferrite-filtered ADC reference and thermistor pull-up), `CAN_H`/`CAN_L` after the swap block, `HEAT_N`/`FAN_N` FET drains, `TH_SIG` thermistor, `TH_ADC` filtered ADC input.

## JLCPCB BOM

`bom_jlcpcb.csv` fills in only LCSC numbers that were checked against JLCPCB's basic parts list. Choose LCSC numbers for the rest in JLCPCB's part search when ordering.

`../gerber/` holds the fab set exported from the routed board with `kicad-cli`: 4-layer gerbers with Protel extensions, separate PTH/NPTH Excellon drills, a job file, `toolhead-bom-jlcpcb.csv` and `toolhead-cpl-jlcpcb.csv`. The CPL marks 58 of the 68 placements as `Bottom`. JLCPCB's bottom-side rotations often need a correction in their placement preview, so check every rotated part there before confirming. `production/` is older output from the Fabrication Toolkit plugin, made before routing; regenerate it from KiCad if you use that plugin.
