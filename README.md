# hotswap_toolhead

A small 24 V CAN toolhead board for 3D printers: one heater (up to 100 W), one fan (≤0.5 A) and one thermistor input (100k NTC or PT1000), with USB-C for programming and debugging. Runs Klipper with the Katapult bootloader on an STM32G0B1.

- **Boards:** two stacked 27 × 27 mm, 4-layer boards joined by a 2×6 2.54 mm board-to-board connector, 11 mm apart on two M2.5 standoffs. The logic board (on top) carries the power and CAN input, protection, MCU, CAN, USB and sensor inputs; the power board (underneath) the 3.3 V buck, the heater and fan drivers and the load plug. 25% less footprint than the single 27 × 36 mm board (branch `narrow-27`), about 12.6 mm more height
- **Input:** XT30(2+2) – 24 V power plus CAN on one connector
- **Protection:** fuse, bidirectional TVS, reverse-polarity FET, ±58 V-tolerant CAN transceiver, fan PTC
- **Programming:** USB alone powers the logic, no 24 V needed

## Repository layout

| Folder | Contents |
| --- | --- |
| `docs/` | Design spec (`design_spec.md`) and schematic overview |
| `hardware/` | KiCad projects for both boards (`toolhead_logic`, `toolhead_power`): schematics, routed PCBs, design rules, JLCPCB BOMs; `panel/`, `panel6/` and `panel4/` are the panels with both |
| `gerber/` | Fab outputs: `logic/` and `power/` per board (4-layer gerbers, drill files, JLCPCB BOM and CPL), and the panels to order (`tools/make_panel.sh`): `panel/` with 9 of each, `panel6/` with 6, `panel4/` with 4: see `gerber/README.md` |
| `tools/` | Python source for the KiCad files: `design.py` is the netlist of both boards and the link between them, `gen_kicad.py` builds the files, `verify.py` checks connectivity, `check_stack.py` checks that the boards line up; `current/check_heater.sh` checks the heater path's copper at full load; `fab.sh` regenerates `gerber/logic` and `gerber/power`; `layout/` holds the placement and routing scripts (see `tools/layout/README.md`) |

## Status

Schematics complete and both PCBs routed: DRC clean (0 errors, 0 unconnected, schematic parity clean) with the custom rules in `hardware/toolhead_*.kicad_dru`, and `tools/check_stack.py` confirms the outlines, holes and the twelve link pins line up. The panel builds with 0 DRC errors. Not yet built or tested. Before ordering, work through **Before ordering** in `hardware/README.md`: several values and part numbers are still placeholders.

## Regenerating the KiCad files

```
python3 tools/gen_kicad.py   # rebuilds hardware/ from tools/design.py
python3 tools/verify.py      # re-parses both schematics, checks every pin's net and the link
```

Running the generator overwrites both boards' schematics (`hardware/toolhead_logic.kicad_sch`, `toolhead_power.kicad_sch`), BOMs and design rules. It writes each `.kicad_pro` only when it is missing and never touches the routed boards. After a netlist change, regenerate, then either run **Update PCB from Schematic** in KiCad and fix up the routing by hand, or re-run the layout (`tools/layout/run_stack.sh`). Then `python3 tools/check_stack.py` (with KiCad's Python) to confirm the boards still stack.
