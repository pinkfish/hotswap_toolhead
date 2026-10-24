# hotswap_toolhead

A small 24 V CAN toolhead board for 3D printers: one heater (60–72 W), one fan (≤0.5 A) and one thermistor input (100k NTC or PT1000), with a 4-pin USB header for programming and debugging. Runs Klipper with the Katapult bootloader on an STM32G0B1.

- **Board:** 42 × 24 mm, 2-layer, two M3 holes 35 mm apart
- **Input:** XT30(2+2) – 24 V power plus CAN on one connector
- **Protection:** fuse, bidirectional TVS, reverse-polarity FET, ±65 V-tolerant CAN transceiver, fan PTC
- **Programming:** USB alone powers the logic, no 24 V needed

## Repository layout

| Folder | Contents |
| --- | --- |
| `docs/` | Design spec (`design_spec.md`) and schematic overview |
| `hardware/` | KiCad 8 project: schematic, PCB starter, design rules, placement script, JLCPCB BOM |
| `tools/` | Python source for the KiCad files: `design.py` is the netlist, `gen_kicad.py` builds the files, `verify.py` checks connectivity |

## Status

Schematic complete; PCB has the outline, mounting holes and a placement script, and needs routing. Before layout, see the **Must-do** list in `hardware/README.md` (dropping the SnapEDA or LCSC XT30(2+2) footprint into `hardware/footprints/`).

## Regenerating the KiCad files

```
python3 tools/gen_kicad.py   # rebuilds hardware/ from tools/design.py
python3 tools/verify.py      # re-parses the schematic and checks every pin's net
```

Running the generator overwrites `hardware/toolhead.kicad_sch` and `hardware/toolhead.kicad_pcb`. Once you start editing in KiCad, treat KiCad as the source and stop regenerating.
