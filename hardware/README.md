# 24 V CAN heater/fan controller – KiCad 8 project

Generated from `tools/design.py` (the netlist) by `tools/gen_kicad.py`. Opens in KiCad 8 or newer.

## What's here

| File | Contents |
| --- | --- |
| `toolhead.kicad_pro` | Project file – open this in KiCad |
| `toolhead.kicad_sch` | Full schematic: 69 parts, 41 nets, grouped by function. Every pin is tied to its net with a net label, so there are no wires to trace. |
| `toolhead.kicad_pcb` | Board starter: 42 × 24 mm outline, two isolated M3 holes 35 mm apart, layout notes |
| `toolhead.kicad_dru` | Custom design rules: high-current track widths, 24 V clearance, USB pair |
| `place_footprints.py` | Puts every footprint on the floorplan from the spec after you import them |
| `bom_jlcpcb.csv` | BOM in JLCPCB's upload format, DNP parts excluded |
| `fp-lib-table`, `footprints/` | Project footprint library for the XT30(2+2) connector (J1) |
| `../tools/` | Generator source: edit `tools/design.py`, then run `python3 tools/gen_kicad.py` and `python3 tools/verify.py` |

The schematic was checked by re-parsing the file and rebuilding the netlist from pin and label positions: every pin matches `tools/design.py`, with no dangling pins.

## Getting to a routed board

1. Open `toolhead.kicad_pro`. Run ERC in the schematic.
2. Add the J1 footprint (see **Must-do** below).
3. In the PCB editor: **Tools → Update PCB from Schematic (F8)**. Footprints load from KiCad's standard libraries.
4. **Tools → Scripting Console**, then run:
   `exec(open('/full/path/to/place_footprints.py').read())`
   Main parts land on the spec's floorplan; passives are staged in rows to the right of the board, grouped by function, for you to drag into place.
5. Copy `toolhead.kicad_dru` next to the project (it is already) – KiCad picks it up as custom rules.
6. Route, then add pours: GND on B.Cu, heater path ≥ 3 mm wide on 1 oz, Q2 drain ≥ 150 mm² both sides with 9+ thermal vias.

This is a placement starting point, not a routed layout. Routing a 3 A heater path next to a 0.5 mm-pitch MCU on a 42 × 24 mm board needs hands-on judgement.

## Must-do before layout

- **U1 (TI LMR16006XDDC, 60 V buck):** footprint `Package_TO_SOT_SMD:SOT-23-6`, pins 1 CB, 2 GND, 3 FB, 4 SHDN, 5 VIN, 6 SW. It is non-synchronous, so D9 (SS210) is its catch diode from SW to GND. Confirm the pinout against TI's datasheet, set L1 from its inductor table (about 22 µH at 0.7 MHz), and set R2 from its feedback formula for 3.3 V with R3 = 10 kΩ.
- **J1 (XT30PW(2+2)-M.G.B, LCSC C19268030):** the schematic points at `hotswap_toolhead:XT30PW-2+2-M`, a project library already registered in `fp-lib-table`. Download the footprint from SnapEDA (or import it from LCSC), save it as `footprints/hotswap_toolhead.pretty/XT30PW-2+2-M.kicad_mod`, and check its pad numbers: 1 = power +, 2 = power −, 3 = signal S1, 4 = signal S2. Step-by-step instructions are in that folder's README.

## Check against datasheets

- **Q1–Q3 PowerPAK footprints:** KiCad's `*_Single` PowerPAK footprints have 5 pads (1–3 source, 4 gate, 5 drain tab), and the symbols match that.

- **U6 STM32G0B1 pinout:** from the G0 LQFP-48 pinout (VREF+ pin 5, VDD/VDDA 6, VSS/VSSA 7, PB0/PB1 19/20, PB13 25, PA11/12 33/34). Confirm against ST DS13560.
- **U3 CAN transceiver pin 5:** varies by part. R12 (DNP) can tie it to +3V3 if it is a VIO pin; otherwise leave it open.
- **SW1/SW2:** footprint is a top-push TL3342 placeholder. Swap for the side-push switch you choose.
- **J2 Nano-Fit and inductor L1:** placeholder footprints from the right families; match to the exact part numbers.
- **Crystal Y1:** 20 pF load with 33 pF caps – check oscillator gain margin (ST AN2867) on the first board.

## Net names

`+24V` load rail, `VIN_RAW`/`VIN_F` before and after the fuse, `VIN_LOGIC` buck input (24 V or USB), `+3V3`, `VREFP` (ferrite-filtered ADC reference and thermistor pull-up), `CAN_H`/`CAN_L` after the swap block, `HEAT_N`/`FAN_N` FET drains, `TH_SIG` thermistor, `TH_ADC` filtered ADC input.

## JLCPCB BOM

`bom_jlcpcb.csv` fills in only LCSC numbers that were checked against JLCPCB's basic parts list. Choose LCSC numbers for the rest in JLCPCB's part search when ordering. A pick-and-place (CPL) file comes from KiCad (**File → Fabrication Outputs → Component Placement**) once the layout is done.
