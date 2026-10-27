# hotswap_toolhead

A small 24 V CAN toolhead board for 3D printers: one heater (60–72 W), one fan (≤0.5 A) and one thermistor input (100k NTC or PT1000), with USB-C for programming and debugging. Runs Klipper with the Katapult bootloader on an STM32G0B1.

- **Board:** 31 × 35 mm, 4-layer (In1 GND plane, In2 +24V plane), two M3 heat-set-insert holes; connectors, the RESET button, LEDs and the heater FET on top, everything else on the bottom
- **Input:** XT30(2+2) – 24 V power plus CAN on one connector
- **Protection:** fuse, bidirectional TVS, reverse-polarity FET, ±58 V-tolerant CAN transceiver, fan PTC
- **Programming:** USB alone powers the logic, no 24 V needed

## Repository layout

| Folder | Contents |
| --- | --- |
| `docs/` | Design spec (`design_spec.md`) and schematic overview |
| `hardware/` | KiCad project: schematic, routed PCB, design rules, placement script, JLCPCB BOM |
| `gerber/` | Fab outputs from the routed PCB: 4-layer gerbers, drill files, JLCPCB BOM and CPL |
| `tools/` | Python source for the KiCad files: `design.py` is the netlist, `gen_kicad.py` builds the files, `verify.py` checks connectivity |

## Status

Schematic complete and PCB routed: DRC clean (0 errors, 0 unconnected, schematic parity clean) with the custom rules in `hardware/toolhead.kicad_dru`. Not yet built or tested. Before ordering, work through **Before ordering** in `hardware/README.md`: several values and part numbers are still placeholders.

## Regenerating the KiCad files

```
python3 tools/gen_kicad.py   # rebuilds hardware/ from tools/design.py
python3 tools/verify.py      # re-parses the schematic and checks every pin's net
```

Running the generator overwrites `hardware/toolhead.kicad_sch`, the BOM, the design rules and `place_footprints.py`. It writes `hardware/toolhead.kicad_pcb` and `toolhead.kicad_pro` only when they are missing, so it never touches the routed board or its netclasses. After a netlist change, regenerate, then run **Update PCB from Schematic** in KiCad and fix up the routing by hand.
