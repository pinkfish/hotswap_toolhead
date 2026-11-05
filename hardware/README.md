# 24 V CAN heater/fan controller – KiCad project

The schematic is generated from `tools/design.py` (the netlist) by `tools/gen_kicad.py`; the PCB is routed. Opens in KiCad 8 or newer (routed and checked in KiCad 10).

## What's here

| File | Contents |
| --- | --- |
| `toolhead.kicad_pro` | Project file – open this in KiCad |
| `toolhead.kicad_sch` | Full schematic: 68 parts, 42 nets, grouped by function. Every pin is tied to its net with a net label, so there are no wires to trace. |
| `toolhead.kicad_pcb` | Routed board: 27 × 36 mm, 4 layers, two M2.5 insert holes. The generator writes a starter here only if the file is missing |
| `toolhead.kicad_pro` | Project file with the netclasses used for routing: Power 0.8 mm / 0.3 mm, Fan 0.4 / 0.3, Supply and USB 0.3 / 0.2 |
| `toolhead.kicad_dru` | Custom design rules: high-current track widths, 24 V clearance, USB pair |
| `place_footprints.py` | Puts every footprint where it sits on the routed board (only needed when rebuilding a board from scratch) |
| `bom_jlcpcb.csv` | BOM in JLCPCB's upload format; the solder-jumper pads (JP1, JP3) excluded; every other part is placed |
| `fp-lib-table`, `footprints/` | Project footprint library: the XT30(2+2) connector (J1) and the AON7264E DFN 3×3 (Q2, land pattern from the LCSC/EasyEDA footprint for C431191) |
| `../tools/` | Generator source: edit `tools/design.py`, then run `python3 tools/gen_kicad.py` and `python3 tools/verify.py` |

The schematic was checked by re-parsing the file and rebuilding the netlist from pin and label positions: every pin matches `tools/design.py`, with no dangling pins.

## Layout

- **Stackup:** F.Cu (connectors, SW1, LEDs, C1–C3, C8, C20, C21, D6, D10, F2, JP1–JP3, Q2, Q3, R4–R6, R11, R14–R16, R18, R22, R23, U7; GND pour), In1 solid GND, In2 solid +24V, B.Cu (all other parts; GND pour). Signals route on F.Cu and B.Cu only.
- **Heater current path:** J1 pin 1 → VIN_RAW pour (B.Cu) → F1 → VIN_F pour (B.Cu) → Q1 → +24V pour on Q1's source with a via array → In2 plane → J2 pin 1 → heater → J2 pin 5 → 0.8 mm tracks and a 28 mm² HEAT_N pour on F.Cu → Q2 → source bar, solid to the top GND pour, and 2 vias → In1 GND plane.
- **MCU corner:** crystal, load caps, VDD/VREF+ decoupling and FB1 sit directly under U6's pins 4–10, moved over from the 31 mm board with their copper; the crystal's GND pads tie across to each other and to C13/C15. +3V3 pins 4 and 6 drop to vias up to C8's pad 1 on top. VREF+ (pin 5) runs down to C11/C12, but on the narrower board that corner is closed in on the bottom (C9, the crystal, U6's pins), so VREFP leaves past FB1 to a via and runs back west on top in the strip between C8 and F2, then down the left of F2 to R17/R18. NRST, which used that strip, runs above C8 instead, between it and U6's thermal vias, to SW1. FB1's +3V3 side reaches the buck's L1 on top round the left of R14, and C8's GND pad has its own via.
- **USB-C:** D+ (B6/A6) strapped above the pad row and D− (A7/B7) below it on F.Cu, one via per pair down to U5. From those vias both run west on F.Cu, D+ above D−, to a via in front of each of U6's pins 34/33, so they never cross. SWCLK leaves pin 36 east under the package corner to a via and runs on F.Cu round the BOOT pads (JP3) to R4, which sits on top below them; that frees the B.Cu strip under J5 for the A9 VBUS via. CC1/CC2 go up through vias just above their pads to R20/R21 under the shell. U6 sits at y 14.5 so its top pin row is clear of J5's pads. On the 27 mm board only D+ keeps that path to U6 (13 mm); D− was re-routed by the autorouter the long way round (37 mm, 2 vias). At USB full speed (12 Mb/s, 83 ns bits) the 24 mm difference is about 0.15 ns, but it's the first thing to tidy by hand.
- **Routing:** the 27 mm board keeps the 31 mm board's routing inside each block it moved across (power input, USB-C, MCU with crystal and CAN, buck, J2, F2). Between them, `tools/layout/narrow_pre.py` pre-routes FAN_P round J2 to D5, D7's +24V via, LED_STAT and the LED anodes, R5's +3V3, F2's +24V via, HEAT_PWM to U7 and R14, NRST, VREFP, U6's and FB1's +3V3, FAN_PWM round the CAN pair to R15 and CAN_L to U3. The rest is autorouted (Freerouting 1.9.0) and finished with a scripted maze router, so it is functional rather than hand-tidy. Review the crystal, USB and CAN paths before ordering.
- **DRC:** 0 errors, 0 unconnected and schematic parity clean with the custom rules. The 13 remaining warnings: U7, D10 and C21 differ from their library footprints because their silkscreen was removed (it overlapped neighbouring pads); H1/H2 (courtyard cut to the insert pad) and F2 (courtyard trimmed to its pads plus 0.05 mm, so it clears J2's) likewise; J1, J2 and J5 silkscreen at the board edge (the connectors sit on it on purpose), and J1's and J5's outlines touching where they meet on the top edge.

Most bottom-side reference designators are on B.Fab rather than the silkscreen (there is no room for them); they still appear on assembly drawings.

## Before ordering

- **U1 (TI LMR16006XDDC, 60 V buck):** footprint `Package_TO_SOT_SMD:SOT-23-6`, pins 1 CB, 2 GND, 3 FB, 4 SHDN, 5 VIN, 6 SW. It is non-synchronous, so D9 (DSK110) is its catch diode from SW to GND. L1 = 22 µH (FNR4030S220MT); R2 = 33 kΩ over R3 = 10 kΩ gives 3.29 V (V_FB = 0.765 V).
- **J1 (XT30PW(2+2)-M.G.B, LCSC C19268030):** footprint is in `footprints/hotswap_toolhead.pretty/XT30PW-2+2-M.kicad_mod`. Check its pad numbers against the datasheet before ordering: 1 = power +, 2 = power −, 3 = CAN_H, 4 = CAN_L (marked H/L on the silkscreen), so +24V doesn't end up on the wrong pin.

## Check against datasheets

- **U7 gate driver (TI UCC27517DBVR, SOT-23-5):** pins 1 VDD, 2 GND, 3 IN+, 4 IN−, 5 OUT, as TI's datasheet and JLCPCB's symbol for C99395 give them. IN− is tied to GND (non-inverting), OUT drives Q2's gate directly, and VDD is the 12 V zener rail (R13 from VIN_LOGIC, D10, C21).
- **Q1 PowerPAK and Q2 DFN footprints:** KiCad's PowerPAK SO-8 `_Single` footprint (Q1) and the project's AOS DFN 3×3 footprint (Q2) both have 5 pads (1–3 source, 4 gate, 5 drain tab), and the symbols match that. Q3 is a SOT-23 (1 G, 2 S, 3 D).

- **U6 STM32G0B1 pinout:** from the G0 LQFP-48 pinout (VREF+ pin 5, VDD/VDDA 6, VSS/VSSA 7, PA2/PA3 13/14, PA6 17, PB0/PB1 19/20, PA11/12 33/34, PA14 36, PB9 48). Confirm against ST DS13560.
- **U3 CAN transceiver (TCAN3414DRBR, VSON-8):** pin 5 is SHDN (high = shutdown, internal pull-down) and is left open, so the transceiver is always on.
- **Crystal Y1:** 20 pF load with 33 pF caps – check oscillator gain margin (ST AN2867) on the first board.

## Net names

`+24V` load rail, `VIN_RAW`/`VIN_F` before and after the fuse, `VIN_LOGIC` buck input (24 V or USB), `+3V3`, `VREFP` (ferrite-filtered ADC reference and thermistor pull-up), `CAN_H`/`CAN_L` straight from J1 pins 3/4, `HEAT_N`/`FAN_N` FET drains, `TH_SIG` thermistor, `TH_ADC` filtered ADC input.

## JLCPCB BOM

`bom_jlcpcb.csv` fills in only LCSC numbers that were checked against JLCPCB's basic parts list. Choose LCSC numbers for the rest in JLCPCB's part search when ordering.

`../gerber/` holds the fab set exported from the routed board with `kicad-cli`: 4-layer gerbers with Protel extensions, separate PTH/NPTH Excellon drills, a job file, `toolhead-bom-jlcpcb.csv` and `toolhead-cpl-jlcpcb.csv`. The CPL marks 37 of the 66 placements as `Bottom`. It is written by `tools/jlc_cpl.py`, which fits each part's own JLCPCB footprint (cached in `tools/jlc_footprints.json` by `tools/jlc_fetch.py`) onto its pads, so every position and rotation is JLCPCB's: no package rotation table, and bottom rotations as seen from below as JLCPCB expects. Parts with no cached footprint fall back to the KiCad anchor and are listed when the script runs; check those in the placement preview. `../gerber/panel/` is the same set for a 3 × 3 panel (99 × 138 mm), built by `tools/make_panel.sh` with KiKit into `panel/toolhead_panel.kicad_pcb`: 5 mm frame rails with four 1.152 mm tooling holes and three fiducials, 2 mm gaps between columns and 6 mm between rows (J1 overhangs the top edge by 2.8 mm and J2 the bottom by 2.3 mm, so the boards can't butt together for V-cuts), and mouse-bite tabs only where both neighbours are clear: J1/J5 fill the top edge and the centred J2 the bottom, so all four are on the sides, a 1.4 mm tab at y 9.8 and a 1.8 mm tab at y 17.7 on each, with the bite holes centred on the board edge. The panel's DRC rules allow H1's and H2's rings 0.49 mm to the corners, because KiKit's rebuilt outline sits a hair inside the board's. Designators are suffixed per board (`R1_0` ... `R1_8`), 594 placements; upload `toolhead_panel-gerbers.zip`, the panel BOM and the panel CPL together, and order it as a customer panel. Which files to upload, and which not to, is in `../gerber/README.md`. Don't order from the KiCad Fabrication Toolkit plugin's output (`production/`, ignored by git): its CPL takes rotations from a generic package table and the pad-bounding-box centre, which puts J2, J5, SW1, U6, U5, U1, D4, D6 and Q2 in the wrong place or orientation for these parts.
