# Ordering from JLCPCB

The USB toolhead board is ordered as a panel. JLCPCB's standard assembly needs a panel of at least 70 × 70 mm, and one board is 18 × 23.5 mm. There are three panel sizes; pick one and order from its folder:

| Folder | Boards | Layout | Panel size |
| --- | --- | --- | --- |
| `panel/` | 9 | 3 × 3 | 72.3 × 92.8 mm |
| `panel6/` | 6 | 3 columns × 2 rows | 72.3 × 72.0 mm |
| `panel4/` | 4 | 2 × 2 | 72.0 × 72.0 mm |

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

- **J2** (JST-SH, right-angle SMD, C160405): the plug opening must face the bottom edge.
- **J5** (USB-C): the plug opening must face the top edge.
- **U6** (STM32G0B1CEU6, C2829190): JLCPCB had 461 in November 2026. Check the BOM page shows enough stock.
- **JP2, JP3:** bare solder pads, not in the BOM. Bridge JP2 with solder for a PT1000.

## Don't use

- **The KiCad Fabrication Toolkit plugin's output** (a `production/` folder next to a board). Its CPL takes positions and rotations from KiCad's footprints, which puts several parts in the wrong place or orientation for JLCPCB.
- **The single-board set in `usb/`.** It's the board without the panel, for viewing and checking.

## Regenerating

After any change to the board, rebuild everything:

```sh
bash tools/fab.sh          # gerber/usb/
zsh tools/make_panel.sh    # 9 boards: hardware/panel/ and gerber/panel/
zsh tools/make_panel.sh 6  # 6 boards: hardware/panel6/ and gerber/panel6/
zsh tools/make_panel.sh 4  # 4 boards: hardware/panel4/ and gerber/panel4/
```

`make_panel.sh` should report 342, 228 or 152 placements (38 parts per board), all fitted to JLCPCB footprints, and panel DRC with 0 errors and 0 unconnected. Commit the panel folders together with the board change.
