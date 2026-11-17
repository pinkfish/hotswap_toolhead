# CAN Toolhead Stack – Design Spec

Nov 16, 2026 (branch `can-stack`)

## Overview

Two stacked 25 × 26 mm, 4-layer boards on a 24 V CAN bus, joined by a 2 × 4 board-to-board link. Together they drive a heater of up to 100 W and a 24 V fan, and read a thermistor and a switch. They are built around an STM32G0B1 and run Klipper over CAN as a second MCU (Katapult for updates).

This is the one-board CAN toolhead of branch `can-sh` (27 × 34 mm, 918 mm²) split in two, so it fits within 25 mm of width: the footprint is 650 mm², 29% less, for about 12.6 mm more height (the second board and the 11 mm gap). The circuit is the same apart from the split and the heater's MCU pin (PD0).

All the plugs are small JST plugs, no XT30:

| Ref | Board | Plug | Carries |
| --- | --- | --- | --- |
| J1 | Logic | JST-XH 6-pin (2.5 mm) | 24 V and GND, two contacts each; CAN-H, CAN-L |
| J2 | Logic | JST-SH 6-pin (1 mm) | Fan, thermistor, switch |
| J5 | Logic | JST-SH 4-pin (1 mm) | USB 2.0: VBUS, D−, D+, GND, wired to a USB socket elsewhere |
| J3 | Power | JST-XH 4-pin (2.5 mm) | Heater, two contacts per side |

The reverse-polarity P-FET of branch `stack` is left out, since the XH plug is keyed. Parts keep the references they have on `stack` and `can-sh`.

## Two-board stack

- **Logic board (upper):** J1 with the fuse (F1), TVS (D1) and C1; the MCU with its crystal, decoupling, RESET, BOOT and LEDs; CAN (U3, D4, R11, JP1); USB (J5, U5, C17, D3); the fan driver (F2, Q3, D5, R15, R16) and J2; the thermistor and switch inputs. Its top side faces out; the link socket J6 is on its underside.
- **Power board (lower):** the heater plug J3, the heater FET and gate driver (Q2, U7, R13, D10, C21, R14), C2, and the 3.3 V buck (D7, U1, L1, D9, C4–C6, C8, R2, R3). The link header J7 is on its top side, facing the logic board.
- **Why this split:** each board carries one of the 12 mm-deep XH plugs, which set the single board's 34 mm. The fan stays on the logic board with its plug J2; the buck goes on the power board, which has the room.
- **Link:** 2 × 4 at 2.54 mm, 3 A per contact: J6 is an SMD socket, 8.5 mm tall (HC-PM254-8.5H-2x4PS, C22373945), J7 a through-hole header with a 2.5 mm spacer (HX PZ2.54-2x4P ZZ, C32713277). Mated, the boards are 11.0 mm apart.

| Pins | Net | Notes |
| --- | --- | --- |
| 1, 2 | +24V | After F1: up to 4.7 A (100 W heater and fan), 2.35 A per contact |
| 3, 4, 6 | GND | The heater's return, 1.6 A per contact |
| 5 | VIN_LOGIC | To the buck: +24V through D7 on the power board, or USB VBUS through D3 on the logic board |
| 7 | HEAT_PWM | PD0 to U7; R14 holds it low on the power board, so the heater stays off with the boards apart |
| 8 | +3V3 | From the buck to the logic board, under 100 mA |

- **Heights in the gap:** the heater plug J3 (about 6.1 mm tall) and L1 (3 mm) stand on the power board's top side; above them the logic board's underside has only small parts (U6 and passives under 1.2 mm, RESET 3.5 mm at the right edge).
- **Overall height:** about 1.6 + 11 + 1.6 mm of boards and gap, plus J1 (about 6 mm) on the logic board's top and J7's pin ends (about 3 mm) under the power board.
- **Check:** `tools/check_stack.py` confirms that the two outlines and notches match and that every J7 pin sits under its J6 contact with the net `design.LINK` gives it.

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
- **Link (J6/J7):** see above: 2.35 A per +24V contact, 1.6 A per GND contact, of 3 A.

## Power

1. **Fuse (F1):** 8 A 1206 fast-acting fuse (Littelfuse 0458008.DR, C187562, 63 V). Sized as on the stack: 4.7 A is under 75% of its rating after derating for 70 °C.
2. **TVS (D1):** SMF33CA (bidirectional, 200 W, SOD-123FL) from +24V to GND, right after the fuse.
3. **No reverse-polarity FET:** the XH plug only fits one way. If the supply is ever wired reversed, Q2's body diode conducts through the heater: the heater runs at full power and Q2 dissipates about 3.4 W (0.8 V × 4.2 A), which F1 (8 A) doesn't stop and which will overheat Q2 within seconds to minutes. The fan path is limited by F2. Check the polarity of a new harness before first power-up.
4. **Bulk capacitance:** 2 × 10 µF / 50 V X5R 1206: C1 on the logic board under F2, C2 on the power board by the heater's +24V strip. As on the stack, there's no electrolytic, so plug J1 in with the supply off.
5. **Logic supply:** +24V → D7 and USB VBUS → D3 (both DSK110 Schottkys) feed VIN_LOGIC, so the board runs from either. VIN_LOGIC feeds a TI LMR16006X buck (U1, 4–60 V, 0.6 A, SOT-23-6) with D9 as catch diode, L1 22 µH (FNR4030S220MT) and C8 22 µF. R2/R3 (33k/10k) set 3.29 V. It runs from VBUS through D3 (about 4.6 V) for programming without 24 V.
6. **Analog reference:** VREF+ and the thermistor pull-up from 3.3 V through FB1 (600 Ω at 100 MHz), with 1 µF + 100 nF (C11, C12), as on the stack.

LEDs: yellow-green on 3.3 V (power, R5 1 kΩ) and blue status on PA15 (R6 100 Ω).

## Heater output

As on the stack:

- **FET (Q2):** AON7264E (C431191), 60 V, DFN 3 × 3 mm, 9.5 mΩ max at 10 V gate (about 13 mΩ hot): about 0.23 W at 4.2 A.
- **Gate driver (U7):** UCC27517 (C99395), non-inverting, from PD0 through link pin 7. Its UVLO and input pull-down, and R14 (10 kΩ to GND, on the power board), hold the heater off through reset, before the firmware runs, on USB power alone and with the boards apart.
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
| Heater PWM | PD0 (38) | Through link pin 7 to U7's IN+; R14 pull-down on the power board. PD0 is at the top of the side facing J6; `can-sh` used PB9 |
| Fan PWM | PB13 (25) | R15 to Q3's gate; R16 pull-down |
| Thermistor | PB12 (24) | ADC1_IN16, RC-filtered and clamped |
| Switch | PB3 (42) | R22 pull-up, R23 + C20 filter |
| Status LED | PA15 (37) | Blue, 100 Ω |
| SWCLK / BOOT0 | PA14 (36) | BOOT pads (JP3) to 3.3 V through R4 |
| HSE | PF0 / PF1 (8 / 9) | 8 MHz crystal |
| Reset | NRST (10) | C15, RESET button (SW1) |

## Sensor inputs

- **Thermistor:** R17 (4.7 kΩ 0.1%) from VREFP to TH_SIG; solder jumper JP2 adds R18 (4.12 kΩ) in parallel for a PT1000 (about 2.2 kΩ). R19 (1 kΩ), C19 (100 nF) and D6 (BAT54S clamp) before PB12.
- **Thermistor return:** J2 pin 4 is GND by U6 on the logic board. The heater's return comes up the link's GND pins under J1's right half and runs to J1's GND pins, away from J2.
- **Switch:** J2 pin 5 (SENS), R22 (10 kΩ) to 3.3 V, R23 (1 kΩ) and C20 (100 nF) to PB3; closes to J2 pin 6 (GND).

## Connectors

| Ref | Part | Pinout |
| --- | --- | --- |
| J1 | Logic: JST S6B-XH-SM4-TB(LF)(SN), XH 2.5 mm 1×6, right-angle SMD (C191914), top edge, plug pointing up. Housing XHP-6, contacts SXH-001T-P0.6 | 1–2 +24V, 3–4 GND, 5 CAN-H, 6 CAN-L |
| J2 | Logic: JST SM06B-SRSS-TB(LF)(SN), SH 1 mm 1×6 (C160405), bottom edge, 2.5 mm right of centre. Housing SHR-06V-S-B, contacts SSH-003T-P0.2 | 1 FAN+ (24 V via F2), 2 FAN−, 3 TH_SIG, 4 thermistor GND, 5 SENS, 6 GND |
| J5 | Logic: JST SM04B-SRSS-TB(LF)(SN), SH 1×4 (C160404), left edge. Housing SHR-04V-S-B | 1 VBUS, 2 D−, 3 D+, 4 GND |
| J3 | Power: JST S4B-XH-SM4-TB(LF)(SN), XH 1×4 (C161861), bottom edge, top side (in the gap), plug pointing down. Housing XHP-4 | 1–2 heater (HEAT−, to Q2), 3–4 heater (+24V) |
| J6, J7 | The link: socket under the logic board, header on the power board | See "Two-board stack" |
| JP1 | CAN termination, solder pads, open | Bridged: 120 Ω across CAN-H/CAN-L |
| JP2 | PT1000 pull-up, solder pads, open | Bridged: PT1000 |
| JP3 | BOOT, two pads shorted with tweezers | |
| SW1 | RESET, EVQ-P7C01P side-push (C388883), on the logic board's underside at the right edge | |

**Mounting:** two M2 half-hole notches (2.2 mm) in the same places on both boards, diagonally opposite: right edge 7.0 mm down and left edge 22.5 mm down. Parts, tracks, vias and pours stay 2.1 mm from each notch's centre on both sides of both boards, room for an M2 screw head or a standoff's end up to 4 mm across. Use M2 × 11 mm female-female standoffs between the boards: a screw through each logic-board notch into the standoff, and one through the power-board notch into the mount (or into the standoff from below). Fit the logic board onto J7 with the power off. The power board's underside has only J7's pin ends (about 3 mm).

## Layout

- **Stackup:** both boards 4 layers, 1.6 mm, 1 oz outer copper. In1 is solid GND, In2 signals.
- **Logic board (top view):**
  - Top side: J1 across the top edge (+24V pins on the right, CAN on the left); J2 on the bottom edge; J5 on the left edge. F1 under J1's +24V pins with D1 below it and F2 beside it; the fan FET, flyback diode, gate resistors, LEDs and their resistors in the middle.
  - Bottom side: U6 and the stack's crystal and decoupling corner (`corner_import.py`); CAN under J1's CAN pins; J6 under J1's right half, clear of the right notch; USB ESD and D3 down the left; C1 under F2; the BOOT pads, thermistor and switch filters right of U6; RESET on the right edge.
- **Power board (top view, top side):** J7 under J6; J3 on the bottom edge; Q2 above J3's HEAT− pins, its gate driver and 12 V rail left of it; the buck in the top-left corner, with the boot capacitor right above U1.
- **Power path** (poured before routing; `tools/layout/stack_logic_pre.py`, `stack_power_pre.py`, with helpers in `pours.py`):
  - Logic board: VIN_RAW from J1 pins 1–2 to F1 on top; +24V from F1, D1 and F2 on top, through 10 vias, to a bottom pour on J6 pins 1–2 and C1; a bottom GND pour on J6's GND pins with 5 vias into the GND plane, which carries the return to J1's GND pins.
  - Power board: a +24V strip from J7 pins 1–2 down the outside of its GND pins and across to J3 pins 3–4; HEAT− from J3 pins 1–2 to Q2's drain; Q2's sources joined, with vias into the GND plane, which J7's through-hole GND pins also reach.
  - As on `can-sh`, `planes_fanout.py` keeps other nets' vias out of the pours, `pour_clear.py` takes Freerouting's crossings back out, and the maze router routes round them.
- **Why 25 × 26 mm:** the logic board sets it. J1's footprint is 21.7 × 12 mm, and J2 and the band between them hold the rest; underneath, U6 with its crystal corner and J6 side by side fill the width. The power board is the same size so the two stack, with room to spare.
- **Routing:** `tools/layout/run_stack.sh logic|power` (Freerouting 1.9.0, then the maze router) from `plan_logic.py` and `plan_power.py`.
- **As routed:**
  - Logic board: 0 DRC errors, 0 unconnected, schematic parity clean; 99 vias and 623 mm of track. The one warning is a dangling track end. From `FR_PASSES=100`, `MAZE_ITER=12`, which left 2 open; 8 more `ripup_loop.sh` passes on its `maze.kicad_pcb` closed them, then run_stack.sh's clean-up steps.
  - Power board: 0 DRC errors, 0 unconnected, no warnings; 63 vias and 182 mm of track. From `FR_PASSES=200`, `MAZE_ITER=12`, routed fully in the run.
  - Each power pour fills in one piece on both boards.
- **Changes on the way:** the heater's PWM moved from PB9 (pin 48, bottom right of U6, boxed in on its way up to J6) to PD0 (38). J2 sits 2.5 mm right of centre so its pads clear the MCU corner's +3V3 vias (the link between VBAT and VDD). R2 and R3 moved away from Q2 to leave room for its GND vias.

## Panel

Both boards go in one panel, in columns of logic/power pairs (`tools/panel_stack.py`), built by `tools/make_panel.sh` (see `gerber/README.md`):

| Panel | Layout | Size | Folders |
| --- | --- | --- | --- |
| 9 pairs | 3 columns of 3 pairs | 93.3 × 184.6 mm | `hardware/panel/`, `gerber/panel/` |
| 6 pairs | 3 columns of 2 pairs | 93.3 × 128.4 mm | `hardware/panel6/`, `gerber/panel6/` |
| 4 pairs | 4 columns of 1 pair | 120.4 × 72.2 mm | `hardware/panel4/`, `gerber/panel4/` |

62 parts per pair: 43 on the logic board (29 on its underside) and 19 on the power board. JP1–JP3 are bare pads. J7 is a through-hole part, which JLCPCB solders as through-hole assembly.

- **Size:** JLCPCB's standard assembly needs a panel of at least 70 × 70 mm; `make_panel.sh` widens the gap to the frame where a side would come to less than 72 mm.
- **Holding the boards:** mouse bites on the side edges, clear of the notches (`tools/panel_tabs.py`): on the logic board at y 2.4 and 10.9, both in its upper half, because J5 and the left notch fill the lower left edge; on the power board at y 2.4 and 19.2. Four tooling holes and three fiducials.

## Bring-up and firmware

1. **First flash over USB:** wire J5 to a USB socket and plug it into the host, with no 24 V. Check 3.3 V. A blank MCU comes up as an STM32 DFU device; if not, short the BOOT pads and tap RESET.
2. **Flash Katapult** (STM32G0B1, 8 MHz crystal, CAN on PB0/PB1, 8 KiB offset), then Klipper over CAN:
   - Klipper `make menuconfig`: STM32G0B1, 8 KiB bootloader, 8 MHz crystal, "CAN bus (on PB0/PB1)", 1000000 (or your bus rate).
   - `python3 ~/katapult/scripts/flashtool.py -i can0 -q` to find the UUID, then `flashtool.py -i can0 -u <uuid> -f out/klipper.bin`.
3. **24 V and CAN:** with the boards stacked, plug in J1 (supply off), then power up. Bridge JP1 if this board ends the bus.

Example config:

```
[mcu tool]
canbus_uuid: 0123456789ab

[extruder]
heater_pin: tool:PD0
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

- [ ] The heater at 100 W for 30 minutes: F1, Q2, J1, J3 and the link's temperatures (the XH and link contacts are the tightest margin, 2.35 A of 3 A).
- [ ] The stack fits together: J7 into J6, the notches lined up, J3's plug clear of the logic board above it.
- [ ] Heater off through reset, during flashing and on USB power alone.
- [ ] CAN at 1 Mbit/s through a long print.
- [ ] The crystal starts reliably (20 pF load with 33 pF caps).
