# hotswap_toolhead (CAN version, branch `can-sh`)

A one-board CAN toolhead for 3D printers. It drives a heater (up to 100 W) and a 24 V fan, and reads a thermistor (100k NTC or PT1000) and a switch. 24 V and the CAN bus come in on one small JST-XH plug. It runs Klipper over CAN on an STM32G0B1.

- **Board:** one 27 × 34 mm, 4-layer board, held by two M2 screws in half-hole notches on its side edges.
- **Plugs, all JST:**
  - 6-pin XH on the top edge: 24 V and GND on two contacts each, CAN-H, CAN-L.
  - 4-pin XH on the bottom edge: the heater, two contacts per side.
  - 6-pin SH (1 mm) on the bottom edge: fan, thermistor, switch.
  - 4-pin SH on the left edge: USB (VBUS, D−, D+, GND), wired to a USB socket for the first flash.
- **Power:** an 8 A fuse and a TVS on the 24 V input, with no reverse-polarity FET (the plug is keyed). A 3.3 V buck runs the logic from 24 V or from USB alone.
- **Other branches:**
  - `usb-sh` is the USB-only board this one is built on: 19.5 × 23.5 mm, no heater.
  - `usb-only` is that board's first version.
  - `stack` is the 24 V CAN version as two stacked 27 × 27 mm boards, with XT30 and Nano-Fit plugs.
  - `narrow-27` and `centre-j2` are the earlier single-board 24 V versions.

## Repository layout

| Folder | Contents |
| --- | --- |
| `docs/` | Design spec (`design_spec.md`), with the Klipper config |
| `hardware/` | KiCad project `toolhead_can`: schematic, routed PCB, design rules, JLCPCB BOM. `panel/`, `panel6/` and `panel4/` are the panels to order |
| `gerber/` | Fab outputs. `can/` is the single board, for checking. `panel/` (9 boards), `panel6/` (6) and `panel4/` (4) are what you order: see `gerber/README.md` |
| `tools/` | See below |

What's in `tools/`:

- `design.py`: the netlist.
- `gen_kicad.py`: builds the schematic, BOM and rules from it.
- `verify.py`: checks every pin's net.
- `fab.sh`: regenerates `gerber/can/`.
- `make_panel.sh`: builds the panels.
- `layout/`: the placement and routing scripts (see `tools/layout/README.md`).

## Status

The schematic is complete and the PCB is routed:

- DRC: 0 errors, 0 unconnected, schematic parity clean.
- All three panels build with 0 DRC errors.

Nothing has been built or tested yet. See the prototype checks at the end of `docs/design_spec.md`, and note that the board has no reverse-polarity protection.

## Regenerating the KiCad files

```
python3 tools/gen_kicad.py   # rebuilds hardware/toolhead_can.kicad_sch, BOM and rules from tools/design.py
python3 tools/verify.py      # re-parses the schematic and checks every pin's net
```

The generator never touches the routed board. After a netlist change, choose one:

- Run **Update PCB from Schematic** in KiCad and fix up the routing.
- Re-run the layout (`tools/layout/run_can.sh`).

Then run `tools/fab.sh` and `tools/make_panel.sh` (9, 6 and 4).
