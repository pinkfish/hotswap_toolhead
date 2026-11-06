# 24 V CAN heater/fan controller – KiCad project

The schematic is generated from `tools/design.py` (the netlist) by `tools/gen_kicad.py`; the PCB is routed. Opens in KiCad 8 or newer (routed and checked in KiCad 10).

## What's here

The design is two stacked boards (see "Two-board stack" in `../docs/design_spec.md`): the logic board on top, the power board underneath, joined by a 2×6 2.54 mm link (J3 / J4).

| File | Contents |
| --- | --- |
| `toolhead_logic.kicad_pro`, `toolhead_power.kicad_pro` | Project files – open these in KiCad; they hold the netclasses used for routing: Power 0.8 mm / 0.3 mm, Fan 0.4 / 0.3, Supply and USB 0.3 / 0.2 |
| `toolhead_logic.kicad_sch` | Logic board schematic: 45 parts, 33 nets (power and CAN input, protection, MCU, CAN, USB, thermistor and switch filters, link socket J3) |
| `toolhead_power.kicad_sch` | Power board schematic: 25 parts, 18 nets (3.3 V buck, heater and fan drivers, J2, link header J4) |
| `toolhead_logic.kicad_pcb`, `toolhead_power.kicad_pcb` | Routed boards: 27 × 27 mm each, 4 layers, the two M2.5 insert holes in the same place on both |
| `toolhead_logic.kicad_dru`, `toolhead_power.kicad_dru` | Custom design rules (the same for both): high-current track widths, 24 V clearance, USB pair, and the one courtyard overlap allowed (C15 beside D1) |
| `toolhead_logic-bom-jlcpcb.csv`, `toolhead_power-bom-jlcpcb.csv`, `bom_jlcpcb.csv` | BOMs in JLCPCB's upload format, per board and both together; the solder-jumper pads (JP1, JP3) excluded; every other part is placed |
| `panel/` | The panel ordered from JLCPCB: 9 of each board, built by `../tools/make_panel.sh` |
| `fp-lib-table`, `footprints/` | Project footprint library: the XT30(2+2) connector (J1) and the AON7264E DFN 3×3 (Q2, land pattern from the LCSC/EasyEDA footprint for C431191) |
| `../tools/` | Generator source: edit `tools/design.py`, then run `python3 tools/gen_kicad.py` and `python3 tools/verify.py` |

Both schematics were checked by re-parsing the files and rebuilding the netlists from pin and label positions: every pin matches `tools/design.py`, with no dangling pins, and the twelve link pins carry the same nets on both boards (except pin 12: GND on the logic board, the thermistor return TH_RTN on the power board).

## Layout

- **Logic board stackup:** F.Cu (J1, J5, SW1, LEDs, C1, JP1–JP3, D3, D4, D6, R4–R6, R11, R17–R23, C19, C20; the +24V pour along the top edge; GND pour), In1 solid GND, In2 signals and GND pour, B.Cu (Q1, F1, D1, D2, R1, U6 with Y1, FB1 and C9–C15, U3, C16, U5, C17, J3; GND pour). +3.3 V is routed.
- **Power board stackup:** F.Cu (J2, J4, Q2, U7, D10, C21, R13, R14, Q3, R15, R16, F2, C2, C3; HEAT_N pour; GND pour), In1 solid GND, In2 solid +24V, B.Cu (U1, L1, D9, C4–C6, C8, R2, R3, D5, D7; GND pour). Signals route on F.Cu and B.Cu only.
- **Heater current path:** J1 pin 1 → VIN_RAW pour (logic B.Cu) → F1 → VIN_F pour → Q1 → +24V pour on Q1's source with a via array → top-layer +24V pour along the logic board's top edge → J3 pins 1/2 → J4 → power board In2 +24V plane → J2 pin 1 → heater → J2 pin 5 → HEAT_N pour on F.Cu → Q2 → source, solid to the top GND pour, and 2 vias → In1 GND → J4/J3 GND pins → logic board GND.
- **Logic board MCU:** U6 sits on the bottom between J1's power pins and J5, turned so its oscillator, NRST and VDD/VREF+ pins face the single board's hand-laid crystal and decoupling corner (`tools/layout/corner_import.py`), CAN faces U3 under J1's CAN pins, USB and SWCLK face U5 and J5, and the thermistor, switch and fan pins (PB12, PB13, PA8) face J3. USB is pre-routed round J5's pad row, which sits right over U6 (`usb_stack_pre.py`), and CAN TX/RX cross under the corner on In2 (`can_stack_pre.py`); the rest is autorouted (Freerouting 1.9.0) and finished with a scripted maze router, so it is functional rather than hand-tidy.
- **DRC:** both boards 0 errors, 0 unconnected and schematic parity clean with the custom rules. The warnings are cosmetic: J1, J5 and J2 silkscreen at the board edge (the connectors sit on it on purpose); silkscreen over copper (U6's and D1's outlines on the logic board, U7's reference on the power board); and footprints that differ from the library because their courtyards or silkscreen were trimmed (H1/H2 to the insert pad; J3 to its pads and body plus 0.25 mm so the panel's mouse bites clear it; U7, D10, C21 and F2 on the power board as on the single board).

Most bottom-side reference designators are on B.Fab rather than the silkscreen (there is no room for them); they still appear on assembly drawings.

## Before ordering

- **U1 (TI LMR16006XDDC, 60 V buck):** footprint `Package_TO_SOT_SMD:SOT-23-6`, pins 1 CB, 2 GND, 3 FB, 4 SHDN, 5 VIN, 6 SW. It is non-synchronous, so D9 (DSK110) is its catch diode from SW to GND. L1 = 22 µH (FNR4030S220MT); R2 = 33 kΩ over R3 = 10 kΩ gives 3.29 V (V_FB = 0.765 V).
- **J1 (XT30PW(2+2)-M.G.B, LCSC C19268030):** footprint is in `footprints/hotswap_toolhead.pretty/XT30PW-2+2-M.kicad_mod`. Check its pad numbers against the datasheet before ordering: 1 = power +, 2 = power −, 3 = CAN_H, 4 = CAN_L (marked H/L on the silkscreen), so +24V doesn't end up on the wrong pin.

## Check against datasheets

- **U7 gate driver (TI UCC27517DBVR, SOT-23-5):** pins 1 VDD, 2 GND, 3 IN+, 4 IN−, 5 OUT, as TI's datasheet and JLCPCB's symbol for C99395 give them. IN− is tied to GND (non-inverting), OUT drives Q2's gate directly, and VDD is the 12 V zener rail (R13 from VIN_LOGIC, D10, C21).
- **Q1 PowerPAK and Q2 DFN footprints:** KiCad's PowerPAK SO-8 `_Single` footprint (Q1) and the project's AOS DFN 3×3 footprint (Q2) both have 5 pads (1–3 source, 4 gate, 5 drain tab), and the symbols match that. Q3 is a SOT-23 (1 G, 2 S, 3 D).

- **U6 STM32G0B1 pinout:** from the G0 LQFP-48 pinout (VREF+ pin 5, VDD/VDDA 6, VSS/VSSA 7, PB0/PB1 19/20, PB12/PB13 24/25, PA8 28, PA11/12 33/34, PA14 36, PB9 48). Confirm against ST DS13560.
- **U3 CAN transceiver (TCAN3414DRBR, VSON-8):** pin 5 is SHDN (high = shutdown, internal pull-down) and is left open, so the transceiver is always on.
- **Crystal Y1:** 20 pF load with 33 pF caps – check oscillator gain margin (ST AN2867) on the first board.

## Net names

`+24V` load rail, `VIN_RAW`/`VIN_F` before and after the fuse, `VIN_LOGIC` buck input (24 V or USB), `+3V3`, `VREFP` (ferrite-filtered ADC reference and thermistor pull-up), `CAN_H`/`CAN_L` straight from J1 pins 3/4, `HEAT_N`/`FAN_N` FET drains, `TH_SIG` thermistor, `TH_ADC` filtered ADC input.

## JLCPCB BOM

`bom_jlcpcb.csv` fills in only LCSC numbers that were checked against JLCPCB's basic parts list. Choose LCSC numbers for the rest in JLCPCB's part search when ordering.

`../gerber/logic/` and `../gerber/power/` hold each board's fab set, exported with `kicad-cli` by `../tools/fab.sh`: 4-layer gerbers with Protel extensions, separate PTH/NPTH Excellon drills, a job file, the BOM and the CPL. The CPL is written by `tools/jlc_cpl.py`, which fits each part's own JLCPCB footprint (cached in `tools/jlc_footprints.json` by `tools/jlc_fetch.py`) onto its pads, so every position and rotation is JLCPCB's: no package rotation table, and bottom rotations as seen from below as JLCPCB expects. Q1 has no JLCPCB footprint to fit and keeps the KiCad anchor; check it in the placement preview. `../gerber/panel/` is the set to order: both boards in one 99.3 × 198.6 mm panel, built by `tools/make_panel.sh` with KiKit into `panel/toolhead_panel.kicad_pcb` (layout plugin `tools/panel_stack.py`): 3 columns of 3 logic/power pairs, 2 mm between columns and from each logic board to its power board, 6 mm from a power board to the next logic board (J2 and J1 overhang into that gap), 5 mm frame rails with four 1.152 mm tooling holes and three fiducials, and mouse-bite tabs on the side edges only, two per side, placed by `tools/panel_tabs.py` where both neighbours are clear. Designators get the board number (`R1_0`, `R1_2` … on logic boards, `C2_1`, `C2_3` … on power boards), 612 placements; upload `toolhead_panel-gerbers.zip`, the panel BOM and the panel CPL together, and order it as a customer panel. Which files to upload, and which not to, is in `../gerber/README.md`. Don't order from the KiCad Fabrication Toolkit plugin's output (`production/`, ignored by git): its CPL takes rotations from a generic package table and the pad-bounding-box centre, which puts several parts in the wrong place or orientation for JLCPCB.
