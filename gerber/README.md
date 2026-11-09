# Ordering from JLCPCB

The toolhead is two stacked boards, a logic board and a power board. Both are fabricated and assembled together in one panel. There are three panel sizes; pick one and order from its folder:

| Folder | Boards | Layout | Panel size |
| --- | --- | --- | --- |
| `panel/` | 9 of each | 3 columns × 3 pairs | 99.3 × 198.6 mm |
| `panel6/` | 6 of each | 3 columns × 2 pairs | 99.3 × 136.4 mm |
| `panel4/` | 4 of each | 4 columns × 1 pair | 128.4 × 74.2 mm |

All three are inside JLCPCB's standard-assembly panel range (70 × 70 to 250 × 250 mm). Four of each in 2 columns × 2 pairs would be 70.2 mm wide, too close to the 70 mm minimum, so `panel4/` is one row.

## Upload these three files

The names below are for `panel/`; in `panel6/` and `panel4/` they are `toolhead_panel6-…` and `toolhead_panel4-…`.

| JLCPCB step | File |
| --- | --- |
| Gerber upload | `panel/toolhead_panel-gerbers.zip` |
| Assembly: BOM | `panel/toolhead_panel-bom-jlcpcb.csv` |
| Assembly: CPL (pick and place) | `panel/toolhead_panel-cpl-jlcpcb.csv` |

Order settings:

- 4 layers, 1.6 mm, 1 oz copper.
- Panel by customer: the zip already holds the panel, frame, tooling holes and fiducials. Don't ask JLCPCB to panelize it again. It holds two different designs; JLCPCB may price that as more than one design.
- Assembly on both sides. The CPL marks the bottom parts as `Bottom`.
- The silkscreen `JLCJLCJLCJLC` on the bottom rail is where JLCPCB prints its order number. Pick "Specify a location" for the order number.

## Check in the placement preview

The CPL is fitted to JLCPCB's own footprint for each part (`tools/jlc_cpl.py`), so positions and rotations should need no fixing. Still look over:

- **Q1** (SQJ461EP, reverse-polarity FET, logic board): the only part with no JLCPCB footprint to fit, so it uses KiCad's anchor and rotation.
- **J3 and J4** (the board-to-board link): J3 is the 2×6 SMD socket on the logic board's underside, J4 the through-hole header on the power board's top. Check J3's pin 1 matches the silkscreen and that J4 is a through-hole part JLCPCB will fit.
- **U6** (STM32G0B1CBU6, C5270156): JLCPCB had 17 in November 2026, and a panel needs 9, 6 or 4. Check the BOM page shows enough stock.
- **U7** (gate driver) and **D10** (12 V zener) on the power board's top. They have no silkscreen marks, so check them against the board.

## Don't use

- **The KiCad Fabrication Toolkit plugin's output** (it writes a `production/` folder next to a board). Its CPL takes positions and rotations from KiCad's footprints, which puts several parts in the wrong place or orientation for JLCPCB. The folder is ignored by git; delete it if the plugin makes one.
- **The single-board sets in `logic/` and `power/`.** They're each board without the panel, for viewing and checking.

## Regenerating

After any change to either board, rebuild both sets:

```sh
bash tools/fab.sh          # gerber/logic/ and gerber/power/
zsh tools/make_panel.sh    # 9 of each: hardware/panel/ and gerber/panel/
zsh tools/make_panel.sh 6  # 6 of each: hardware/panel6/ and gerber/panel6/
zsh tools/make_panel.sh 4  # 4 of each: hardware/panel4/ and gerber/panel4/
```

`make_panel.sh` should report 612, 408 or 272 placements on 18, 12 or 8 boards, and panel DRC with 0 errors and 0 unconnected. Commit the panel folders together with the board change.
