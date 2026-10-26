# 24V CAN Heater/Fan Controller PCB – Design Spec

Oct 23, 2026

## Overview and assumptions

A 31 × 42 mm, 4-layer board (connectors, buttons and LEDs on the top side, everything else on the bottom, like the FYSETC H36 and Mellow Tool-Lite) with two M3 heat-set-insert mounting holes that takes 24 V and CAN on one connector and drives one heater, one fan, one temperature sensor and one switch input (fan, thermistor and switch share one 2×3 Nano-Fit plug), with a USB-C port for flashing and debugging. It is built around an STM32G0B1 so it runs Klipper (with Katapult bootloader) out of the box, like common 3D-printer toolhead boards.

Design targets, chosen where the request left them open:

| Parameter | Target | Why |
| --- | --- | --- |
| Supply | 24 V nominal, 12–30 V operating | Standard printer/CNC rail; 12 V works with a lower-power heater |
| Heater output | 24 V, 3 A continuous (72 W), low-side PWM | Sized for a 60–72 W cartridge (2.5–3 A) |
| Fan output | 24 V, up to 0.5 A, low-side PWM, flyback-protected | Covers 2-wire 30–50 mm fans and small blowers |
| Sensor input | 100k NTC thermistor (e.g. 3950), 4.7 kΩ pull-up | Most common hotend sensor; PT1000 option by jumper |
| CAN | Classic CAN, 500 kbit/s or 1 Mbit/s, switchable 120 Ω termination | Klipper default rates |
| USB | USB 2.0 Full Speed on a USB-C receptacle, device mode; powers all logic on its own for programming, no 24 V needed | Flashing (DFU), USB-serial debug, or USB-only operation |
| Board fuse | 6 A on the 24 V input | Protects the harness if the heater FET fails short |

The heater output is safe-by-default: the FET gate is held off by pull-downs during reset, boot and firmware crashes.

## System architecture

![Schematic overview](schematic_overview.png)

The 24 V rail goes straight to the heater and fan through the protection stage; logic runs from a single 3.3 V buck that USB VBUS can also feed for bench flashing, and the MCU drives the heater and fan FETs directly.

## Power input and regulation

24 V enters through a fuse, a TVS and a reverse-polarity P-FET to become the load rail for the heater and fan. One buck makes 3.3 V for all logic; there is no 5 V rail and no separate gate-drive supply.

1. **Fuse (F1):** 6 A 1206 one-time SMD fuse (BSMD1206C-1600T, rated to 63 V DC), the largest 1206 fuse JLCPCB stocks. A 72 W heater plus fan draws about 3.6 A, which would run a 5 A fuse near its derating limit in a warm toolhead. Even after a fuse's typical 20–25% derating at 70 °C, 6 A stays above the 3.6 A load.
2. **TVS (D1):** SMAJ33CA (bidirectional, SMA) from +24V to GND at the input. Clamps hot-plug and supply spikes below the 60 V rating of Q1, the output FETs and the buck. Because it's bidirectional it stays off with a reversed supply, so Q1 handles reverse polarity without blowing the fuse. Its 33 V standoff keeps it quiet with the supply set anywhere from 24 to 30 V.
3. **Reverse polarity (Q1):** P-channel MOSFET, ≥60 V / ≥8 A, low R_DS(on) (e.g. SQJ461EP or similar), source to load, drain to input. Gate to GND through 10 kΩ, with a 12 V Zener (D2) gate–source to protect V_GS.
4. **Bulk capacitance:** 1 × 47 µF / 50 V aluminium electrolytic, 105 °C (Lelon RVT1H470M0607, 2000 h at 105 °C, roughly 20 000 h at 70 °C; no 6.3 × 7.7 mm part rated ≥5000 h is stocked) (not polymer: its higher internal resistance damps hot-plug ringing) plus 2 × 10 µF / 50 V X5R ceramic (JLCPCB basic; about 3 µF each at 24 V after DC-bias derating) on the 24 V rail, close to the heater and fan FETs.
5. **Logic input OR (D7, D3):** +24V → D7 → VIN_LOGIC, and USB VBUS → D3 → VIN_LOGIC, both 100 V 1 A Schottkys in SOD-123F (the Tool-Lite uses SOD-123 here too). The board can be programmed from USB alone, and the diodes stop 24 V reaching the USB host and VBUS reaching the heater rail.
6. **24 V → 3.3 V buck (U1):** TI LMR16006XDDC (4–60 V in, 600 mA, 0.7 MHz, SOT-23-6), so it survives anything the TVS lets through. It is non-synchronous, so it needs a catch diode (D9, DSK110 100 V 1 A Schottky, SOD-123FL) from SW to GND. The Tool-Lite's synchronous SY8303 would drop this diode, but it is only rated to 40 V. L1 is 22 µH (FNR4030S220MT, 4 × 4 mm, 1.2 A rated, so it survives the 1.2 A typical switch current limit), giving about 0.19 A ripple at 30 V in; C8 is 22 µF. Feedback is R2 = 33 kΩ over R3 = 10 kΩ: V_OUT = 0.765 V × (1 + 33/10) = 3.29 V. SHDN is tied straight to VIN, within its 65 V absolute maximum; TI suggests a 100 kΩ series resistor for that, worth adding on a future revision. Its 4 V minimum input lets it run from VBUS through D3 (about 4.6 V). Total 3.3 V load is under 100 mA.
7. **Analog supply:** in the STM32G0B1's 48-pin packages (LQFP-48 and UFQFPN-48 share the pinout), VDDA is bonded to VDD on one pin (pin 6, VDD/VDDA) and VSSA to VSS (pin 7), but the ADC reference VREF+ is its own pin (pin 5). Feed VREF+ and the thermistor pull-up together from 3.3 V through FB1 (600 Ω @ 100 MHz), with 1 µF + 100 nF from VREF+ to pin 7, so the reading stays ratiometric. Leave the internal VREFBUF disabled (its default), since VREF+ is driven externally.

LEDs: yellow-green on 3.3 V (power good, 1 kΩ, about 1.2 mA) and blue status on PB5 (100 Ω, a few mA). Emerald-green and blue LEDs need about 2.8–3.1 V, which would barely light from 3.3 V through 1 kΩ, so the power LED is yellow-green (about 2.1 V). There's no heater-on LED; Klipper reports the heater state.

## CAN bus interface

A 3.3 V CAN transceiver with ±58 V bus fault protection connects the MCU's FDCAN2 peripheral to the bus.

- **Transceiver (U3):** TI TCAN3414DR (SO-8, 3.0–3.6 V supply) with 100 nF. Its ±58 V bus fault protection on CAN_H/CAN_L means a 24 V short from the neighbouring XT30 power pins doesn't destroy it. STB (pin 8) is tied straight to GND for normal mode. Pin 5 is SHDN (high = shutdown, internal pull-down), so it is left open and R12 must never be fitted. The MAX33012E considered earlier needs a 4.5–5.5 V supply, which this board doesn't have. Avoid the SN65HVD230 and TCAN330, whose bus pins only tolerate about ±12–16 V.
- **MCU pins:** TXD → PB1 (FDCAN2_TX), RXD → PB0 (FDCAN2_RX). This matches the Klipper/Katapult option "CAN bus (on PB0/PB1)".
- **Termination (R_T, JP1):** 120 Ω, 0805, in series with a solder jumper across CAN_H/CAN_L. Bridge it only on the board at the end of the bus.
- **ESD (D4):** NUP2105L or PESD2CAN (SOT-23) on CAN_H/CAN_L to GND, placed at the connector.
- **Optional common-mode choke (L2):** 51 µH CAN choke (e.g. ACT45B-510-2P) with 0 Ω bypass footprints. Leave it bypassed unless EMC testing calls for it.
- **Routing:** CAN_H/CAN_L as a tightly coupled pair, 120 Ω differential where practical, no stubs longer than ~10 mm between connector, ESD, termination and transceiver.

Crystal: an 8 MHz HSE crystal (±20 ppm or better) on PF0/PF1 is required for reliable 1 Mbit/s CAN timing; the internal oscillator is not accurate enough.

## Microcontroller and pin assignment

The MCU is an STM32G0B1CB in the 105 °C temperature grade (order code ending T7, or T3 for 125 °C, if stocked; the common CBT6 is only rated to 85 °C ambient): a Cortex-M0+ at 64 MHz with 128 KB flash in UFQFPN-48 (7 × 7 mm; exposed pad to GND with a 3 × 3 via grid), chosen because it has both FD-CAN and crystal-less USB and is fully supported by Klipper and Katapult.

| Function | MCU pin | Peripheral | Notes |
| --- | --- | --- | --- |
| CAN RX | PB0 | FDCAN2_RX | To transceiver RXD |
| CAN TX | PB1 | FDCAN2_TX | To transceiver TXD |
| USB D− | PA11 | USB_DM | Via USBLC6 to J5 |
| USB D+ | PA12 | USB_DP | Via USBLC6 to J5 |
| Heater PWM | PB13 | GPIO / TIM1_CH1N | To Q2 gate via 10 kΩ; 10 kΩ pull-down at the pin |
| Fan PWM | PB8 | TIM16_CH1 | To Q3 gate via 1 kΩ; 10 kΩ pull-down at the pin |
| Thermistor | PA3 | ADC1_IN3 | RC-filtered, clamped |
| Switch sensor | PA2 | GPIO | 10 kΩ pull-up to 3.3 V, 1 kΩ + 100 nF filter; switch closes to GND |
| Status LED | PB5 | GPIO | Blue LED, 1 kΩ to GND |
| SWDIO | PA13 | SWD | Not broken out (no SWD header) |
| SWCLK / BOOT0 | PA14 | SWD / BOOT0 | BOOT button (SW2) to 3.3 V through 1 kΩ |
| HSE | PF0 / PF1 | OSC_IN / OSC_OUT | 8 MHz, 20 pF-load crystal with 2 × 33 pF C0G load caps (adjust for board stray capacitance; check oscillator gain margin per ST AN2867) |
| Reset | NRST | — | 100 nF to GND, RESET button (SW1) to GND |

Decoupling: 100 nF on the single VDD/VDDA pin plus one 10 µF bulk on the 3.3 V rail near the MCU. Unused pins are left as test pads where space allows (PA0, PA1, PB3, PB4 are useful for a future endstop or fan tach). Fan PWM and the switch input sit on PB8 and PA2 rather than PA0/PA1 so that the pin 4–10 side of the package stays free for the crystal and decoupling.

## Heater control output

The heater is switched low-side by a 60 V N-MOSFET driven straight from an MCU pin. The FET is chosen to be fully on at the MCU's 3.3 V, so no gate driver is needed.

- **Heater FET (Q2):** 60 V N-MOSFET with R_DS(on) ≤ 30 mΩ specified at V_GS = 2.5 V (50 mΩ absolute maximum), ideally rated for 175 °C junction, in a 3 × 3 mm DFN or PowerPAK 1212-8 package. Pick it from a distributor's parametric search with those filters; the choice is narrower than at 40 V, and the 2.5 V rating is the one that matters. On-resistance rises about 50% as the FET heats up inside a warm printer, so at 3 A a 30 mΩ part dissipates about 0.4 W and a 50 mΩ part about 0.7 W. See Thermal for what that means and the copper it needs.
- **Gate network:** 10 kΩ series resistor from PB13 to the gate, and a 10 kΩ pull-down from PB13 to GND on the MCU side of it. The pull-down holds the heater off while the MCU is in reset or unprogrammed; putting it on the MCU side means the gate still sees the full 3.3 V rather than a divided voltage. The 10 kΩ series resistor also limits the current into PB13 to a safe level if the FET ever fails with its gate shorted to 24 V. Switching takes about 10–20 µs, which is negligible at heater PWM rates.
- **Output:** heater connects between +24V (fused) and the FET drain.
- **Firmware safety:** Klipper's `max_power`, `verify_heater` and thermal-runaway checks are the primary protection. For an unattended machine, add a thermal fuse in the heater block itself.

PWM frequency: Klipper defaults to slow software PWM (~10 Hz) for heaters, which keeps switching losses negligible.

## Fan control output

The fan uses the same direct-drive low-side topology as the heater, with a flyback diode because a fan motor is inductive.

- **Fan FET (Q3):** 60 V logic-level N-MOSFET in SOT-23 (≥ 1.5 A, fully on at 2.5 V gate). The Tool-Lite uses a 30 V AO3400 here; 60 V keeps the margin over the TVS clamp.
- **Gate network:** 1 kΩ series resistor from PB8, with a 10 kΩ pull-down from PB8 to GND on the MCU side. The fan keeps the smaller series resistor because it switches at up to 1 kHz.
- **Flyback diode (D5):** DSK110 100 V 1 A Schottky (SOD-123FL, the same part as D3, D7 and D9) across the fan terminals, cathode to +24V.
- **Snubber cap (C):** optional 100 nF / 50 V across the output footprint, unpopulated by default.
- **PWM:** hardware PWM on PB8 (TIM16_CH1). Use a low frequency (about 100 Hz–1 kHz) for 2-wire fans to avoid whine and stalling. 25 kHz only applies to 4-wire fans with their own PWM input, and it would also cause noticeable switching loss with the 1 kΩ gate resistor.

The fan shares J3, a 2×3 Nano-Fit, so keep the fan at 0.5 A or less. A resettable PTC fuse (F2: 0.75 A hold at 25 °C, rated ≥30 V, 1812; a PTC's hold current drops to roughly two-thirds at 70 °C, so this size still carries a 0.5 A fan in a hot chamber without nuisance trips) in the fan's +24V line protects the connector and traces if the fan cable shorts, since the 6 A main fuse would never blow in time. If you later want tach feedback, PA0 is free and can be broken out to a third pin with a 10 kΩ pull-up to 3.3 V.

## Sensor input

The sensor input is a ratiometric thermistor divider on ADC pin PA3, filtered and clamped so a heater-to-sensor short cannot destroy the MCU.

- **Pull-up:** 4.7 kΩ 0.1% (25 ppm/°C) from the ADC reference rail (see Power, analog supply) to the sensor pin. This is Klipper's default `pullup_resistor` for 100k NTCs.
- **PT1000 option (JP2):** a 2-pin 2.0 mm jumper header (as on the Tool-Lite) puts a 4.12 kΩ 0.1% resistor in parallel with the 4.7 kΩ: no shunt = 4.7 kΩ (100k NTC), shunt fitted ≈ 2.2 kΩ (PT1000). Place the header right beside the pull-up resistors so the extra trace stays short and away from the heater and fan. Set `pullup_resistor` in firmware to match.
- **Filter:** 1 kΩ series resistor into PA3, then 100 nF X7R to AGND at the pin. Time constant ≈ 0.1 ms, far faster than thermal changes, and it gives the ADC a low-impedance source.
- **Protection:** BAT54S dual Schottky on PA3 (to 3.3 V and to GND) after the 1 kΩ, so a 24 V fault is limited to about 22 mA into the clamp.
- **Ground:** the sensor return goes to AGND, joined to GND at a single point near the MCU's VSS/VSSA pin (pin 7; VSSA is bonded to VSS in this package).

Only one sensor-type assumption matters here: if you plan to use a thermocouple or a PT100, this circuit is not suitable and needs a dedicated front end (MAX31856 or MAX31865 over SPI).

## USB debug header

Debugging uses a USB-C receptacle (USB 2.0 Full Speed) for flashing and serial logs. There is no SWD header; USB DFU and Katapult cover flashing and recovery. The USB-C receptacle is about 3.2 mm tall; nothing else on the board is over 3 mm.

- **USB-C (J5):** HRO TYPE-C-31-M-12 16-pin receptacle (LCSC C165948). Both D+ pins and both D− pins are tied together so the plug works either way up; SBU is unused; shell to GND. Any USB-C cable works.
- **CC (R20, R21):** 5.1 kΩ from CC1 and CC2 to GND, so a USB-C host or charger recognises a device and turns VBUS on.
- **ESD (U5):** USBLC6-2SC6 on D+/D−/VBUS, right at the header.
- **Data lines:** D+ → PA12, D− → PA11, routed as a 90 Ω differential pair and kept short.
- **VBUS:** to VIN_LOGIC through D3 (see Power), plus 10 µF. 
- **BOOT and RESET:** two side-push right-angle tactile switches (SW1 RESET, SW2 BOOT, about 3.5 × 3 mm each) on the right edge next to J5, reachable with the board mounted. Hold BOOT and tap RESET to enter the ROM DFU bootloader. On the STM32G0 the BOOT0 pin is only read when the nBOOT_SEL option bit is cleared, so set nBOOT_SEL = 0 over USB DFU (STM32CubeProgrammer, Option Bytes tab) during first programming, before flashing Katapult. A blank chip enters DFU regardless, and once Katapult is in, double-tapping RESET enters Katapult even if the BOOT button is ignored.

What USB gives you: DFU flashing, Katapult flashing, Klipper's USB-serial mode for bench testing without a CAN adapter, and USB-to-CAN bridge mode if this board should ever be the CAN master. Bench note: with USB connected to a PC and 24 V connected at the same time, the PC and printer grounds are tied through the USB cable. If CAN errors appear while debugging, use a laptop on battery or an isolated USB adapter.

## Connectors and pinouts

Power and CAN come in on one Amass XT30(2+2) hybrid connector: two heavy power contacts for 24 V and GND plus two small signal contacts for CAN_H and CAN_L. The heater keeps a Nano-Fit for current, fan, thermistor and a switch sensor share one latching 2×3 right-angle Nano-Fit (same terminals as the heater plug), and USB is USB-C. Power/CAN and USB sit on the top edge; the heater and the 2×3 sit on the bottom edge with their plugs pointing down, overhanging the edge by about 3 mm.

| Ref | Function | Connector | Pin 1 | Pin 2 | Pin 3 | Pin 4 |
| --- | --- | --- | --- | --- | --- | --- |
| J1 | 24 V + CAN in | Amass XT30PW(2+2)-M, right-angle (power pins ≈15 A, signal pins for CAN) | +24V (power) | GND (power) | CAN_H (signal) | CAN_L (signal) |
| J2 | Heater | Molex Nano-Fit 2.5 mm, 1×2, right-angle | +24V (fused) | HEATER− (FET drain) | — | — |
| J3 | Fan / thermistor / switch | Molex Nano-Fit 2.5 mm, 2×3, right-angle (105314-xx06), latching | +24V via F2 (PTC) | FAN− (FET drain) | TH_SIG | GND (thermistor return); 5 SENS; 6 GND |
| J5 | USB | USB-C 16-pin (USB 2.0) | VBUS | D− | D+ | GND, CC1/CC2 via 5.1 kΩ |
| JP1 | CAN termination | Solder jumper (2-pad) | — | — | — | — |
| JP2 | PT1000 pull-up | 2-pin 2.0 mm header + shunt | — | — | — | — |

The XT30 housing keys the power polarity, but which small pin carries CAN_H and which carries CAN_L varies between BTT and Voron-style boards and even between revisions, so there's no single cable to copy. Instead, the two signal pins pass through a CAN swap block of four 0402 0 Ω footprints: fit the straight pair by default (S1 = CAN_H, S2 = CAN_L), or the crossed pair if your cable is wired the other way. A reversed pair doesn't damage anything; the board just won't appear on the bus until it's swapped. Check your cable against the controller-end silkscreen before the first power-up. Keep the fan at 0.5 A or less (F2 trips above that). Nano-Fit housings are rated to +105 °C, but USB-C and other plastics are typically rated to about +85 °C including contact heating, so mount the board where the chamber air stays below that, away from the heater block's radiant heat.

## Bill of materials

About 60 placements and 7 resistor values. Part numbers are suggestions: check stock, footprints and current datasheets before ordering. The machine-readable BOM is `hardware/bom_jlcpcb.csv`.

| Ref | Part | Package | Qty | Notes |
| --- | --- | --- | --- | --- |
| U1 | TI LMR16006XDDC 60 V buck, set to 3.3 V (C87080) | SOT-23-6 | 1 | 4–60 V in; D9 catch diode |
| U3 | TI TCAN3414DR 3.3 V CAN FD transceiver, ±58 V bus fault (C22396693) | SO-8 | 1 | Pin 5 SHDN left open; R12 never fitted |
| U5 | ST USBLC6-2SC6 USB ESD (C7519) | SOT-23-6 | 1 | |
| U6 | STM32G0B1CBU6 MCU (C5270156; UFQFPN-48 is 85 °C, no 105 °C grade stocked) | UFQFPN-48 7 × 7 | 1 | JLCPCB had only 18 in stock in October 2026 |
| Q1 | Vishay SQJ461EP-T1_GE3 60 V P-MOSFET (C3279500) | PowerPAK SO-8 | 1 | Reverse polarity |
| Q2 | 60 V N-MOSFET, ≤30 mΩ at V_GS = 2.5 V (50 mΩ max) | 3 × 3 mm DFN | 1 | Heater; driven directly by the MCU |
| Q3 | Winsok WST6066A 60 V N-MOSFET, 120 mΩ at 2.5 V, 2.1 A (C148352) | SOT-23 | 1 | Fan |
| Y1 | 8 MHz crystal, ±20 ppm, 20 pF load (YXC X322508MSB4SI) | 3225 4-pin | 1 | JLCPCB C9002; 2 × 33 pF C0G 0402 load caps |
| F1 | 6 A one-time fuse, BSMD1206C-1600T (C49328461) | 1206 | 1 | Main 24 V input |
| F2 | PTC 0.75 A hold, 33 V, JK-mSMD075-33 (C369169) | 1812 | 1 | Fan +24V |
| D1 | SMAJ33CA bidirectional TVS (C19077549) | SMA | 1 | Stays off with a reversed supply |
| D2 | MMSZ5242B 12 V Zener (C19077426) | SOD-123 | 1 | Q1 gate clamp |
| D3, D5, D7, D9 | DSK110 Schottky 100 V 1 A (C22466354) | SOD-123FL | 4 | USB OR, 24 V OR, fan flyback, buck catch diode |
| D4 | onsemi NUP2105LT1G CAN ESD (C14486) | SOT-23 | 1 | |
| D6 | BAT54S dual Schottky (C7420333) | SOT-23 | 1 | Sensor clamp |
| LED1, LED2 | KT-0603YG yellow-green (C2289), KT-0603B blue (C2288) | 0603 | 2 | 3V3 power, status |
| FB1 | Murata BLM15AG601SN1D, 600 Ω @ 100 MHz (C76884) | 0402 | 1 | Feeds VREF+ (pin 5) and the thermistor pull-up |
| SW1, SW2 | Panasonic EVQ-P7C01K side-push switch (C528965) | 3.5 × 2.9 mm SMD | 2 | RESET, BOOT; only 4 were stocked in October 2026 |
| R | 0 Ω | 0402 | 2 | CAN swap (2 of 4 footprints fitted) |
| R | 120 Ω | 0805 | 1 | CAN termination |
| R | 1 kΩ | 0402 | 4 | Fan gate series, sensor filter, BOOT, power LED |
| R | 100 Ω (C25076) | 0402 | 1 | Status LED |
| R | 4.12 kΩ 0.1% 25 ppm, Yageo RT0402BRD074K12L (C852812) | 0402 | 1 | PT1000 option, switched by JP2 |
| R | 4.7 kΩ 0.1% 25 ppm, Yageo RT0402BRD074K7L (C281778) | 0402 | 1 | Thermistor pull-up |
| R | 10 kΩ | 0402 | 5 | Heater gate series, pin pull-downs ×2, Q1 gate, buck FB bottom |
| R | 33 kΩ 1% (C25779) | 0402 | 1 | Buck FB top (R2) |
| C | 47 µF 50 V aluminium electrolytic, 105 °C, Lelon RVT1H470M0607 (C72523) | 6.3 × 7.7 mm SMD | 1 | 24 V bulk; not polymer |
| C | 10 µF 50 V X5R (JLCPCB basic C13585) | 1206 | 2 | 24 V ceramic |
| C | 22 µF 25 V X5R 1206, 10 µF 25 V X5R 0805, 1 µF 10 V X5R 0402, 100 nF 16 V X7R 0402 (50 V 0603 for C5, C18), 33 pF C0G 0402 | 0402–1206 | ~13 | JLCPCB basic: C12891, C15850, C52923, C1525, C14663 |
| J1 | Amass XT30PW(2+2)-M.G.B | Through-hole, right-angle | 1 | 24 V + CAN; LCSC C19268030; footprint from SnapEDA in the project library |
| J2 | Molex Nano-Fit 105313-1102, 1×2 right-angle (C564339) | Through-hole | 1 | Heater |
| J3 | Molex Nano-Fit 105314-1106, 2×3 right-angle (C586245) | Through-hole | 1 | Fan, thermistor, switch sensor |
| J5 | USB-C 16-pin, HRO TYPE-C-31-M-12 (C165948) | 0.5 mm | 1 | USB |
| R20, R21 | 5.1 kΩ (C25905) | 0402 | 2 | USB-C CC pull-downs |
| R22, R23, C20 | 10 kΩ, 1 kΩ, 100 nF | 0402 | 3 | Switch sensor pull-up and filter |
| JP2 | 2-pin 2.0 mm header PZ200V-11-02P (C541856) + shunt | Through-hole | 1 | NTC / PT1000 select |

**JLCPCB sourcing.** JLCPCB charges a feeder fee for every "extended" part type, so the design uses JLCPCB basic parts wherever one meets the spec. LCSC numbers were checked against JLCPCB's basic/preferred parts list in October 2026; confirm stock when ordering.

| Function | JLCPCB basic part | LCSC # |
| --- | --- | --- |
| 100 nF decoupling | 16 V X7R 0402 (C1525); the two 50 V spots (C5, C18) stay 0603 (C14663) |
| CAN termination | Uni-Royal 120 Ω 1% 0805 | C17437 |
| 8 MHz crystal | YXC X322508MSB4SI, 3225, 20 pF load | C9002 |
| 33 pF load caps | 50 V C0G 0402 | C1562 |
| Buck FB top | 33 kΩ 1% 0402 | C25779 |
| Status LED resistor | 100 Ω 1% 0402 | C25076 |
| 1–22 µF ceramics | X5R: 1 µF 10 V 0402, 10 µF 25 V, 10 µF 50 V, 22 µF 25 V | C52923, C15850, C13585, C12891 |

These parts stay extended because no basic part meets the spec: the MCU (no basic STM32 has both FD-CAN and a USB bootloader), the 60 V buck, the ±58 V CAN transceiver, the ferrite bead (basic ones are 0603), the LEDs, the diodes, the 60 V 2.5 V-rated FETs, the reverse-polarity FET, both fuses, the TVS, the 0.1% thermistor resistors and all connectors. The crystal and X5R ceramics are rated to 85 °C, which leaves about 35 °C of margin at the expected 50 °C ambient.

## PCB layout guidance

Target a 31 × 42 mm, 4-layer, 1.6 mm board with 1 oz copper. Stackup: top (connectors, GND pour), In1 solid GND, In2 solid +24V, bottom (all ICs and passives, GND pour). Every SMD GND and +24V pad gets its own via to its plane; +3.3 V is routed as traces. The +24V plane carries the 3.6 A input current, which 1 oz traces of a routable width cannot.

**Floorplan (top view):** connectors, buttons, LEDs, the bulk electrolytic and JP2 on the top side; everything else on the bottom.

- **Mounting holes:** two M3 holes for 5 mm heat-set inserts, each with a 4 mm-radius keep-out (insert + 1.5 mm) on both sides: H1 on the left edge 3.5 mm in and 20.5 mm down from the top; H2 at the bottom edge between J2 and J3, 4.5 mm up from the bottom edge.
- **Top end:** J1 (XT30 2+2, right-angle, mouth up, front about 2.8 mm past the edge) and J5 (USB-C, shell flush). Q1, F1 and D1 sit underneath between J1's pins; U3 (CAN) behind J1's signal pins; U5 and the CC resistors between J5's shield pins.
- **Right edge:** SW1 (RESET) and SW2 (BOOT), side-push.
- **Bottom end:** J2 (heater Nano-Fit 1×2) and J3 (fan/thermistor/switch Nano-Fit 2×3), right-angle, pointing down and about 2.3 mm past the edge (the locating pegs stay 0.5 mm inside it). Q2 sits under J2; Q3, D5 and F2 near J3.
- **Centre (bottom side):** U6 with its decoupling, VREF and crystal parts on the pin 4–10 side; the buck below and to the right of the MCU, away from the thermistor filter.
- **Thermistor:** RC filter and clamp close to PA3, away from the heater traces; run TH_SIG from J3 away from FAN_N.

**Current and copper:**

- Heater path (J1 → F1 → Q1 → J2, and J2 → Q2 → GND): pours at least 3 mm wide on 1 oz, for 3 A at ≤ 10 °C rise. Stitch the FET source pads to the ground plane with 6+ vias (0.3 mm drill).
- Give Q2's drain pad at least 150 mm² of top copper with 9+ thermal vias to a matching bottom pour, and keep Q2 at least 5 mm from the MCU and crystal. Q3 needs about 50 mm².
- Keep the buck converter's switch node small and on the top layer, with its input cap, IC and ground return in a tight loop.

**Signal integrity:**

- CAN_H/CAN_L and USB D+/D− as coupled pairs over unbroken ground; no vias if avoidable.
- AGND: a small island under the thermistor filter and VSSA, joined to GND at one point near the MCU.
- Keep the thermistor trace at least 2 mm from heater and fan switching nodes.

**Fab:** standard JLCPCB/PCBWay rules work (0.15 mm trace/space, 0.3 mm vias). Add test points for +24V, +3V3, GND, CAN_H, CAN_L and TH_SIG.

**As routed (rev A), where it differs from the guidance above:**

- **Q2 drain:** 81 mm² of HEAT_N copper (top and bottom pours) with 17 thermal vias, not 150 mm²; the J2/Q2 corner of a 31 mm board has no more room. Expect Q2 to run hotter than the Thermal section assumes; check it at full heater power.
- **FET source vias:** Q1 drains into the +24V plane through 5 vias and a bottom pour; Q2's source reaches the GND plane through 4 vias plus the bottom GND pour, not 6+.
- **Heater path:** the input runs J1 → F1 → Q1 through bottom-layer VIN_RAW/VIN_F pours, and the load current through the In2 +24V plane, rather than 3 mm traces.
- **Buck switch node:** on the bottom layer, since all ICs are on the bottom.
- **AGND:** not split; the thermistor filter returns to the solid In1 GND plane.
- **USB and CAN pairs:** USB D+/D− change layers (three vias each) to cross the USB-C's interleaved pins and reach U6. CAN also uses vias.
- **Test points:** none fitted.

## Thermal

The expected air temperature around the board is about 50 °C. The design is checked at a 70 °C worst case: an enclosed chamber at 60 °C plus local heat near the toolhead. Every part is rated for that, and the heater FET is the only part that runs meaningfully warm.

Estimated temperatures at full heater power (72 W, 3 A, 24 V) and 70 °C ambient:

| Part | Dissipation | Estimated temperature | Rating |
| --- | --- | --- | --- |
| Q2 heater FET, 30 mΩ part | ~0.4 W | ~100 °C junction | 150–175 °C |
| Q2 heater FET, 50 mΩ part | ~0.7 W | ~120 °C junction | 150–175 °C |
| Q1 reverse-polarity FET | ~0.4 W | ~90 °C junction | 150 °C |
| F1 fuse | ~0.15 W | ~75 °C | Derated, still above load |
| U1 buck | <0.1 W | ~75 °C | 125 °C |
| MCU, transceiver, fan FET, diodes | <0.05 W each | ~72 °C | 105 °C or higher |
| Bulk capacitor | Ripple only | ~72 °C | 105 °C long-life |

These are estimates from typical thermal resistances (about 70 °C/W for a 3 × 3 mm FET on 150 mm² of copper per side), so measure Q2's case temperature with a thermocouple during a long print on the first prototype. Temperature-sensitive choices made for this environment: the MCU's 105 °C grade (the common CBT6 is only rated to 85 °C), a 105 °C long-life electrolytic (an 85 °C part would last under a year of continuous running at 70 °C), and a fan PTC sized for its hold current at temperature. The crystal and the 1–22 µF ceramics are 85 °C-rated JLCPCB basic parts: about 35 °C of margin at the expected 50 °C, and still within rating at the 70 °C worst case.

Mounting: keep the board away from the heater block's radiant heat, ideally in the hotend fan's airflow, on standoffs so air can pass behind it. The USB-C connector sets the practical ceiling of about 85 °C.

Supply voltage: the heater's resistance is fixed, so running at 30 V instead of 24 V raises heater current to about 3.75 A and Q2's loss by about 55%. At 30 V, set Klipper's `max_power` to 0.64 to hold heater power at 72 W.

## Bring-up and firmware

Bring the board up on USB first, then 24 V with no loads, then CAN, and connect the heater last.

1. **USB only:** check the 3.3 V rail, hold BOOT and tap RESET; the MCU should enumerate as an STM32 DFU device.
2. **Flash Katapult** (MCU STM32G0B1, 8 MHz crystal, CAN on PB0/PB1, 1 Mbit/s), then Klipper with the same settings and the Katapult bootloader offset.
3. **24 V, current-limited to ~200 mA, no loads:** confirm Q2's gate stays at 0 V through reset and boot, and that idle draw is under ~60 mA.
4. **CAN:** bridge JP1 if this is the last node, then run `~/klippy-env/bin/python ~/klipper/scripts/canbus_query.py can0` to get the UUID.
5. **Loads:** fan first, then thermistor (check room temperature reads correctly), then the heater with a PID calibration.

Example Klipper config (replace the UUID):

```
[mcu tool]
canbus_uuid: 0123456789ab

[heater_generic tool_heater]
heater_pin: tool:PB13
sensor_type: Generic 3950
sensor_pin: tool:PA3
pullup_resistor: 4700
max_power: 1.0
min_temp: 0
max_temp: 300
control: pid
pid_Kp: 22
pid_Ki: 1
pid_Kd: 100

[verify_heater tool_heater]

[fan_generic tool_fan]
pin: tool:PB8
cycle_time: 0.01

[output_pin status_led]
pin: tool:PB5
```

Run `PID_CALIBRATE HEATER=tool_heater TARGET=200` and save the results; the PID values above are placeholders. For a PT1000, fit the shunt on JP2 and change the sensor lines to `sensor_type: PT1000` and `pullup_resistor: 2200`.

**Decisions before schematic capture (all settled; two prototype checks left):**

- [x] Sensor type settled: 100k NTC or PT1000, selected by JP2
- [x] Heater power settled: 60–72 W at 24 V
- [x] J1 settled: XT30(2+2) for a BTT/Voron-style cable, CAN order set by the swap footprints
- [x] Analog supply settled: VREF+ is a separate pin (5), VDD/VDDA bonded on pin 6, so FB1 is fitted
- [x] Mounting settled: two M3 holes on the sides, 35 mm apart; fan settled at 0.5 A or less
- [ ] Prototype check (required feature): program the board from a laptop USB port with 24 V disconnected, and confirm the buck input stays above about 4.4 V (the buck needs 4 V minimum)
- [ ] Prototype check: measure Q2's case temperature with a thermocouple during a long print in the enclosed printer; it should stay under about 110 °C
