# Project footprint library: hotswap_toolhead

J1 in the schematic uses the footprint **`hotswap_toolhead:XT30PW-2+2-M`**.
Put the Amass XT30PW(2+2)-M.G.B footprint in this folder as **`XT30PW-2+2-M.kicad_mod`**.

## Option A – SnapEDA (what you picked)

1. Download the KiCad files from https://www.snapeda.com/parts/XT30PW(2+2)-M.G.B/AMASS/view-part/ (free account needed).
2. Copy the `.kicad_mod` file into this folder and rename it `XT30PW-2+2-M.kicad_mod`.
3. Optional: put the `.step` model next to it and point the footprint's 3D model path at it.

## Option B – LCSC/EasyEDA (no account needed)

```
pip install easyeda2kicad
easyeda2kicad --footprint --3d --lcsc_id=C19268030 --output ./hotswap_toolhead
```

This writes into `hotswap_toolhead.pretty/`; rename the generated `.kicad_mod` to `XT30PW-2+2-M.kicad_mod`.

## Check the pad numbers before layout

The schematic symbol uses: **1 = power +**, **2 = power −**, **3 = signal S1**, **4 = signal S2**.
Open the footprint in the Footprint Editor and confirm its pads use those numbers. Downloaded footprints often number pads differently (or add mounting pads); renumber them to match, otherwise Update PCB from Schematic will put 24 V on the wrong pin. Check the polarity (the + pin) against the Amass datasheet drawing.

The library is already registered for this project in `hardware/fp-lib-table`, so nothing needs adding in KiCad's library settings.
