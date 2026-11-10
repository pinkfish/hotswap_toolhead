# USB Toolhead Board – Design Spec

Nov 10, 2026 (branch `usb-sh`)

## Overview

One 18 × 23.5 mm, 4-layer board, powered and connected by a single USB-C cable. It reads a thermistor and a switch, and drives a 5 V fan. All three share one 6-pin JST-SH plug. It is built around an STM32G0B1 and runs Klipper over USB as a second MCU.

There is no heater output, no 24 V and no CAN: **the heater is wired straight to the printer's mainboard** on its own cable.

This is the two-board 24 V CAN stack (branch `stack`) with the power input, CAN, heater driver, buck and board-to-board link taken out. The parts it shares with the stack's logic board keep their references.

Branch `usb-only` has the first version of this board: 22 × 30 mm with a 2 mm JST-PH plug, two M2.5 holes and a PT1000 header. This branch swaps the PH for a 1 mm JST-SH, drops the holes and turns the PT1000 header into a solder jumper, which takes the board from 660 to 423 mm² (36% smaller).

| Parameter | Target | Why |
| --- | --- | --- |
| Supply | USB VBUS, 4.75–5.25 V | USB-C carries one supply voltage (VBUS, 5 V unless USB-PD negotiates more) plus GND, so 24 V can't come down the USB cable |
| Logic | 3.3 V LDO from VBUS, under 50 mA | No buck needed at 5 V in |
| Fan output | 5 V from VBUS, 0.3 A or less, low-side PWM, flyback-protected | What a USB 2.0 port (0.5 A) can feed beside the logic; 5 V 30–40 mm fans draw 0.1–0.2 A |
| Sensor input | 100k NTC (e.g. 3950) with a 4.7 kΩ pull-up, or PT1000 by solder jumper | As on the stack |
| Switch input | Switch to GND, 10 kΩ pull-up, RC filter | Endstop, probe or filament switch |
| USB | USB 2.0 Full Speed, USB-C receptacle, device mode | Klipper's USB-serial; DFU and Katapult for flashing |

**Why an STM32 and not an ESP32:** mainline Klipper has no ESP32 port. The STM32G0B1 is one of Klipper's best-supported MCUs, and the stack had already routed it.

## Heater on the mainboard

The heater cartridge is wired to a heater output on the mainboard, on its own two-wire cable. The thermistor stays on this board, so in Klipper the heater's `heater_pin` names a mainboard pin and its `sensor_pin` names a pin on this board (`tool:PB12`).

**Not yet checked:** that Klipper runs a heater whose pin and sensor are on different MCUs.

- Klipper's config doesn't forbid it, and the host runs the PID loop. But the heater's safety shutdown (`max_duration` on the heater pin) and the sensor's reporting timing then live on different MCUs.
- If Klipper refuses the config or the heater misbehaves, wire the thermistor to the mainboard as well, and use this board's thermistor input for a chamber or part-cooling sensor.

## Power

1. **VBUS:** from J5 through the USBLC6's VBUS clamp (U5) to C17 (10 µF). The CC pull-downs (R20, R21, 5.1 kΩ) make any USB-C host or charger turn VBUS on. There is no fuse on VBUS: the host port limits its own current, and the fan has its own PTC.
2. **3.3 V LDO (U1):** Microne ME6211C33M5G-N (C82942, SOT-23-5, 500 mA, about 100 mV dropout at 100 mA), with CE tied to VIN and 1 µF in (C4) and out (C8). C10 (10 µF) is the 3.3 V bulk by U6.
3. **Analog reference:** VREF+ (pin 5) and the thermistor pull-up are fed from 3.3 V through FB1 (600 Ω at 100 MHz), with 1 µF + 100 nF (C11, C12) to pin 7. This keeps the reading ratiometric, as on the stack.
4. **Budget:** the logic takes about 40 mA. A 0.3 A fan brings the total to about 0.35 A, inside a USB 2.0 port's 0.5 A. Many mainboard USB-A ports are only rated 0.5 A in total, and a 0.5 A fan would sit right at that limit.

LEDs: yellow-green on 3.3 V (power, R5 1 kΩ) and blue status on PA15 (R6 100 Ω).

## Microcontroller

STM32G0B1CEU6 (C2829190): 512 KB flash, UFQFPN-48 7 × 7 mm, exposed pad to GND.

- **Why the CE:** it has the same pinout and package as the stack's 128 KB CBU6. JLCPCB had 461 of the CEU6 in November 2026 but only 6 of the CBU6.
- **Crystal:** the 8 MHz crystal (Y1, 20 pF load, 2 × 33 pF C0G) is required. Klipper's STM32G0 code clocks USB from the PLL, and the internal oscillator is outside USB's 0.25% tolerance.

| Function | Pin | Notes |
| --- | --- | --- |
| USB D− / D+ | PA11 / PA12 (33 / 34) | Through U5 to J5 |
| Fan PWM | PB13 (25) | R15 1 kΩ to Q3's gate; R16 10 kΩ pull-down holds the fan off through reset |
| Thermistor | PB12 (24) | ADC1_IN16, RC-filtered and clamped |
| Switch | PB8 (47) | R22 10 kΩ pull-up, R23 1 kΩ + C20 100 nF filter |
| Status LED | PA15 (37) | Blue, 100 Ω |
| SWCLK / BOOT0 | PA14 (36) | BOOT pads (JP3) to 3.3 V through R4 (1 kΩ); no SWD header |
| HSE | PF0 / PF1 (8 / 9) | 8 MHz crystal |
| Reset | NRST (10) | C15 100 nF, RESET button (SW1) to GND |

The fan, switch and status LED are on the pins nearest their parts, so their tracks don't cross the board (on `usb-only` they were PA8, PB13 and PB5). Klipper drives a fan and reads a switch on any GPIO; the fan uses software PWM by default.

## Fan output

- **Supply:** the fan runs from VBUS (5 V) through F2. F2 is a 0.5 A hold, 16 V PTC (BSMD1206-050-16V, C883124, 1206). A PTC's hold current drops to about two-thirds at 70 °C, so keep the fan at 0.3 A or less. F2 protects the USB port and the plug if the fan cable shorts.
- **Switch (Q3):** WST6066A, 60 V N-MOSFET in SOT-23, 120 mΩ at 2.5 V gate, driven straight from PB13.
- **Flyback (D5):** DSK110 Schottky across the fan, cathode to FAN+.
- **PWM:** a 2-wire 5 V fan at about 100 Hz–1 kHz (`cycle_time: 0.01` or shorter).

## Sensor inputs

- **Thermistor:** R17 (4.7 kΩ 0.1%, 25 ppm) from VREFP to TH_SIG. Bridging solder jumper JP2 adds R18 (4.12 kΩ 0.1%) in parallel for a PT1000, giving about 2.2 kΩ. TH_SIG then goes through R19 (1 kΩ) and C19 (100 nF) to PB12, and D6 (BAT54S) clamps PB12 to 3.3 V and GND.
- **Thermistor return:** J2 pin 4 goes to the board's GND. No load current flows in this board's ground apart from the fan's 0.3 A, which returns through Q3, so the thermistor doesn't need its own return as it did on the stack.
- **Switch:** J2 pin 5 (SENS) has R22 (10 kΩ) to 3.3 V, then R23 (1 kΩ) and C20 (100 nF) to PB8. The switch closes to J2 pin 6 (GND).

## Connectors

| Ref | Function | Part | Pinout |
| --- | --- | --- | --- |
| J5 | USB | HRO TYPE-C-31-M-12 16-pin USB-C (C165948), on the top edge, plug pointing up | VBUS, D+/D− (both rows tied), CC1/CC2 to GND through 5.1 kΩ, shell to GND |
| J2 | Fan, thermistor, switch | JST SH 1.0 mm 1×6, right-angle SMD, SM06B-SRSS-TB(LF)(SN) (C160405), on the bottom edge, plug pointing down; 1 A per contact, 28–32 AWG. Mating housing SHR-06V-S-B with SSH-003T-P0.2 contacts, or a pre-crimped SH cable | 1 FAN+ (5 V via F2), 2 FAN− (Q3 drain), 3 TH_SIG, 4 thermistor GND, 5 SENS, 6 GND |
| JP2 | PT1000 pull-up | Two solder pads on the bottom, open by default | Bridged: PT1000 |
| JP3 | BOOT | Two solder pads, shorted with tweezers | |
| SW1 | RESET | Panasonic EVQ-P7C01P side-push (C388883), on the right edge | |

**Mounting:** there are no holes. Hold the board in a printed pocket or clip on the toolhead, by its edges; the USB-C shell and the plug take the cable forces through their own pads.

**USB cable:** use a shielded cable that is as short as the toolhead's travel allows. The cable carries the fan current as well as data, so a thin, long cable loses VBUS voltage. The board needs at least about 3.4 V at the LDO input to hold 3.3 V; the fan just slows down a little.

USB in a printer's cable chain is more exposed to noise than CAN, so if Klipper reports `Lost communication with MCU`:
- check the cable and its shield first;
- then the host port.

## Bill of materials

38 placements, 24 BOM lines (`hardware/toolhead_usb-bom-jlcpcb.csv`; `hardware/bom_jlcpcb.csv` is the same). JP2 and JP3 are bare pads.

| Ref | Part | Package | LCSC |
| --- | --- | --- | --- |
| U6 | STM32G0B1CEU6 | UFQFPN-48 | C2829190 |
| U1 | ME6211C33M5G-N 3.3 V LDO | SOT-23-5 | C82942 |
| U5 | USBLC6-2SC6 USB ESD | SOT-23-6 | C7519 |
| Q3 | WST6066A 60 V N-MOSFET | SOT-23 | C148352 |
| D5 | DSK110 100 V 1 A Schottky | SOD-123F | C22466354 |
| D6 | BAT54S | SOT-23 | C7420333 |
| F2 | PTC 0.5 A hold 16 V, BSMD1206-050-16V | 1206 | C883124 |
| Y1 | 8 MHz 20 pF crystal, YXC X32258MSB4SI | 3225 | C2682774 |
| FB1 | 600 Ω at 100 MHz ferrite | 0402 | C76884 |
| J5 | USB-C 16-pin, HRO TYPE-C-31-M-12 | SMD + THT shell | C165948 |
| J2 | JST SM06B-SRSS-TB(LF)(SN) | SMD | C160405 |
| SW1 | EVQ-P7C01P | SMD | C388883 |
| LED1, LED2 | Yellow-green, blue | 0603 | C2289, C2288 |
| R17, R18 | 4.7 kΩ and 4.12 kΩ, 0.1% 25 ppm | 0402 | C281778, C852812 |
| R, C | 100 Ω, 1 kΩ ×5, 5.1 kΩ ×2, 10 kΩ ×2; 33 pF ×2, 100 nF ×5, 1 µF ×3, 10 µF ×2 | 0402, 0805 | JLCPCB basic parts |

## Layout

- **Stackup:** 4 layers, 1.6 mm, 1 oz outer copper. Layers:
  - F.Cu: J5, J2, SW1, the LEDs and their resistors, the fan FET with its gate resistors and flyback diode, the thermistor divider, filter and clamp, and the switch filter.
  - In1: solid GND.
  - In2: signals.
  - B.Cu: U6 and its crystal and decoupling, U5 and C17, U1 with C4, C8 and C10, F2, the CC pull-downs, and the BOOT and PT1000 jumpers.
  - Both outer layers carry a GND pour.
- **Floorplan (top view):**
  - USB-C on the top edge, centred, plug pointing up.
  - The SH plug on the bottom edge, plug pointing down, so the cable leaves straight down. Its hold-down pads are 0.5 mm in from the edge, so the housing overhangs the edge by about 0.7 mm. It sits 0.35 mm right of centre so that its pad row and right hold-down pad clear the MCU corner's vias.
  - The LEDs and their resistors right of the USB-C; RESET on the right edge, between the connectors.
  - U6 in the middle of the bottom side, turned so its USB pins face J5. The stack's hand-laid crystal and decoupling corner is brought across with it (`tools/layout/corner_import.py`). It has to face J2, because U6's USB pins are on the opposite side of the package.
  - Each side follows U6's pins: the fan, thermistor and PT1000 jumper on the left, by PB12/PB13; the status LED, BOOT pads and the switch filter on the right, by PA15, PA14 and PB8.
- **Why 18 × 23.5 mm:** 16 × 22 placed but left 12–16 connections open; 17 × 22 to 17 × 24 left 1–10. Two things set the final size. The side columns beside U6's pins must take a SOT-23 (4.4 mm at 18 mm wide). And the right column has to fit C17, the BOOT pads and their resistor above RESET's peg holes, with the +3V3 pad facing U6 so it can be reached.
- **USB pair** (`tools/layout/usb_pair_pre.py`, locked before routing): J5's pad row is right over U6's USB pins, and the two parts' pin orders cross.
  - D+ is strapped above J5's pad row and D− below it, each to a via in its U5 pin.
  - D− runs straight down to U6 pin 33 on the bottom layer.
  - D+ crosses over D−'s via on In2 to a second via, then comes down to pin 34 beside D−.
  - U5's GND pin, boxed in by the pair, has its own via.
  - J5's right-hand VBUS pad (A4/B9) and CC1 (A5) are boxed in too. Both leave along under the pad row on the top layer. VBUS goes to a via right of J5's shell leg and on to C17; CC1 runs below it to a via further right, which leaves the strip right of J5 for the LEDs. The script shifts these coordinates with the board's centre line.
- **Routing:** placed by `tools/layout/plan_usb.py` and routed by `tools/layout/run_usb.sh`: Freerouting 1.9.0, then a scripted maze router.
- **As routed:** 0 DRC errors, 0 unconnected, schematic parity clean; 62 vias and 456 mm of track. The only warnings are J5's silkscreen at the board edge. The committed board is one of two runs side by side that both routed fully (`FR_PASSES=200`, `MAZE_ITER=3`, `SOFT_ITERS=0`; the other used 100 passes).

## Panel

Order the board as a panel of 9, 6 or 4 built by `tools/make_panel.sh` (see `gerber/README.md`):

| Panel | Grid | Size | Folders |
| --- | --- | --- | --- |
| 9 | 3 × 3 | 72.3 × 92.8 mm | `hardware/panel/`, `gerber/panel/` |
| 6 | 3 columns × 2 rows | 72.3 × 72.0 mm | `hardware/panel6/`, `gerber/panel6/` |
| 4 | 2 × 2 | 72.0 × 72.0 mm | `hardware/panel4/`, `gerber/panel4/` |

- **Size:** JLCPCB's standard assembly needs a panel of at least 70 × 70 mm. Where the boards and the 5 mm frame come to less than 72 mm on a side, the gap between the boards and the frame is widened.
- **Holding the boards:** mouse bites on the side edges (`tools/panel_tabs.py`), four tooling holes and three fiducials.
- **After every layout change:** rebuild all three panels.

## Bring-up and firmware

1. **Plug in USB:** check 3.3 V. A blank MCU enumerates as an STM32 DFU device by itself. If it doesn't, short the BOOT pads and tap RESET.
2. **Build Klipper** (`make menuconfig`):
   - STM32G0B1, 8 MHz crystal.
   - Communication: USB (on PA11/PA12).
   - Bootloader offset: "No bootloader" when flashing over DFU, or 8 KiB with Katapult.
3. **Flash it:** `make flash FLASH_DEVICE=0483:df11`.
4. **Find the port:** `ls /dev/serial/by-id/`.

Example config. Replace the serial path, and set `heater_pin` to the mainboard's heater output:

```
[mcu tool]
serial: /dev/serial/by-id/usb-Klipper_stm32g0b1xx_0123456789ABCDEF-if00

[extruder]
heater_pin: PA2                    # the mainboard's heater output
sensor_type: Generic 3950
sensor_pin: tool:PB12
pullup_resistor: 4700
# ... step_pin, dir_pin etc. as before

[heater_fan hotend_fan]
pin: tool:PB13
cycle_time: 0.01
heater: extruder
heater_temp: 50.0

[output_pin status_led]
pin: tool:PA15

[temperature_sensor tool_mcu]
sensor_type: temperature_mcu
sensor_mcu: tool

[filament_switch_sensor tool_switch]
switch_pin: !tool:PB8
pause_on_runout: True
```

Notes on the config:

- **Pull-up:** PB8 has its own pull-up (R22), so it needs no `^`. The switch closes to GND, and `!` makes a closed switch read as filament present. As an endstop, use `endstop_pin: !tool:PB8` instead.
- **PT1000:** bridge JP2 with solder and set `sensor_type: PT1000` and `pullup_resistor: 2200`.
- **Order:** run `PID_CALIBRATE` after the first heat-up, with the fan running.

**Prototype checks:**

- [ ] Klipper accepts a heater on the mainboard with its sensor on this board, and the heater holds temperature and trips `verify_heater` when the thermistor is unplugged.
- [ ] USB stays connected through a long print with the fan running (cable and EMI).
- [ ] The crystal starts reliably (20 pF load with 33 pF caps; ST AN2867).
