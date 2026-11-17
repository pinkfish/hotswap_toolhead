# Ordering from JLCPCB

The CAN toolhead stack is ordered as one panel holding both boards, in columns of logic/power pairs. JLCPCB's standard assembly needs a panel of at least 70 × 70 mm, and each board is 25 × 26 mm. There are three panel sizes; pick one and order from its folder:

| Folder | Pairs | Layout | Panel size |
| --- | --- | --- | --- |
| `panel/` | 9 | 3 columns of 3 pairs | 93.3 × 184.6 mm |
| `panel6/` | 6 | 3 columns of 2 pairs | 93.3 × 128.4 mm |
| `panel4/` | 4 | 4 columns of 1 pair | 120.4 × 72.2 mm |

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
- The link header J7 on each power board is a through-hole part (HX PZ2.54-2x4P ZZ): JLCPCB solders it as through-hole assembly.
- The silkscreen `JLCJLCJLCJLC` on the frame is where JLCPCB prints its order number. Pick "Specify a location" for the order number.

## Check in the placement preview

The CPL is fitted to JLCPCB's own footprint for each part (`tools/jlc_cpl.py`), so positions and rotations should need no fixing. Still look over these:

- **J1** (logic, JST-XH 6-pin, C191914): the plug opening must face the top edge.
- **J2** (logic, JST-SH 6-pin, C160405) and **J3** (power, JST-XH 4-pin, C161861): the plug openings must face the bottom edge.
- **J5** (logic, JST-SH 4-pin, C160404): the plug opening must face the left edge.
- **J6** (logic underside, link socket, C22373945; 316 in stock in November 2026) and **J7** (power, link header, C32713277).
- **Q2** (power, AON7264E, DFN 3 × 3): the large drain pad toward J3.
- **U6** (STM32G0B1CEU6, C2829190): JLCPCB had 461 in November 2026. Check the BOM page shows enough stock.
- **JP1, JP2, JP3:** bare solder pads, not in the BOM. Bridge JP1 for CAN termination, JP2 for a PT1000.

## Don't use

- **The KiCad Fabrication Toolkit plugin's output** (a `production/` folder next to a board). Its CPL takes positions and rotations from KiCad's footprints, which puts several parts in the wrong place or orientation for JLCPCB.
- **The single-board sets in `logic/` and `power/`.** They're the boards without the panel, for viewing and checking.

## Regenerating

After any change to the board, rebuild everything:

```sh
bash tools/fab.sh          # gerber/logic/ and gerber/power/
zsh tools/make_panel.sh    # 9 pairs: hardware/panel/ and gerber/panel/
zsh tools/make_panel.sh 6  # 6 pairs: hardware/panel6/ and gerber/panel6/
zsh tools/make_panel.sh 4  # 4 pairs: hardware/panel4/ and gerber/panel4/
```

`make_panel.sh` should report 558, 372 or 248 placements (62 parts per logic + power pair), all fitted to JLCPCB footprints, and panel DRC with 0 errors and 0 unconnected. Commit the panel folders together with the board change.
