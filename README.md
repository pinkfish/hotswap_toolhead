# hotswap_toolhead (CAN stack, branch `can-stack`)

A CAN toolhead for 3D printers on two stacked boards. It drives a heater (up to 100 W) and a 24 V fan, and reads a thermistor (100k NTC or PT1000) and a switch. 24 V and the CAN bus come in on one small JST-XH plug. It runs Klipper over CAN on an STM32G0B1.

- **Boards:** two 25 × 26 mm, 4-layer boards, stacked 11 mm apart on a 2 × 4 board-to-board link: the logic board (MCU, CAN, USB, fan, sensors, 24 V input) on top and the power board (heater driver, 3.3 V buck) under it. Both have two M2 half-hole notches on their side edges for standoffs.
- **Plugs, all JST:**
  - Logic board, 6-pin XH on the top edge: 24 V and GND on two contacts each, CAN-H, CAN-L.
  - Logic board, 6-pin SH (1 mm) on the bottom edge: fan, thermistor, switch.
  - Logic board, 4-pin SH on the left edge: USB (VBUS, D−, D+, GND), wired to a USB socket for the first flash.
  - Power board, 4-pin XH on the bottom edge: the heater, two contacts per side.
- **Power:** an 8 A fuse and a TVS on the 24 V input, with no reverse-polarity FET (the plug is keyed). A 3.3 V buck runs the logic from 24 V or from USB alone.
- **Other branches:**
  - `can-sh` is the same circuit on one 27 × 34 mm board.
  - `usb-sh` is the USB-only board that one is built on: 19.5 × 23.5 mm, no heater.
  - `usb-only` is that board's first version.
  - `stack` is the 24 V CAN version as two stacked 27 × 27 mm boards, with XT30 and Nano-Fit plugs.
  - `narrow-27` and `centre-j2` are the earlier single-board 24 V versions.

## Repository layout

| Folder | Contents |
| --- | --- |
| `docs/` | Design spec (`design_spec.md`), with the Klipper config |
| `hardware/` | KiCad projects `toolhead_logic` and `toolhead_power`: schematics, routed PCBs, design rules, JLCPCB BOMs. `panel/`, `panel6/` and `panel4/` are the panels to order, each holding both boards |
| `gerber/` | Fab outputs. `logic/` and `power/` are the single boards, for checking. `panel/` (9 pairs), `panel6/` (6) and `panel4/` (4) are what you order: see `gerber/README.md` |
| `tools/` | See below |

What's in `tools/`:

- `design.py`: the netlist.
- `gen_kicad.py`: builds the schematic, BOM and rules from it.
- `verify.py`: checks every pin's net, and that the link's two halves match.
- `check_stack.py`: checks that the routed boards stack (outline, notches, link pins).
- `fab.sh`: regenerates `gerber/logic/` and `gerber/power/`.
- `make_panel.sh`: builds the panels.
- `layout/`: the placement and routing scripts (see `tools/layout/README.md`).

## Status

The schematic is complete and the PCB is routed:

- DRC: 0 errors, 0 unconnected, schematic parity clean, on both boards.
- `check_stack.py`: the boards stack.
- All three panels build with 0 DRC errors.

Nothing has been built or tested yet. See the prototype checks at the end of `docs/design_spec.md`, and note that the board has no reverse-polarity protection.

## Regenerating the KiCad files

```
python3 tools/gen_kicad.py   # rebuilds both schematics, BOMs and rules from tools/design.py
python3 tools/verify.py      # re-parses the schematic and checks every pin's net
```

The generator never touches the routed board. After a netlist change, choose one:

- Run **Update PCB from Schematic** in KiCad and fix up the routing.
- Re-run the layout (`tools/layout/run_stack.sh logic|power`).

Then run `tools/check_stack.py`, `tools/fab.sh` and `tools/make_panel.sh` (9, 6 and 4).
