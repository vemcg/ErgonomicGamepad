# ErgonomicGamepad

Custom ergonomic gaming keypad PCB project (KiCad) with a 4x6 key matrix, hot-swap sockets, and USB-C.

## Overview

This repo contains the schematic, PCB, and production support files for an ATmega32U4-based ergonomic keypad.

## Hardware Summary

| Item | Value |
|---|---|
| MCU | ATmega32U4 (TQFP-44) |
| Key Matrix | 4 rows x 6 columns (24 keys) |
| Switch Interface | MX-compatible Kailh hot-swap sockets |
| USB | USB-C receptacle |
| Clock | 16 MHz crystal |
| Passive Size | 0603 resistors/capacitors |
| Protection/Diodes | 1N4148 matrix diodes, 1N5819WS Schottky |

## Core Project Files

- `ErgonomicGamepad.kicad_sch` - Schematic
- `ErgonomicGamepad.kicad_pcb` - PCB layout
- `ErgonomicGamepad.kicad_pro` - KiCad project
- `jlcpcb/production_files/jlc_sourcing_bom_template.csv` - Main sourcing/BOM table
- `jlcpcb/production_files/jlc_stock_check_queue.csv` - JLC stock-check queue
- `jlcpcb/gerber/` - Manufacturing output folder

## Pinout Baseline

### Matrix

| Signal | Pins |
|---|---|
| ROW1-ROW4 | PF7, PF6, PF5, PF4 |
| COL1-COL6 | PD1, PD2, PD3, PD4, PD5, PD6 |

### Programming Header (ISP)

| Signal | Pin Mapping |
|---|---|
| SCK | PB1 |
| MOSI | PB2 |
| MISO | PB3 |
| RESET | J5 pin 5 -> U1 ~RESET |

## Footprint Baseline (Current)

- SW1-SW24: `Switch_Keyboard_Hotswap_Kailh:SW_Hotswap_Kailh_MX_Plated_1.00u`
- J1: `Connector_USB:USB_C_Receptacle_HRO_TYPE-C-31-M-12`
- R1-R7: `Resistor_SMD:R_0603_1608Metric`
- C1-C5: `Capacitor_SMD:C_0603_1608Metric`
- D25-D26: `LED_SMD:LED_0603_1608Metric`
- TP1-TP7: `TestPoint:TestPoint_Pad_D1.5mm`
- J2/J3/J4/J6: `PinHeader_1x08_P2.54mm_Vertical`
- J7: `PinHeader_1x02_P2.54mm_Vertical`
- J5: `PinHeader_2x03_P2.54mm_Vertical`
- JP1: `SolderJumper-2_P1.3mm_Open_Pad1.0x1.5mm`
- Y1: `Crystal:Crystal_SMD_3215-2Pin_3.2x1.5mm`
- SWR1: `Button_Switch_SMD:SW_SPST_TL3342`

## Progress (Brief)

Done:
- Schematic is component-complete.
- Footprints assigned for all currently tracked parts.
- Schematic and PCB baseline are synced.
- ISP signal mapping corrected and documented.
- JLC sourcing workflow files are in place.

Not done yet:
- Component placement refinement.
- PCB routing completion.
- Panelization/mechanical finalization.
- Final DRC-clean release candidate.
- Gerber/BOM/CPL release package for fabrication.
- Firmware development.

## Process Checklist

For the full detailed build, verification, and manufacturing checklist, use [PROCESS.md](PROCESS.md).

---

Last Updated: July 2026
Project Status: Pre-Layout Baseline
