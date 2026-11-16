# CAN Toolhead Board – Design Spec

Nov 16, 2026 (branch `can-sh`)

## Overview

One 27 × 34 mm, 4-layer board on a 24 V CAN bus. It drives a heater of up to 100 W and a 24 V fan, and reads a thermistor and a switch. It is built around an STM32G0B1 and runs Klipper over CAN as a second MCU (Katapult for updates).

All its connectors are small JST plugs, no XT30:

| Ref | Plug | Carries |
| --- | --- | --- |
| J1 | JST-XH 6-pin (2.5 mm) | 24 V and GND, two contacts each; CAN-H, CAN-L |
| J3 | JST-XH 4-pin (2.5 mm) | Heater, two contacts per side |
| J2 | JST-SH 6-pin (1 mm) | Fan, thermistor, switch |
| J5 | JST-SH 4-pin (1 mm) | USB 2.0: VBUS, D−, D+, GND, wired to a USB socket elsewhere |

This is the `usb-sh` board (one-board USB toolhead) with the stack's (branch `stack`) power input, 3.3 V buck, CAN and heater driver added back. The stack's reverse-polarity P-FET is left out, since the XH plug is keyed. The parts it shares with the stack keep their references.

| Parameter | Target | Why |
| --- | --- | --- |
| Supply | 24 V nominal, 12–30 V | Standard printer rail |
| Heater output | 24 V, 4.2 A (100 W), low-side PWM | Up to a 100 W cartridge; each heater wire on two 3 A XH contacts |
| Fan output | 24 V, up to 0.5 A, low-side PWM, flyback-protected | 2-wire 24 V fans |
| Sensor input | 100k NTC (e.g. 3950), 4.7 kΩ pull-up; PT1000 by solder jumper | |
| Switch input | Switch to GND, 10 kΩ pull-up, RC filter | Endstop, probe or filament switch |
| CAN | Classic CAN, 500 kbit/s or 1 Mbit/s, solder-jumper 120 Ω termination | Klipper default rates |
| USB | USB 2.0 Full Speed on a 4-pin plug; powers the logic on its own | First flash, bench use |
| Input fuse | 8 A | Protects the harness if the heater FET fails short |

## Connector currents

A 100 W heater draws 4.2 A at 24 V; with a 0.5 A fan the board takes about 4.7 A.

- **J1:** 24 V on pins 1–2 and GND on pins 3–4, 2.35 A per contact, under the XH's 3 A.
- **J3:** HEAT− on pins 1–2 and +24 V on pins 3–4, 2.1 A per contact. The heater isn't polarised.
- **Wire:** 22 AWG (0.34 mm²) in the XH crimps for J1's power pins and J3; the XH contacts take 22–28 AWG.
- **J2 and J5:** SH contacts are rated 1 A. The fan draws at most 0.5 A; USB under 0.5 A.

## Power

1. **Fuse (F1):** 8 A 1206 fast-acting fuse (Littelfuse 0458008.DR, C187562, 63 V). Sized as on the stack: 4.7 A is under 75% of its rating after derating for 70 °C.
2. **TVS (D1):** SMF33CA (bidirectional, 200 W, SOD-123FL) from +24V to GND, right after the fuse.
3. **No reverse-polarity FET:** the XH plug only fits one way. If the supply is ever wired reversed, Q2's body diode conducts through the heater: the heater runs at full power and Q2 dissipates about 3.4 W (0.8 V × 4.2 A), which F1 (8 A) doesn't stop and which will overheat Q2 within seconds to minutes. The fan path is limited by F2. Check the polarity of a new harness before first power-up.
4. **Bulk capacitance:** 2 × 10 µF / 50 V X5R 1206 (C1, C2), on the bottom under the +24V strip. As on the stack, there's no electrolytic, so plug J1 in with the supply off.
5. **Logic supply:** +24V → D7 and USB VBUS → D3 (both DSK110 Schottkys) feed VIN_LOGIC, so the board runs from either. VIN_LOGIC feeds a TI LMR16006X buck (U1, 4–60 V, 0.6 A, SOT-23-6) with D9 as catch diode, L1 22 µH (FNR4030S220MT) and C8 22 µF. R2/R3 (33k/10k) set 3.29 V. It runs from VBUS through D3 (about 4.6 V) for programming without 24 V.
6. **Analog reference:** VREF+ and the thermistor pull-up from 3.3 V through FB1 (600 Ω at 100 MHz), with 1 µF + 100 nF (C11, C12), as on the stack.

LEDs: yellow-green on 3.3 V (power, R5 1 kΩ) and blue status on PA15 (R6 100 Ω).

## Heater output

As on the stack:

- **FET (Q2):** AON7264E (C431191), 60 V, DFN 3 × 3 mm, 9.5 mΩ max at 10 V gate (about 13 mΩ hot): about 0.23 W at 4.2 A.
- **Gate driver (U7):** UCC27517 (C99395), non-inverting, from PB9. Its UVLO and input pull-down, and R14 (10 kΩ from PB9 to GND), hold the heater off through reset, before the firmware runs, and on USB power alone.
- **12 V gate rail:** R13 (10 kΩ) from VIN_LOGIC, clamped by D10 (BZX585-C12) with C21 (1 µF).
- **Safety:** Klipper's `verify_heater` and thermal-runaway checks are the primary protection. For an unattended machine, add a thermal fuse in the heater block.

## Fan output

- **Supply:** +24V through F2, a 0.75 A hold 33 V PTC (JK-mSMD075-33, C369169, 1812).
- **Switch (Q3):** WST6066A (60 V, SOT-23), from PB13 through R15 (1 kΩ), R16 (10 kΩ) pull-down.
- **Flyback (D5):** DSK110 across the fan.

The `usb-sh` board ran a 5 V fan from USB; this one runs a 24 V fan.

## CAN

As on the stack: TI TCAN3414 transceiver (U3, VSON-8, ±58 V bus fault protection) on FDCAN2 (PB0 RX, PB1 TX), NUP2105L ESD (D4) by J1, and a 120 Ω termination (R11) through solder jumper JP1. Bridge JP1 only on the board at the end of the bus.

## USB

J5 is a 4-pin JST-SH: 1 VBUS, 2 D−, 3 D+, 4 GND (USB-A pin order). There is no USB-C socket on the board.

- **The other end:** a small USB-C socket board (panel-mount or breakout) wired to J5. It must have the two **5.1 kΩ CC pull-downs**: without them a USB-C host or a C-to-C cable won't turn VBUS on. A USB-A to C cable works without them.
- **Cable:** twisted D+/D−, under about 30 cm. USB Full Speed (12 Mbit/s) doesn't need a matched pair at that length.
- **ESD:** U5 (USBLC6-2SC6) and C17 (10 µF) on VBUS, as before.
- USB is for the first flash and the bench. In the printer, run Klipper over CAN.

## Microcontroller

STM32G0B1CEU6 (C2829190): 512 KB flash, UFQFPN-48, exposed pad to GND, 8 MHz crystal (Y1).

| Function | Pin | Notes |
| --- | --- | --- |
| CAN RX / TX | PB0 / PB1 (19 / 20) | FDCAN2, to U3 |
| USB D− / D+ | PA11 / PA12 (33 / 34) | Through U5 to J5 |
| Heater PWM | PB9 (48) | To U7's IN+; R14 pull-down |
| Fan PWM | PB13 (25) | R15 to Q3's gate; R16 pull-down |
| Thermistor | PB12 (24) | ADC1_IN16, RC-filtered and clamped |
| Switch | PB3 (42) | R22 pull-up, R23 + C20 filter. PB8, used on `usb-sh`, is boxed in here beside the heater's PB9 |
| Status LED | PA15 (37) | Blue, 100 Ω |
| SWCLK / BOOT0 | PA14 (36) | BOOT pads (JP3) to 3.3 V through R4 |
| HSE | PF0 / PF1 (8 / 9) | 8 MHz crystal |
| Reset | NRST (10) | C15, RESET button (SW1) |

## Sensor inputs

- **Thermistor:** R17 (4.7 kΩ 0.1%) from VREFP to TH_SIG; solder jumper JP2 adds R18 (4.12 kΩ) in parallel for a PT1000 (about 2.2 kΩ). R19 (1 kΩ), C19 (100 nF) and D6 (BAT54S clamp) before PB12.
- **Thermistor return:** J2 pin 4 is GND at the bottom-left, by U6. The heater's return runs on the other side of the board: a top-layer GND pour from Q2's source straight up to J1's GND pins. So heater current doesn't flow through the GND under the thermistor's return.
- **Switch:** J2 pin 5 (SENS), R22 (10 kΩ) to 3.3 V, R23 (1 kΩ) and C20 (100 nF) to PB3; closes to J2 pin 6 (GND).

## Connectors

| Ref | Part | Pinout |
| --- | --- | --- |
| J1 | JST S6B-XH-SM4-TB(LF)(SN), XH 2.5 mm 1×6, right-angle SMD (C191914), top edge, plug pointing up. Housing XHP-6, contacts SXH-001T-P0.6 | 1–2 +24V, 3–4 GND, 5 CAN-H, 6 CAN-L |
| J3 | JST S4B-XH-SM4-TB(LF)(SN), XH 1×4 (C161861), bottom edge right, plug pointing down. Housing XHP-4 | 1–2 heater (HEAT−, to Q2), 3–4 heater (+24V) |
| J2 | JST SM06B-SRSS-TB(LF)(SN), SH 1 mm 1×6 (C160405), bottom edge left. Housing SHR-06V-S-B, contacts SSH-003T-P0.2 | 1 FAN+ (24 V via F2), 2 FAN−, 3 TH_SIG, 4 thermistor GND, 5 SENS, 6 GND |
| J5 | JST SM04B-SRSS-TB(LF)(SN), SH 1×4 (C160404), left edge. Housing SHR-04V-S-B | 1 VBUS, 2 D−, 3 D+, 4 GND |
| JP1 | CAN termination, solder pads, open | Bridged: 120 Ω across CAN-H/CAN-L |
| JP2 | PT1000 pull-up, solder pads, open | Bridged: PT1000 |
| JP3 | BOOT, two pads shorted with tweezers | |
| SW1 | RESET, EVQ-P7C01P side-push (C388883), right edge | |

**Mounting:** two M2 half-hole notches (2.2 mm), diagonally opposite: right edge 5.5 mm down (beside J1) and left edge 24.5 mm down (above J2). Parts, tracks, vias and pours stay 2.1 mm from each notch's centre on both sides. The mount needs a recess under the bottom-side parts (L1 is the tallest, 3 mm).

## Layout

- **Stackup:** 4 layers, 1.6 mm, 1 oz outer copper. In1 is solid GND, In2 signals.
- **Floorplan (top view):**
  - J1 across the top edge: +24V pins on the right, CAN on the left over U6's CAN pins.
  - J3 bottom right, J2 bottom left, J5 on the left edge.
  - Top side, in the band between J1 and J3: F1 under J1's +24V pins; the +24V strip down to J3's +24V pins with D1 at its side; Q2 over J3's HEAT− pins with U7 and its 12 V rail left of it; RESET and, below it, the LEDs right of the strip.
  - Bottom side: U6 and its crystal corner in the middle; CAN, the BOOT pads and C10 under J1; USB ESD and the thermistor network down the left; the fan driver under J2 and the buck under J3; C1 and C2 under the strip.
- **Power path** (`tools/layout/can_pre.py`, poured before routing, top layer): VIN_RAW from J1 pins 1–2 to F1; the +24V strip from F1 to J3 pins 3–4, 2.6 mm wide (about 5 A in 1 oz outer copper at a 10 °C rise), which leaves a column for vias between it and SW1/the LEDs; HEAT− from J3 pins 1–2 to Q2's drain; and the GND return beside the strip, from Q2's source and D1 up to J1 pins 3–4. Each pour is built from the pads, so it follows the placement. U6 sits under the heater stage, so the return stays on the top layer instead of dropping through vias. `planes_fanout.py` keeps other nets' fan-out vias out of these pours. Freerouting treats them as planes it may cross, so `pour_clear.py` takes other nets' copper back out of them after routing, and the maze router (which treats them as obstacles) reroutes it.
- **Why 27 × 34 mm:** the two XH plugs set it. J1's footprint is 21.7 × 12 mm and J3's 16.7 × 12 mm (pads plus body), so the band between them on the top side is 10 mm. Across the bottom edge, J3 and J2 side by side, with 0.5 mm from each hold-down pad to the edge, need 27 mm.
- **Routing:** placed by `tools/layout/plan_can.py`, routed by `tools/layout/run_can.sh` (Freerouting 1.9.0, then the maze router).
- **As routed:** 0 DRC errors, 0 unconnected, schematic parity clean; 113 vias and 828 mm of track; each power pour fills in one piece. The only warnings are two vias that join bottom-layer track ends (LED2_A, SENS_IN). The committed board is from `FR_PASSES=200`, `MAZE_ITER=12`, `SOFT_ITERS=0`, which left 3 connections open; 10 more `ripup_loop.sh` passes on its `maze.kicad_pcb` closed them, followed by run_can.sh's clean-up steps. A 100-pass run, finished the same way, had 4 DRC errors.
- **Pin changes on the way:** SENS_IN moved from PB8 (pin 47) to PB3 (42), whose escape isn't boxed in by the heater's PB9. Q2 sits 1.55 mm right of the centre of J3's HEAT− pins and U7 1.2 mm further left than first planned, so the drain and U7's OUT pad clear U6's corner vias underneath (on the stack these join VBAT and VDD through In2). SW1 sits above the LEDs so both side edges are clear at y 19–22 for the panel's lower mouse bites.

## Panel

Order the board as a panel built by `tools/make_panel.sh` (see `gerber/README.md`):

| Panel | Grid | Size | Folders |
| --- | --- | --- | --- |
| 9 | 3 × 3 | 99.3 × 124.3 mm | `hardware/panel/`, `gerber/panel/` |
| 6 | 3 columns × 2 rows | 99.3 × 88.2 mm | `hardware/panel6/`, `gerber/panel6/` |
| 4 | 2 × 2 | 72.0 × 88.2 mm | `hardware/panel4/`, `gerber/panel4/` |

60 parts per board (45 on the bottom), 38 BOM lines; JP1–JP3 are bare pads. Mouse bites at y 2.3 and 20.75 on both side edges.

- **Size:** JLCPCB's standard assembly needs a panel of at least 70 × 70 mm.
- **Holding the boards:** mouse bites on the side edges, clear of the notches (`tools/panel_tabs.py`), four tooling holes and three fiducials.

## Bring-up and firmware

1. **First flash over USB:** wire J5 to a USB socket and plug it into the host, with no 24 V. Check 3.3 V. A blank MCU comes up as an STM32 DFU device; if not, short the BOOT pads and tap RESET.
2. **Flash Katapult** (STM32G0B1, 8 MHz crystal, CAN on PB0/PB1, 8 KiB offset), then Klipper over CAN:
   - Klipper `make menuconfig`: STM32G0B1, 8 KiB bootloader, 8 MHz crystal, "CAN bus (on PB0/PB1)", 1000000 (or your bus rate).
   - `python3 ~/katapult/scripts/flashtool.py -i can0 -q` to find the UUID, then `flashtool.py -i can0 -u <uuid> -f out/klipper.bin`.
3. **24 V and CAN:** plug in J1 (supply off), then power up. Bridge JP1 if this board ends the bus.

Example config:

```
[mcu tool]
canbus_uuid: 0123456789ab

[extruder]
heater_pin: tool:PB9
sensor_type: Generic 3950
sensor_pin: tool:PB12
pullup_resistor: 4700
max_power: 1.0
# ... step_pin, dir_pin etc. as before

[heater_fan hotend_fan]
pin: tool:PB13
heater: extruder
heater_temp: 50.0

[output_pin status_led]
pin: tool:PA15

[temperature_sensor tool_mcu]
sensor_type: temperature_mcu
sensor_mcu: tool

[filament_switch_sensor tool_switch]
switch_pin: !tool:PB3
pause_on_runout: True
```

- **PT1000:** bridge JP2 and set `sensor_type: PT1000`, `pullup_resistor: 2200`.
- **Switch:** PB3 has its own pull-up (R22), so no `^`; `!` reads a closed switch as present. As an endstop: `endstop_pin: !tool:PB3`.

**Prototype checks:**

- [ ] The heater at 100 W for 30 minutes: F1, Q2, J1 and J3 temperatures (the XH contacts are the tightest margin, 2.35 A of 3 A).
- [ ] Heater off through reset, during flashing and on USB power alone.
- [ ] CAN at 1 Mbit/s through a long print.
- [ ] The crystal starts reliably (20 pF load with 33 pF caps).
