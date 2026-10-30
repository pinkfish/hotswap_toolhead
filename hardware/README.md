# 24 V CAN heater/fan controller – KiCad project

The schematic is generated from `tools/design.py` (the netlist) by `tools/gen_kicad.py`; the PCB is routed. Opens in KiCad 8 or newer (routed and checked in KiCad 10).

## What's here

| File | Contents |
| --- | --- |
| `toolhead.kicad_pro` | Project file – open this in KiCad |
| `toolhead.kicad_sch` | Full schematic: 65 parts, 41 nets, grouped by function. Every pin is tied to its net with a net label, so there are no wires to trace. |
| `toolhead.kicad_pcb` | Routed board: 31 × 36 mm, 4 layers, two M3 insert holes. The generator writes a starter here only if the file is missing |
| `toolhead.kicad_pro` | Project file with the netclasses used for routing: Power 0.8 mm / 0.3 mm, Fan 0.4 / 0.3, Supply and USB 0.3 / 0.2 |
| `toolhead.kicad_dru` | Custom design rules: high-current track widths, 24 V clearance, USB pair |
| `place_footprints.py` | Puts every footprint where it sits on the routed board (only needed when rebuilding a board from scratch) |
| `bom_jlcpcb.csv` | BOM in JLCPCB's upload format; the solder-jumper pads (JP1, JP3) excluded; every other part is placed |
| `fp-lib-table`, `footprints/` | Project footprint library: the XT30(2+2) connector (J1) and the AON7264E DFN 3×3 (Q2, land pattern from the LCSC/EasyEDA footprint for C431191) |
| `../tools/` | Generator source: edit `tools/design.py`, then run `python3 tools/gen_kicad.py` and `python3 tools/verify.py` |

The schematic was checked by re-parsing the file and rebuilding the netlist from pin and label positions: every pin matches `tools/design.py`, with no dangling pins.

## Layout

- **Stackup:** F.Cu (connectors, SW1, LEDs, C1–C3, C8, C20, D6, F2, JP1–JP3, Q2, Q3, R4–R6, R11, R13–R16, R18, R22, R23; GND pour), In1 solid GND, In2 solid +24V, B.Cu (all other parts; GND pour). Signals route on F.Cu and B.Cu only.
- **Heater current path:** J1 pin 1 → VIN_RAW pour (B.Cu) → F1 → VIN_F pour (B.Cu) → Q1 → +24V pour on Q1's source with a via array → In2 plane → J2 pin 1 → heater → J2 pin 5 → 0.8 mm tracks and a 31 mm² HEAT_N pour on F.Cu → Q2 → source bar, solid to the top GND pour, and 2 vias → In1 GND plane.
- **MCU corner:** crystal, load caps, VDD/VREF+ decoupling and FB1 sit directly under U6's pins 4–10; +3V3 pins 4 and 6 drop to staggered vias so VREF+ (pin 5) runs straight down to C11/C12. NRST, OSC_OUT and OSC_IN are pre-routed in that order under the pin row, and the crystal's GND pads tie across to each other and to C13/C15.
- **USB-C:** D+ (B6/A6) strapped above the pad row and D− (A7/B7) below it on F.Cu, one via per pair down to U5. From those vias both run west on F.Cu, D+ above D−, to a via in front of each of U6's pins 34/33, so they never cross. SWCLK leaves pin 36 east under the package corner to a via and runs on F.Cu round the BOOT pads (JP3) to R4, which sits on top below them; that frees the B.Cu strip under J5 for the A9 VBUS via. CC1/CC2 go up through vias just above their pads to R20/R21 under the shell. U6 sits at y 14.1 so its top pin row is clear of J5's pads.
- **Routing:** USB (to U6), CC1/CC2, SWCLK/BOOT, the A9 VBUS via, the crystal/NRST corner and VREFP's exit, TH_ADC, SENS_IN, CAN_TX/RX and the CAN_H/CAN_L escape from U3, U3's +3V3, FAN_PWM, HEAT_PWM, NRST from SW1, and the buck's VIN_LOGIC/BUCK_SW/FB links are pre-routed by script; the rest is autorouted (Freerouting 1.9.0) and finished with a scripted maze router, so it is functional rather than hand-tidy. Review the crystal, USB and CAN paths before ordering.
- **DRC:** 0 errors, 0 unconnected and schematic parity clean with the custom rules. The 7 remaining warnings: J1, J2 and J5 silkscreen at the board edge (the connectors sit on it on purpose) and H1/H2 courtyards changed from the library footprint to match the insert keep-out.

Most bottom-side reference designators are on B.Fab rather than the silkscreen (there is no room for them); they still appear on assembly drawings.

## Before ordering

- **U1 (TI LMR16006XDDC, 60 V buck):** footprint `Package_TO_SOT_SMD:SOT-23-6`, pins 1 CB, 2 GND, 3 FB, 4 SHDN, 5 VIN, 6 SW. It is non-synchronous, so D9 (DSK110) is its catch diode from SW to GND. L1 = 22 µH (FNR4030S220MT); R2 = 33 kΩ over R3 = 10 kΩ gives 3.29 V (V_FB = 0.765 V).
- **J1 (XT30PW(2+2)-M.G.B, LCSC C19268030):** footprint is in `footprints/hotswap_toolhead.pretty/XT30PW-2+2-M.kicad_mod`. Check its pad numbers against the datasheet before ordering: 1 = power +, 2 = power −, 3 = CAN_H, 4 = CAN_L (marked H/L on the silkscreen), so +24V doesn't end up on the wrong pin.

## Check against datasheets

- **Q1 PowerPAK and Q2 DFN footprints:** KiCad's PowerPAK SO-8 `_Single` footprint (Q1) and the project's AOS DFN 3×3 footprint (Q2) both have 5 pads (1–3 source, 4 gate, 5 drain tab), and the symbols match that. Q3 is a SOT-23 (1 G, 2 S, 3 D).

- **U6 STM32G0B1 pinout:** from the G0 LQFP-48 pinout (VREF+ pin 5, VDD/VDDA 6, VSS/VSSA 7, PA2/PA3 13/14, PA6 17, PB0/PB1 19/20, PA11/12 33/34, PA14 36, PB9 48). Confirm against ST DS13560.
- **U3 CAN transceiver (TCAN3414DRBR, VSON-8):** pin 5 is SHDN (high = shutdown, internal pull-down) and is left open, so the transceiver is always on.
- **Crystal Y1:** 20 pF load with 33 pF caps – check oscillator gain margin (ST AN2867) on the first board.

## Net names

`+24V` load rail, `VIN_RAW`/`VIN_F` before and after the fuse, `VIN_LOGIC` buck input (24 V or USB), `+3V3`, `VREFP` (ferrite-filtered ADC reference and thermistor pull-up), `CAN_H`/`CAN_L` straight from J1 pins 3/4, `HEAT_N`/`FAN_N` FET drains, `TH_SIG` thermistor, `TH_ADC` filtered ADC input.

## JLCPCB BOM

`bom_jlcpcb.csv` fills in only LCSC numbers that were checked against JLCPCB's basic parts list. Choose LCSC numbers for the rest in JLCPCB's part search when ordering.

`../gerber/` holds the fab set exported from the routed board with `kicad-cli`: 4-layer gerbers with Protel extensions, separate PTH/NPTH Excellon drills, a job file, `toolhead-bom-jlcpcb.csv` and `toolhead-cpl-jlcpcb.csv`. The CPL marks 36 of the 63 placements as `Bottom`. JLCPCB's bottom-side rotations often need a correction in their placement preview, so check every rotated part there before confirming. `../gerber/panel/` is the same set for a 3 × 3 panel (111 × 138 mm), built by `tools/make_panel.sh` with KiKit into `panel/toolhead_panel.kicad_pcb`: 5 mm frame rails with four 1.152 mm tooling holes and three fiducials, 2 mm gaps between columns and 6 mm between rows (J1 overhangs the top edge by 2.8 mm and J2 the bottom by 2.3 mm, so the boards can't butt together for V-cuts), and mouse-bite tabs only where both neighbours are clear: J1/J5 fill the top edge and the centred J2 the bottom, so all four are on the sides, a 1.4 mm tab at y 9.8 and a 2.5 mm tab at y 26.3 on each, with the bite holes centred on the board edge. The panel's DRC rules allow H2's ring 0.49 mm to the corner, because KiKit's rebuilt outline sits 0.0006 mm inside the board's. Designators are suffixed per board (`R1_0` ... `R1_8`), 567 placements; upload `toolhead_panel-gerbers.zip`, the panel BOM and the panel CPL together, and order it as a customer panel. `production/` is older Fabrication Toolkit output; it includes DNP parts in its BOM unless Exclude DNP is ticked, which JLCPCB rejects.
