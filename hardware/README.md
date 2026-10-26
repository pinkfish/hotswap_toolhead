# 24 V CAN heater/fan controller – KiCad project

The schematic is generated from `tools/design.py` (the netlist) by `tools/gen_kicad.py`; the PCB is routed. Opens in KiCad 8 or newer (routed and checked in KiCad 10).

## What's here

| File | Contents |
| --- | --- |
| `toolhead.kicad_pro` | Project file – open this in KiCad |
| `toolhead.kicad_sch` | Full schematic: 72 parts, 44 nets, grouped by function. Every pin is tied to its net with a net label, so there are no wires to trace. |
| `toolhead.kicad_pcb` | Routed board: 31 × 42 mm, 4 layers, two M3 insert holes. The generator writes a starter here only if the file is missing |
| `toolhead.kicad_pro` | Project file with the netclasses used for routing: Power 0.8 mm / 0.3 mm, Fan 0.4 / 0.3, Supply and USB 0.3 / 0.2 |
| `toolhead.kicad_dru` | Custom design rules: high-current track widths, 24 V clearance, USB pair |
| `place_footprints.py` | Puts every footprint where it sits on the routed board (only needed when rebuilding a board from scratch) |
| `bom_jlcpcb.csv` | BOM in JLCPCB's upload format, DNP parts excluded |
| `fp-lib-table`, `footprints/` | Project footprint library for the XT30(2+2) connector (J1) |
| `../tools/` | Generator source: edit `tools/design.py`, then run `python3 tools/gen_kicad.py` and `python3 tools/verify.py` |

The schematic was checked by re-parsing the file and rebuilding the netlist from pin and label positions: every pin matches `tools/design.py`, with no dangling pins.

## Layout

- **Stackup:** F.Cu (connectors, buttons, LEDs, C1, JP2; GND pour), In1 solid GND, In2 solid +24V, B.Cu (all other parts; GND pour). Signals route on F.Cu and B.Cu only.
- **Heater current path:** J1 pin 1 → VIN_RAW pour (B.Cu) → F1 → VIN_F pour (B.Cu) → Q1 → +24V pour on Q1's source with a via array → In2 plane → J2 → heater → J2 pin 2 → HEAT_N pours on both outer layers (81 mm², 17 thermal vias) → Q2 → 4 vias → In1 GND plane.
- **MCU corner:** crystal, load caps, VDD/VREF+ decoupling and FB1 sit directly under U6's pins 4–10; +3V3 pins 4 and 6 drop to staggered vias so VREF+ (pin 5) runs straight down to C11/C12.
- **USB-C:** D+ (B6/A6) strapped above the pad row and D− (A7/B7) below it on F.Cu, one via per pair down to U5, whose flow-through pins carry the pair across.
- **Routing:** autorouted (Freerouting) and finished with a scripted router, so it is functional rather than hand-tidy. Review the crystal, USB and CAN paths before ordering.
- **DRC:** 0 errors and 0 unconnected with the custom rules. The remaining warnings are expected: J2/J3 silkscreen over the board edge (the plugs overhang on purpose), H1/H2 courtyards enlarged to the insert keep-out, and two unused escape vias (CAN_TX, SWCLK) that join same-layer track ends.

Most bottom-side reference designators are on B.Fab rather than the silkscreen (there is no room for them); they still appear on assembly drawings.

## Before ordering

- **U1 (TI LMR16006XDDC, 60 V buck):** footprint `Package_TO_SOT_SMD:SOT-23-6`, pins 1 CB, 2 GND, 3 FB, 4 SHDN, 5 VIN, 6 SW. It is non-synchronous, so D9 (DSK110) is its catch diode from SW to GND. L1 = 22 µH (FNR4030S220MT); R2 = 33 kΩ over R3 = 10 kΩ gives 3.29 V (V_FB = 0.765 V).
- **J1 (XT30PW(2+2)-M.G.B, LCSC C19268030):** footprint is in `footprints/hotswap_toolhead.pretty/XT30PW-2+2-M.kicad_mod`. Check its pad numbers against the datasheet before ordering: 1 = power +, 2 = power −, 3 = signal S1, 4 = signal S2, so +24V doesn't end up on the wrong pin.

## Check against datasheets

- **Q1–Q3 PowerPAK footprints:** KiCad's `*_Single` PowerPAK footprints have 5 pads (1–3 source, 4 gate, 5 drain tab), and the symbols match that.

- **U6 STM32G0B1 pinout:** from the G0 LQFP-48 pinout (VREF+ pin 5, VDD/VDDA 6, VSS/VSSA 7, PB0/PB1 19/20, PB13 25, PA11/12 33/34). Confirm against ST DS13560.
- **U3 CAN transceiver (TCAN3414DR):** pin 5 is SHDN (high = shutdown, internal pull-down) and is left open. R12 (DNP) would tie it to +3V3 and switch the transceiver off, so never fit it. A TCAN3413 (pin 5 = VIO) would need R12 fitted.
- **J2 Nano-Fit and inductor L1:** placeholder footprints from the right families; match to the exact part numbers.
- **Crystal Y1:** 20 pF load with 33 pF caps – check oscillator gain margin (ST AN2867) on the first board.

## Net names

`+24V` load rail, `VIN_RAW`/`VIN_F` before and after the fuse, `VIN_LOGIC` buck input (24 V or USB), `+3V3`, `VREFP` (ferrite-filtered ADC reference and thermistor pull-up), `CAN_H`/`CAN_L` after the swap block, `HEAT_N`/`FAN_N` FET drains, `TH_SIG` thermistor, `TH_ADC` filtered ADC input.

## JLCPCB BOM

`bom_jlcpcb.csv` fills in only LCSC numbers that were checked against JLCPCB's basic parts list. Choose LCSC numbers for the rest in JLCPCB's part search when ordering.

`../gerber/` holds the fab set exported from the routed board with `kicad-cli`: 4-layer gerbers with Protel extensions, separate PTH/NPTH Excellon drills, a job file, `toolhead-bom-jlcpcb.csv` and `toolhead-cpl-jlcpcb.csv`. The CPL marks 58 of the 68 placements as `Bottom`. JLCPCB's bottom-side rotations often need a correction in their placement preview, so check every rotated part there before confirming. `production/` is older output from the Fabrication Toolkit plugin, made before routing; regenerate it from KiCad if you use that plugin.
