# USB toolhead board – KiCad project

`tools/gen_kicad.py` generates the schematic from `tools/design.py`, the netlist. The PCB is routed. The project opens in KiCad 8 or newer; it was routed and checked in KiCad 10.

## What's here

| File | Contents |
| --- | --- |
| `toolhead_usb.kicad_pro` | The project file: open this in KiCad. Netclasses: Fan 0.4 / 0.3 mm, Supply and USB 0.3 / 0.2 mm |
| `toolhead_usb.kicad_sch` | Schematic: 40 parts. Blocks: logic supply, MCU, USB, the plug, fan, thermistor, switch |
| `toolhead_usb.kicad_pcb` | The routed board: 22 × 30 mm, 4 layers, two M2.5 holes |
| `toolhead_usb.kicad_dru` | Custom design rules: USB pair, and the fan current's minimum track width |
| `toolhead_usb-bom-jlcpcb.csv`, `bom_jlcpcb.csv` | The BOM in JLCPCB's upload format (the two are the same). The BOOT pads (JP3) are left out; every other part is placed |
| `panel/`, `panel6/`, `panel4/` | The panels to order: 9, 6 or 4 boards, built by `../tools/make_panel.sh` |
| `fp-lib-table`, `footprints/` | Project footprint library, left over from the 24 V boards; the USB board uses only KiCad's standard libraries |

`tools/verify.py` re-parses the schematic and rebuilds the netlist from pin and label positions. Every pin matches `tools/design.py`, and no pin is left dangling.

## Layout

| Layer | What's on it |
| --- | --- |
| F.Cu | J5 (USB-C), J2 (JST-PH), SW1, LED1/LED2 with R5/R6, JP3 with R4, JP2, R17–R19 and C19; GND pour |
| In1 | Solid GND |
| In2 | Signals and +3V3 |
| B.Cu | U6 with Y1, FB1 and C9, C11–C15; U5 and C17 under J5; R20/R21; the fan driver (Q3, D5, R15, R16) and F2; U1 with C4, C8 and C10; D6; R22, R23 and C20; GND pour |

- **Holes:** H1 and H2 have 5.4 mm isolated pads (no net) for M2.5 heat-set inserts.
- **Reference designators:** most bottom-side ones are on B.Fab rather than the silkscreen, because there is no room for them. They still appear on assembly drawings.

## Check against datasheets

- **U1 (ME6211C33M5G-N):** pins 1 VIN, 2 GND, 3 CE, 4 NC, 5 VOUT. CE is tied to VIN.
- **J2 (JST S6B-PH-SM4-TB):** pin 1 is at the left, seen from the top with the plug opening at the bottom edge. Check against the cable's housing before crimping:
  - 1 FAN+
  - 2 FAN−
  - 3 TH_SIG
  - 4 thermistor GND
  - 5 SENS
  - 6 GND
- **U6 STM32G0B1 pinout:** VREF+ 5, VDD/VDDA 6, VSS/VSSA 7, PB12/PB13 24/25, PA8 28, PA11/12 33/34, PA14 36, PB5 44. Confirm against ST DS13560.
- **Crystal Y1:** 20 pF load with 33 pF caps. Check the oscillator's gain margin (ST AN2867) on the first board.

## Net names

| Net | What it is |
| --- | --- |
| `VBUS` | USB 5 V |
| `+3V3` | The LDO's output |
| `VREFP` | The ferrite-filtered ADC reference and thermistor pull-up |
| `FAN_P` | The fan + after F2 |
| `FAN_N` | Q3's drain |
| `TH_SIG` | The thermistor |
| `TH_ADC` | The filtered ADC input |
| `SENS` / `SENS_IN` | The switch, before and after its filter |

## Fab outputs

`../tools/fab.sh` exports `../gerber/usb/` with `kicad-cli`: 4-layer gerbers, drill files, the BOM and the CPL. `tools/jlc_cpl.py` writes the CPL by fitting each part's own JLCPCB footprint onto its pads. The panels are in `../gerber/panel*/`. `../gerber/README.md` says which files to upload.
