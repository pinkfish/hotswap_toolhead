# Layout scripts

These scripts placed and routed `hardware/toolhead.kicad_pcb` (31 × 33 mm, 4 layers). They are kept so the layout can be redone after a netlist or placement change. They are not needed to open, check or order the board.

```
tools/layout/run_layout.sh /path/to/workdir
```

`run_layout.sh` copies the project files from `hardware/` into the work directory. It strips the committed board of copper and runs every step below. It leaves `board.kicad_pcb` there and never writes to `hardware/`. Check the result in KiCad and with `tools/verify.py` before copying it over `hardware/toolhead.kicad_pcb`. Then run `tools/fab.sh` to regenerate `gerber/`, and `tools/make_panel.sh` to rebuild the panel.

## Requirements

- **KiCad 10:** its Python (`KICAD_PY`) and `kicad-cli` (`KICAD_CLI`). The defaults are the macOS app paths.
- **Freerouting 1.9.0:** set `FREEROUTING_JAR` to the jar. It isn't in the repo. 2.x crashed or hung on this board.
- **Java 21 or newer:** set `JAVA` if `java` isn't on the path. Freerouting 1.9.0 opens its window while it routes.

Other settings: `BH` sets the board height (default 33). `MAZE_ITER` sets the maze clean-up passes (default 6). `FR_PASSES` and `FR_TIMEOUT` control Freerouting.

## Steps

| Script | What it does |
|---|---|
| `strip.py` | Copies the board without tracks, vias and zones, and resets pad zone connections |
| `place.py` | Places parts from `PLAN` (x, y, rotation, side, fixed), draws the outline and hole keep-outs, and pushes movable parts apart until no courtyards overlap |
| `corner_pre.py` | Hand layout of the U6 pin 4–10 corner: crystal, load caps, VREF, NRST |
| `misc_pre.py` | Q2 source bar; JP3 BOM flags |
| `usb_pre.py` | USB-C data pins joined on F.Cu, one via per pair down to the USBLC6 (U5) |
| `th_pre.py th` / `th_pre.py pwm` | Thermistor lane (TH_ADC) and HEAT_PWM |
| `left_pre.py` | Left-side pre-routes: +3V3 trunk, SENS, SENS_IN, FAN_P, NRST, SWCLK |
| `sig_fanout.py` | Escape vias for the listed U6 pins |
| `buck_pre.py` | Buck power links on B.Cu: VIN_LOGIC from D3 to C4, BUCK_SW from U1 through D9 to L1 |
| `planes_fanout.py` | In1 GND and In2 +24V planes, with a via from every plane pad |
| `netclasses.py` | Power, Fan, Supply and USB net classes in the project |
| `power_pre.py` | +24V pour and via array on Q1, with room reserved for the VIN pours (`--post` fills them after routing) |
| `export_dsn.py`, `frbest.sh` | Specctra export with the boundary pulled 0.3 mm in from the edge, then Freerouting |
| `finish3.py` | Imports the session; adds the HEAT_N pour and the F/B GND pours; stitches and fills |
| `ripup_loop.sh`, `maze.py` | Re-runs DRC and routes whatever is still unconnected on a 0.05 mm grid |
| `finalize.py`, `undangle.py`, `silk.py` | Solid connections for starved thermals; removes dangling vias and stubs; silkscreen tidy-up |
| `check.sh` | DRC summary; the full report goes in `drc.json` beside the board |

## Done by hand on the committed board

These changes came after the scripted run. Redo them, or check they're still needed, on a new run:

- Q2 source pads 1–3 have a solid zone connection. A second GND via sits at (16.3, 27.75), joined by a 0.4 mm F.Cu track from (16.6, 26.72).
- FAN_PWM: `finalize.py` removes U6 pin 47's escape via near (21.94, 22.65) as dangling, which leaves FAN_PWM open (the run ends with 1 unconnected item). On the committed board a short B.Cu link to (22.09, 22.9) replaced the via. On a new run, check the DRC for this item and link it however the router left it.
- CAN H/L labels on F.Silkscreen at (5.55, 7.65) and (5.55, 5.1).

Coordinates are in mm from the board's top-left corner, seen from the top. KiCad places the board at an offset of (100, 100).
