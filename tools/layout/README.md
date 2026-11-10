# Layout scripts

These scripts placed and routed `hardware/toolhead_usb.kicad_pcb` (18 × 23.5 mm, 4 layers). They are kept so the layout can be redone after a netlist or placement change. They are not needed to open, check or order the board.

```
git show stack:hardware/toolhead_logic.kicad_pcb > donor.kicad_pcb
SRC=donor.kicad_pcb tools/layout/run_usb.sh /path/to/work
```

`run_usb.sh` lays out the board from its schematic, in these steps:

1. Exports the netlist.
2. Builds a board from it with `from_netlist.py`. Footprints come from the stack's logic board (`SRC`) wherever the part and footprint match, so its pad and courtyard edits carry over.
3. Brings that board's routed MCU corner across, turned with U6 to `U6_AT` (`corner_import.py`).
4. Places the rest from `plan_usb.py`.
5. Pre-routes and locks the USB pair (`usb_pair_pre.py`).
6. Adds the In1 GND plane and the plane fan-out.
7. Routes the rest with Freerouting, then the maze clean-up loop.

It copies the project files from `hardware/` into the work directory, leaves `board.kicad_pcb` there and never writes to `hardware/`. Check the result in KiCad, then copy it over `hardware/toolhead_usb.kicad_pcb` and run `tools/verify.py`.

The layout isn't finished at that point. The board is always fabricated in a panel (see "Panel" in `docs/design_spec.md`), so every layout change must be followed by:

1. `tools/fab.sh`, which regenerates `gerber/usb/`.
2. `tools/make_panel.sh` with 9, 6 and 4, which rebuilds `hardware/panel*/` and `gerber/panel*/`. Each must report panel DRC at 0 errors and 0 unconnected.
3. Committing the board, `gerber/` and `hardware/panel*/` together.

`tools/panel_tabs.py` finds the tab positions itself: two tabs on each side edge, as far apart as the clear stretches of edge allow, where no copper is within 0.6 mm of either side edge and no part overhangs it. It stops with an error if the board has no room for two.

`run_layout.sh` and `run_narrow.sh` are the 24 V single-board flows (branches `centre-j2` and `narrow-27`), and many of the `*_pre.py` scripts below belong to them. They expect files this branch doesn't have.

## Requirements

- **KiCad 10:** its Python (`KICAD_PY`) and `kicad-cli` (`KICAD_CLI`). The defaults are the macOS app paths.
- **Freerouting 1.9.0:** set `FREEROUTING_JAR` to the jar. It isn't in the repo. 2.x crashed or hung on this board.
- **Java 21 or newer:** set `JAVA` if `java` isn't on the path. Freerouting 1.9.0 opens its window while it routes.

Other settings: `BW`/`BH` set the board size (`run_usb.sh` defaults to 18 × 23.5, `run_narrow.sh` to 27 × 36, `run_layout.sh` to 31 × 36), `U6_AT` the MCU's place in `run_usb.sh` (default: centred, 12.2 mm down); `V24_TOP` (logic board) sets the outline of the top-layer +24V pour, `IN2_SPLIT` instead makes In2 a +24V strip and a +3V3 plane (tried first; it left too little routing room); `C1Y`, `U6X` and `U6Y` move C1 and the MCU in `run_layout.sh`. `MAZE_ITER` sets the maze clean-up passes (default 6), `SOFT_ITERS` how many of them may rip up unlocked routes. `FR_PASSES` and `FR_TIMEOUT` control Freerouting. `PRE_ONLY=1` stops after the Specctra export, leaving `pre_route.kicad_pcb` and `toolhead.dsn`. `HARD` lists the nets maze-routed and locked before Freerouting (`run_usb.sh`: none, `usb_pair_pre.py` lays the pair instead; `run_narrow.sh`: its own default list; `HARD=` skips it).

Freerouting 1.9.0 isn't deterministic: the same pre-route board gives different results from run to run, and a run can end with a connection or two open. Run it again a few times rather than adding maze passes. On the USB board the maze's rip-up passes made things worse; `SOFT_ITERS=0` keeps it to adding copper. When the same connection stays open across runs, it needs a pre-route or a placement change instead.

## Steps

| Script | What it does |
|---|---|
| `from_netlist.py` | Builds a board from the schematic netlist, taking each footprint from the donor board when the part and footprint match (H1/H2 always, unless `KEEP` lists other references; `run_usb.sh` keeps none), otherwise from the KiCad or project library |
| `strip.py` | Copies the board without tracks, vias and zones, and resets pad zone connections |
| `place.py` | Places parts from `PLAN` (x, y, rotation, side, fixed), draws the outline and hole keep-outs (when the plan has holes), and pushes movable parts apart until no courtyards overlap |
| `sync_nets.py` | Re-assigns pad nets from the schematic netlist, so a pin change in `design.py` reaches the stripped board |
| `corner_pre.py` | Hand layout of the U6 pin 4–10 corner: crystal, load caps, VREF, NRST; VREFP's exit round FB1 and FB1's +3V3 via |
| `misc_pre.py` | Q2 source bar, solid to the GND pours; JP3 BOM flags |
| `usb_pre.py` | USB-C data pins joined on F.Cu, one via per pair down to the USBLC6 (U5), then D+/D− on F.Cu to vias in front of U6 pins 34/33; SWCLK round JP3 to R4; the A9 VBUS via; CC1/CC2 vias above their pads; the F.Cu keep-out under the receptacle body |
| `left_pre.py` | Lanes from U6's left side on B.Cu: TH_ADC to R19/C19/D6, SENS_IN to C20, CAN_TX/RX to U3; the CAN_H/CAN_L escape from U3 and U3's GND ties and +3V3 feed; FAN_PWM across on F.Cu to R15/R16 |
| `sig_fanout.py` | Escape vias for the listed U6 pins |
| `heat_pre.py` | HEAT_PWM from its escape via under SW1 and down the right edge to R13/R14; R14's GND tied to Q2's source and Q2 pin 1's via; NRST from SW1 round that run to C15 |
| `buck_pre.py` | Buck links on B.Cu: VIN_LOGIC from D7 to U1/C4/C5, BUCK_SW from U1 to L1 and D9, BOOT, and FB up to R3/R2 |
| `planes_fanout.py` | In1 GND and In2 +24V planes, with a via from every plane pad. With `V24_TOP` (the logic board), +24V is a top-layer pour along the top edge instead, from Q1's source to J3's +24V pins, its bottom-side pads get vias inside it, and In2 is left to the router. `SKIP_ROUTED` leaves pads that pre-placed copper already ties to a via |
| `plan_usb.py` | `run_usb.sh`: the `PLAN` that `place.py` reads (`PLAN_FILE`). Fixed: J5, J2, SW1, U6 with its corner parts, and most of the rest; positions follow the board's width and height |
| `usb_pair_pre.py` | `run_usb.sh`: the USB pair from J5 through U5 to U6, with fixed coordinates: D+ strapped above J5's pad row and D− below it, each to a via in its U5 pin; D− straight down to U6 pin 33 on B.Cu; D+ over D−'s via on In2 to a second via and down to pin 34; a GND via in U5 pin 2; J5's right VBUS pad and CC1 out along under the pad row to vias right of J5's shell leg, VBUS on to C17. Drawn for a 22 mm board and shifted with the centre line (`BW`). Stops if the pads have moved |
| `corner_import.py` | Before placing: puts U6 at its new place and rotation and brings the donor's crystal, load caps, NRST cap and VDD/VREF+ decoupling corner across with it, turned to match, with that corner's bottom-side copper and plane vias |
| `crtyd_trim.py` | Cuts a footprint's courtyard to its pads and body plus a margin (the stack's J3, so the panel's mouse bites cleared it) |
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
| `add_vias.py` | Stitches a net between layers with as many vias as fit in a region: each candidate on a grid must sit inside the net's pours on two layers, off every SMD pad and 0.3 mm clear of other holes, and pass DRC (errors and warnings) |
| `gate_driver.py` | Applied once to the 31 mm board, after the run: adds the heater gate driver U7 beside Q2 and its 12 V rail (R13 from VIN_LOGIC, D10, C21) underneath, moves R14 up beside C2, and re-routes HEAT_PWM round U7 to IN+ |

## Done by hand on the single 27 × 36 board (branch `narrow-27`)

The 27 mm board is `run_narrow.sh`'s `board.kicad_pcb` from the run that routed fully, with three fixes made by hand that the scripts now make themselves: a stitching via 0.1 mm from J2 pin 7's drill removed (`finish3.py` now keeps clear of drilled pads), a dangling FAN_P via and stub past D5 removed, and a second `finalize.py`/`undangle.py` pass. C21's and U7's references were also moved to F.Fab, as their silk sat on each other's pads.

The 31 mm board it started from was a `run_layout.sh` run (`FR_PASSES` 55) with Q2's source pads set to a solid zone connection, which `misc_pre.py` now does itself, plus two later edits. First, JP2 changed from the Pin1Left to the Pin1Right SMD header footprint (the real part's leg stagger) with its pin numbers swapped, so TH_SIG's pad moved up and JP2_A's down by 1.27 mm. Second, `gate_driver.py` added the heater gate driver: U7 on top between Q2 and the right edge, the GATE_12V rail parts under it, R14 moved up beside C2, and R13 turned from the gate series resistor into the rail's feed resistor on the bottom. `place.py` and `heat_pre.py` still describe the earlier direct gate drive, so a fresh `run_layout.sh` run needs `gate_driver.py` after it. The CAN H/L labels on F.Silkscreen come through from that board.

Coordinates are in mm from the board's top-left corner, seen from the top. KiCad places the board at an offset of (100, 100).
