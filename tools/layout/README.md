# Layout scripts

These scripts placed and routed `hardware/toolhead.kicad_pcb` (31 × 36 mm, 4 layers). They are kept so the layout can be redone after a netlist or placement change. They are not needed to open, check or order the board.

```
tools/layout/run_layout.sh /path/to/workdir
```

`run_layout.sh` copies the project files from `hardware/` into the work directory. It strips the committed board of copper and runs every step below. It leaves `board.kicad_pcb` there and never writes to `hardware/`. Check the result in KiCad and with `tools/verify.py` before copying it over `hardware/toolhead.kicad_pcb`.

The layout isn't finished at that point. The board is always fabricated as a 3 × 3 panel (see "Panel" in `docs/design_spec.md`), so every layout change must be followed by:

1. `tools/fab.sh`, which regenerates the single-board `gerber/`.
2. `tools/make_panel.sh`, which rebuilds `hardware/panel/` and `gerber/panel/`. It must report 9 boards and 567 placements, with panel DRC at 0 errors and 0 unconnected.
3. Committing the board, `gerber/`, `hardware/panel/` and `gerber/panel/` together.

Keep the tab windows clear of parts at the side edges (y 9.0–10.6 and 23.2–29.5, left and right; there are no top/bottom tabs), or move the tabs in `tools/panel_tabs.py`.

## Requirements

- **KiCad 10:** its Python (`KICAD_PY`) and `kicad-cli` (`KICAD_CLI`). The defaults are the macOS app paths.
- **Freerouting 1.9.0:** set `FREEROUTING_JAR` to the jar. It isn't in the repo. 2.x crashed or hung on this board.
- **Java 21 or newer:** set `JAVA` if `java` isn't on the path. Freerouting 1.9.0 opens its window while it routes.

Other settings: `BH` sets the board height (default 36), `C1Y`, `U6X` and `U6Y` move C1 and the MCU. `MAZE_ITER` sets the maze clean-up passes (default 6). `FR_PASSES` and `FR_TIMEOUT` control Freerouting. `PRE_ONLY=1` stops after the Specctra export, leaving `pre_route.kicad_pcb` and `toolhead.dsn`.

Freerouting's result depends on the pass count, so the committed board came from routing the same pre-route board several times: `PRE_ONLY=1 run_layout.sh dir`, then Freerouting, `finish3.py`, `power_pre.py --post` and `ripup_loop.sh` on copies with `FR_PASSES` 25 to 55, keeping a copy that ends with 0 unconnected and the shortest track. A single `run_layout.sh` run can end with one or two connections open; when the same one stays open across pass counts, it needs a pre-route rather than more maze passes.

## Steps

| Script | What it does |
|---|---|
| `strip.py` | Copies the board without tracks, vias and zones, and resets pad zone connections |
| `place.py` | Places parts from `PLAN` (x, y, rotation, side, fixed), draws the outline and hole keep-outs, and pushes movable parts apart until no courtyards overlap |
| `sync_nets.py` | Re-assigns pad nets from the schematic netlist, so a pin change in `design.py` reaches the stripped board |
| `corner_pre.py` | Hand layout of the U6 pin 4–10 corner: crystal, load caps, VREF, NRST; VREFP's exit round FB1 and FB1's +3V3 via |
| `misc_pre.py` | Q2 source bar, solid to the GND pours; JP3 BOM flags |
| `usb_pre.py` | USB-C data pins joined on F.Cu, one via per pair down to the USBLC6 (U5), then D+/D− on F.Cu to vias in front of U6 pins 34/33; SWCLK round JP3 to R4; the A9 VBUS via; CC1/CC2 vias above their pads; the F.Cu keep-out under the receptacle body |
| `left_pre.py` | Lanes from U6's left side on B.Cu: TH_ADC to R19/C19/D6, SENS_IN to C20, CAN_TX/RX to U3; the CAN_H/CAN_L escape from U3 and U3's GND ties and +3V3 feed; FAN_PWM across on F.Cu to R15/R16 |
| `sig_fanout.py` | Escape vias for the listed U6 pins |
| `heat_pre.py` | HEAT_PWM from its escape via under SW1 and down the right edge to R13/R14; R14's GND tied to Q2's source and Q2 pin 1's via; NRST from SW1 round that run to C15 |
| `buck_pre.py` | Buck links on B.Cu: VIN_LOGIC from D7 to U1/C4/C5, BUCK_SW from U1 to L1 and D9, BOOT, and FB up to R3/R2 |
| `planes_fanout.py` | In1 GND and In2 +24V planes, with a via from every plane pad |
| `netclasses.py` | Power, Fan, Supply and USB net classes in the project |
| `power_pre.py` | +24V pour and via array on Q1, with room reserved for the VIN pours (`--post` fills them after routing) |
| `export_dsn.py`, `frbest.sh` | Specctra export with the boundary pulled 0.3 mm in from the edge, then Freerouting |
| `finish3.py` | Imports the session; adds the HEAT_N pour and the F/B GND pours; stitches and fills |
| `ripup_loop.sh`, `maze.py` | Re-runs DRC and routes whatever is still unconnected on a 0.05 mm grid |
| `finalize.py`, `undangle.py`, `silk.py` | Solid connections for starved thermals; removes dangling vias and stubs; silkscreen tidy-up |
| `check.sh` | DRC summary; the full report goes in `drc.json` beside the board |

## Done by hand on the committed board

The committed board is a run's `board.kicad_pcb` (31 × 36, `FR_PASSES` 55) with Q2's source pads set to a solid zone connection, which `misc_pre.py` now does itself, plus one later hand edit: JP2 changed from the Pin1Left to the Pin1Right SMD header footprint (the real part's leg stagger) with its pin numbers swapped, so TH_SIG's pad moved up and JP2_A's down by 1.27 mm. Their stubs were re-routed, and VREFP's turn from the left edge onto the bottom-edge run now drops to y 33.81 before turning, clear of JP2's lower pad. A fresh run routes JP2 by itself. The CAN H/L labels on F.Silkscreen at (5.55, 7.65) and (5.55, 5.1) come through from the stripped board.

Coordinates are in mm from the board's top-left corner, seen from the top. KiCad places the board at an offset of (100, 100).
