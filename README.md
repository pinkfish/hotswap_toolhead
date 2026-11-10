# hotswap_toolhead (USB version)

A small USB toolhead board for 3D printers. It reads a thermistor (100k NTC or PT1000) and a switch, and drives a 5 V fan (0.3 A or less). Everything comes over one USB-C cable. It runs Klipper over USB on an STM32G0B1.

The heater is not on this board: it is wired straight to the printer's mainboard on its own cable.

- **Board:** one 22 × 30 mm, 4-layer board, two M2.5 holes.
- **Plugs:** USB-C on the top edge. A 6-pin JST-PH on the bottom edge carries fan, thermistor and switch.
- **Power:** USB VBUS (5 V) feeds a 3.3 V LDO for the logic, and the fan through a PTC.
- **Other branches:** `stack` is the 24 V CAN version: two stacked 27 × 27 mm boards with a 100 W heater output. `narrow-27` and `centre-j2` are the single-board 24 V versions.

## Repository layout

| Folder | Contents |
| --- | --- |
| `docs/` | Design spec (`design_spec.md`), with the Klipper config |
| `hardware/` | KiCad project `toolhead_usb`: schematic, routed PCB, design rules, JLCPCB BOM. `panel/`, `panel6/` and `panel4/` are the panels to order |
| `gerber/` | Fab outputs. `usb/` is the single board, for checking. `panel/` (9 boards), `panel6/` (6) and `panel4/` (4) are what you order: see `gerber/README.md` |
| `tools/` | See below |

What's in `tools/`:

- `design.py`: the netlist.
- `gen_kicad.py`: builds the schematic, BOM and rules from it.
- `verify.py`: checks every pin's net.
- `fab.sh`: regenerates `gerber/usb/`.
- `make_panel.sh`: builds the panels.
- `layout/`: the placement and routing scripts (see `tools/layout/README.md`).

## Status

The schematic is complete and the PCB is routed:

- DRC: 0 errors, 0 unconnected, schematic parity clean.
- All three panels build with 0 DRC errors.

Nothing has been built or tested yet. Before relying on it, read "Heater on the mainboard" in `docs/design_spec.md`: a Klipper heater with its sensor on a different MCU hasn't been tried.

## Regenerating the KiCad files

```
python3 tools/gen_kicad.py   # rebuilds hardware/toolhead_usb.kicad_sch, BOM and rules from tools/design.py
python3 tools/verify.py      # re-parses the schematic and checks every pin's net
```

The generator never touches the routed board. After a netlist change, choose one:

- Run **Update PCB from Schematic** in KiCad and fix up the routing.
- Re-run the layout (`tools/layout/run_usb.sh`).

Then run `tools/fab.sh` and `tools/make_panel.sh` (9, 6 and 4).
