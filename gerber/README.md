# Ordering from JLCPCB

The toolhead is two stacked boards, a logic board and a power board. Both are fabricated and assembled together in one panel, 9 of each. Order from `panel/`.

## Upload these three files

| JLCPCB step | File |
| --- | --- |
| Gerber upload | `panel/toolhead_panel-gerbers.zip` |
| Assembly: BOM | `panel/toolhead_panel-bom-jlcpcb.csv` |
| Assembly: CPL (pick and place) | `panel/toolhead_panel-cpl-jlcpcb.csv` |

Order settings:

- 4 layers, 1.6 mm, 1 oz copper.
- Panel by customer: the zip already holds the 99.3 × 198.6 mm panel, frame, tooling holes and fiducials. Don't ask JLCPCB to panelize it again. It holds two different designs; JLCPCB may price that as more than one design.
- Assembly on both sides. The CPL marks the bottom parts as `Bottom`.
- The silkscreen `JLCJLCJLCJLC` on the bottom rail is where JLCPCB prints its order number. Pick "Specify a location" for the order number.

## Check in the placement preview

The CPL is fitted to JLCPCB's own footprint for each part (`tools/jlc_cpl.py`), so positions and rotations should need no fixing. Still look over:

- **Q1** (SQJ461EP, reverse-polarity FET, logic board): the only part with no JLCPCB footprint to fit, so it uses KiCad's anchor and rotation.
- **J3 and J4** (the board-to-board link): J3 is the 2×6 SMD socket on the logic board's underside, J4 the through-hole header on the power board's top. Check J3's pin 1 matches the silkscreen and that J4 is a through-hole part JLCPCB will fit.
- **U6** (STM32G0B1CBU6, C5270156): JLCPCB had 17 in November 2026, and the panel needs 9. Check the BOM page shows enough stock.
- **U7** (gate driver) and **D10** (12 V zener) on the power board's top. They have no silkscreen marks, so check them against the board.

## Don't use

- **The KiCad Fabrication Toolkit plugin's output** (it writes a `production/` folder next to a board). Its CPL takes positions and rotations from KiCad's footprints, which puts several parts in the wrong place or orientation for JLCPCB. The folder is ignored by git; delete it if the plugin makes one.
- **The single-board sets in `logic/` and `power/`.** They're each board without the panel, for viewing and checking.

## Regenerating

After any change to either board, rebuild both sets:

```sh
bash tools/fab.sh          # gerber/logic/ and gerber/power/
zsh tools/make_panel.sh    # hardware/panel/ and gerber/panel/
```

`make_panel.sh` should report 612 placements on 18 boards and panel DRC with 0 errors and 0 unconnected. Commit `hardware/panel/` and `gerber/panel/` together with the board change.
