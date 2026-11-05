# Layout scripts

These scripts placed and routed `hardware/toolhead.kicad_pcb` (27 × 36 mm, 4 layers). They are kept so the layout can be redone after a netlist or placement change. They are not needed to open, check or order the board.

```
SRC=src31.kicad_pcb tools/layout/run_narrow.sh /path/to/workdir
```

The 27 mm board is laid out from the routed 31 × 36 mm one (`git show centre-j2:hardware/toolhead.kicad_pcb > src31.kicad_pcb`): `run_narrow.sh` moves its routed blocks across with their copper, places the rest and routes it. `run_layout.sh` is the original from-scratch run that made the 31 mm board. Both copy the project files from `hardware/` into the work directory, leave `board.kicad_pcb` there and never write to `hardware/`. Check the result in KiCad and with `tools/verify.py` before copying it over `hardware/toolhead.kicad_pcb`.

The layout isn't finished at that point. The board is always fabricated as a 3 × 3 panel (see "Panel" in `docs/design_spec.md`), so every layout change must be followed by:

1. `tools/fab.sh`, which regenerates the single-board `gerber/`.
2. `tools/make_panel.sh`, which rebuilds `hardware/panel/` and `gerber/panel/`. It must report 9 boards and 594 placements, with panel DRC at 0 errors and 0 unconnected.
3. Committing the board, `gerber/`, `hardware/panel/` and `gerber/panel/` together.

Keep the tab windows clear of copper at the side edges (y 9.0–10.9 and 16.5–18.8, left and right; there are no top/bottom tabs), or move the tabs in `tools/panel_tabs.py`.

## Requirements

- **KiCad 10:** its Python (`KICAD_PY`) and `kicad-cli` (`KICAD_CLI`). The defaults are the macOS app paths.
- **Freerouting 1.9.0:** set `FREEROUTING_JAR` to the jar. It isn't in the repo. 2.x crashed or hung on this board.
- **Java 21 or newer:** set `JAVA` if `java` isn't on the path. Freerouting 1.9.0 opens its window while it routes.

Other settings: `BW`/`BH` set the board size (`run_narrow.sh` defaults to 27 × 36, `run_layout.sh` to 31 × 36); `C1Y`, `U6X` and `U6Y` move C1 and the MCU in `run_layout.sh`. `MAZE_ITER` sets the maze clean-up passes (default 6), `SOFT_ITERS` how many of them may rip up unlocked routes. `FR_PASSES` and `FR_TIMEOUT` control Freerouting. `PRE_ONLY=1` stops after the Specctra export, leaving `pre_route.kicad_pcb` and `toolhead.dsn`. `HARD` (`run_narrow.sh`) lists the nets maze-routed and locked before Freerouting; `HARD=` skips that.

Freerouting 1.9.0 isn't deterministic here: the same pre-route board gives different results run to run (one run took 27 s, the next 90 s), and a run can end with one to three connections open. The committed 27 mm board came from running `run_narrow.sh` three times side by side (default `HARD`, `HARD=` and `HARD=/VREFP,/NRST,/+3V3`) and keeping the one that ended with 0 unconnected; run it again a few times rather than adding maze passes. When the same connection stays open across runs, it needs a pre-route (`narrow_pre.py`) instead.

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
| `finish3.py` | Imports the session; adds the HEAT_N pour and the F/B GND pours; stitches (keeping stitching vias 0.25 mm from any drilled pad) and fills |
| `ripup_loop.sh`, `maze.py` | Re-runs DRC and routes whatever is still unconnected on a 0.05 mm grid. `ONLY`/`ORDER`/`LOCK` route just the listed nets, in that order, and lock them (the `HARD` step) |
| `finalize.py`, `undangle.py`, `silk.py` | Solid connections for starved thermals; removes dangling vias, then dangling stubs and the near-zero-length scraps of the session import, keeping any whose removal would open a connection; silkscreen tidy-up |
| `check.sh` | DRC summary; the full report goes in `drc.json` beside the board |
| `blocks.py` | `run_narrow.sh`: copies the 31 mm board with C1 swapped to the 1206 ceramic and the holes to M2.5, then moves its routed blocks (power input, USB-C, MCU with crystal and CAN, buck, J2, F2) to the 27 mm outline with their own copper; sets SW1's duplicate pad numbers as jumpers (its two pin-1 pads are joined inside the switch) and trims F2's courtyard to its pads plus 0.05 mm so it clears J2's |
| `plan_narrow.py` | `run_narrow.sh`: the `PLAN` that `place.py` reads (`PLAN_FILE`) for the parts not in a block; block parts keep their place |
| `declash.py` | Removes moved block copper that DRC reports in a clash with the new placement, then copper left touching no pad; in a clash with a `narrow_pre.py` pre-route only the other copper goes |
| `narrow_pre.py` | `run_narrow.sh` pre-routes, grouped so `declash.py` keeps them: FAN_P to D5 round J2, D7's +24V via, LED_STAT and the LED anodes, R5's +3V3 to R2, F2's +24V via, HEAT_PWM to U7 and R14, NRST over C8 to SW1, VREFP out of its decoupling and back west between C8 and F2, U6's +3V3 vias to C8, FB1's +3V3 to L1, C8's GND via, FAN_PWM round the CAN pair to R15, CAN_L to U3 |
| `island_vias.py` | A GND via in each F/B GND pour island that has none (an island boxed in by tracks counts as unconnected) |
| `gate_driver.py` | Applied once to the committed board, after the run: adds the heater gate driver U7 beside Q2 and its 12 V rail (R13 from VIN_LOGIC, D10, C21) underneath, moves R14 up beside C2, and re-routes HEAT_PWM round U7 to IN+ |

## Done by hand on the committed board

The committed 27 mm board is `run_narrow.sh`'s `board.kicad_pcb` from the run that routed fully, with three fixes made by hand that the scripts now make themselves: a stitching via 0.1 mm from J2 pin 7's drill removed (`finish3.py` now keeps clear of drilled pads), a dangling FAN_P via and stub past D5 removed, and a second `finalize.py`/`undangle.py` pass. C21's and U7's references were also moved to F.Fab, as their silk sat on each other's pads.

The 31 mm board it started from was a `run_layout.sh` run (`FR_PASSES` 55) with Q2's source pads set to a solid zone connection, which `misc_pre.py` now does itself, plus two later edits. First, JP2 changed from the Pin1Left to the Pin1Right SMD header footprint (the real part's leg stagger) with its pin numbers swapped, so TH_SIG's pad moved up and JP2_A's down by 1.27 mm. Second, `gate_driver.py` added the heater gate driver: U7 on top between Q2 and the right edge, the GATE_12V rail parts under it, R14 moved up beside C2, and R13 turned from the gate series resistor into the rail's feed resistor on the bottom. `place.py` and `heat_pre.py` still describe the earlier direct gate drive, so a fresh `run_layout.sh` run needs `gate_driver.py` after it. The CAN H/L labels on F.Silkscreen come through from that board.

Coordinates are in mm from the board's top-left corner, seen from the top. KiCad places the board at an offset of (100, 100).
