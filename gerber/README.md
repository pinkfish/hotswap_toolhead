# Ordering from JLCPCB

The board is fabricated and assembled as a 3 × 3 panel only. Order from `panel/`.

## Upload these three files

| JLCPCB step | File |
| --- | --- |
| Gerber upload | `panel/toolhead_panel-gerbers.zip` |
| Assembly: BOM | `panel/toolhead_panel-bom-jlcpcb.csv` |
| Assembly: CPL (pick and place) | `panel/toolhead_panel-cpl-jlcpcb.csv` |

Order settings:

- 4 layers, 1.6 mm, 1 oz copper.
- Panel by customer: the zip already holds the 3 × 3 array, frame, tooling holes and fiducials. Don't ask JLCPCB to panelize it again.
- Assembly on both sides. The CPL marks the bottom parts as `Bottom`.
- The silkscreen `JLCJLCJLCJLC` on the bottom rail is where JLCPCB prints its order number. Pick "Specify a location" for the order number.

## Check in the placement preview

The CPL is fitted to JLCPCB's own footprint for each part (`tools/jlc_cpl.py`), so positions and rotations should need no fixing. Still look over:

- **Q1** (SQJ461EP, reverse-polarity FET): the only part with no JLCPCB footprint to fit, so it uses KiCad's anchor and rotation.
- **U6** (STM32G0B1CBU6, C5270156): JLCPCB had 17 in November 2026, and the panel needs 9. Check the BOM page shows enough stock.
- **U7** (gate driver, top, beside Q2) and **D10** (12 V zener, bottom, under U7). They have no silkscreen marks, so check them against the board. Seen from the top, U7's pin 1 is the corner on Q2's side, nearer J2's edge, and its OUT pin faces Q2's gate. D10's cathode is the pad nearer the right-hand edge, the edge with SW1.

## Don't use

- **The KiCad Fabrication Toolkit plugin's output** (it writes a `production/` folder next to the board). Its CPL takes positions and rotations from KiCad's footprints, which puts J2, J5, Q2, U5, U6, D4 and others in the wrong place or orientation for JLCPCB. The folder is ignored by git; delete it if the plugin makes one.
- **The single-board files at the top of `gerber/`** (`toolhead-*.g*`, `toolhead-*.drl`, `toolhead-bom-jlcpcb.csv`, `toolhead-cpl-jlcpcb.csv`). They're the same board without the panel, for viewing and checking.

## Regenerating

After any change to the board, rebuild both sets:

```sh
bash tools/fab.sh          # gerber/  (single board)
zsh tools/make_panel.sh    # hardware/panel/ and gerber/panel/
```

`make_panel.sh` should report 594 placements on 9 boards and panel DRC with 0 errors and 0 unconnected. Commit `hardware/panel/` and `gerber/panel/` together with the board change.
