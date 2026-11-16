# Ordering from JLCPCB

The CAN toolhead board is ordered as a panel. JLCPCB's standard assembly needs a panel of at least 70 × 70 mm, and one board is 27 × 34 mm. There are three panel sizes; pick one and order from its folder:

| Folder | Boards | Layout | Panel size |
| --- | --- | --- | --- |
| `panel/` | 9 | 3 × 3 | 99.3 × 124.3 mm |
| `panel6/` | 6 | 3 columns × 2 rows | 99.3 × 88.2 mm |
| `panel4/` | 4 | 2 × 2 | 72.0 × 88.2 mm |

Where the boards come to less than 72 mm on a side, `tools/make_panel.sh` widens the gap to the frame on that side. All three panels are inside JLCPCB's standard-assembly range (70 × 70 to 250 × 250 mm).

## Upload these three files

The names below are for `panel/`; in `panel6/` and `panel4/` they are `toolhead_panel6-…` and `toolhead_panel4-…`.

| JLCPCB step | File |
| --- | --- |
| Gerber upload | `panel/toolhead_panel-gerbers.zip` |
| Assembly: BOM | `panel/toolhead_panel-bom-jlcpcb.csv` |
| Assembly: CPL (pick and place) | `panel/toolhead_panel-cpl-jlcpcb.csv` |

Order settings:

- 4 layers, 1.6 mm, 1 oz copper.
- Panel by customer: the zip already holds the panel, frame, tooling holes and fiducials. Don't ask JLCPCB to panelize it again.
- Assembly on both sides. The CPL marks the bottom parts as `Bottom`.
- The silkscreen `JLCJLCJLCJLC` on the frame is where JLCPCB prints its order number. Pick "Specify a location" for the order number.

## Check in the placement preview

The CPL is fitted to JLCPCB's own footprint for each part (`tools/jlc_cpl.py`), so positions and rotations should need no fixing. Still look over these:

- **J1** (JST-XH 6-pin, C191914): the plug opening must face the top edge.
- **J3** (JST-XH 4-pin, C161861) and **J2** (JST-SH 6-pin, C160405): the plug openings must face the bottom edge.
- **J5** (JST-SH 4-pin, C160404): the plug opening must face the left edge.
- **Q2** (AON7264E, DFN 3 × 3): the large drain pad toward J3.
- **U6** (STM32G0B1CEU6, C2829190): JLCPCB had 461 in November 2026. Check the BOM page shows enough stock.
- **JP1, JP2, JP3:** bare solder pads, not in the BOM. Bridge JP1 for CAN termination, JP2 for a PT1000.

## Don't use

- **The KiCad Fabrication Toolkit plugin's output** (a `production/` folder next to a board). Its CPL takes positions and rotations from KiCad's footprints, which puts several parts in the wrong place or orientation for JLCPCB.
- **The single-board set in `can/`.** It's the board without the panel, for viewing and checking.

## Regenerating

After any change to the board, rebuild everything:

```sh
bash tools/fab.sh          # gerber/can/
zsh tools/make_panel.sh    # 9 boards: hardware/panel/ and gerber/panel/
zsh tools/make_panel.sh 6  # 6 boards: hardware/panel6/ and gerber/panel6/
zsh tools/make_panel.sh 4  # 4 boards: hardware/panel4/ and gerber/panel4/
```

`make_panel.sh` should report 540, 360 or 240 placements (60 parts per board), all fitted to JLCPCB footprints, and panel DRC with 0 errors and 0 unconnected. Commit the panel folders together with the board change.
