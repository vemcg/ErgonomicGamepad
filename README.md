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
- JP1/JP2: `Connector_PinHeader_2.54mm:PinHeader_1x02_P2.54mm_Vertical`
- Y1: `Crystal:Crystal_SMD_3215-2Pin_3.2x1.5mm`
- SWR1: `Button_Switch_SMD:SW_SPST_B3U-3000P`

## Jumper Shunts Needed (Not Part of PCBA)

JP1 (power-path select) and JP2 (forces hardware bootloader via U1 pin 33 /
HWB when bridged) are populated as bare 2-pin headers during JLCPCB assembly,
but the assembly process does not install a shunt on them - a jumper shunt is
a friction-fit plastic/metal cap, not a soldered part, so it has to be
installed by hand after the boards arrive.

Buy separately (not on the PCBA BOM):
- **2.54mm 2-pin jumper shunt cap** - e.g. BOOMELE, LCSC `C5305` (~$0.01/unit,
  50-piece minimum order on LCSC). Any standard 2.54mm/0.1" shunt works; this
  is a common commodity part also sold on Amazon/DigiKey/etc.
- Need at least 2 (one per jumper), but buy a small handful (the LCSC MOQ is
  50 anyway) since they're easy to lose.

## Switches & Keycaps Needed (Not Part of PCBA)

SW01-SW24 are Kailh MX hotswap sockets, soldered directly to the board (see
Footprint Baseline above), but the actual keyswitches and keycaps are
separate hand-sourced items that get plugged in after assembly - the whole
point of a hotswap board is that these aren't soldered.

- **Hotswap sockets** (on-board, hand-soldered): Kailh `CPG151101S11-16`,
  LCSC `C5156480` - https://www.lcsc.com/datasheet/C5156480.pdf. Currently
  shows near-zero LCSC stock (consignment-style listing), so plan to
  hand-source and hand-solder these rather than rely on JLCPCB
  auto-placement - see Progress notes below. Need 24 plus a few spares.
  Each socket takes 2 solder joints (through-hole); the extra alignment
  pins in the footprint hold it steady while soldering. For practical
  hobbyist purchasing, the real path is AliExpress - there are multiple
  listings selling genuine Kailh hotswap sockets in small hobbyist-friendly
  quantities (30/90/110-packs), which is how most individual keyboard
  builders actually buy these - or a specialty keyboard-parts retailer
  like splitkb.com, which stocks Kailh hotswap sockets specifically for
  this use case.
- **Keyswitches** (plug into the sockets, not soldered): Cherry MX Brown
  (tactile), official part `MX1A-G1NW`. Also frequently out of stock on
  LCSC - source from a specialty mechanical-keyboard parts retailer instead
  (e.g. KBDfans, NovelKeys, Mechanicalkeyboards.com, or similar). Since the
  socket is switch-agnostic (any standard MX-footprint switch fits), a
  well-regarded MX-compatible clone switch would also work if genuine
  Cherry isn't available. Need 24 plus a few spares.
- **Keycaps**: MX-compatible (cross-stem) keycaps, not yet specced -
  profile (OEM/Cherry/DSA/etc.), material, and colorway are a personal
  choice. Note this layout is a non-standard ergonomic 4x6 matrix, not a
  regular keyboard row layout, so a generic pre-made keycap set is unlikely
  to have correctly-sculpted keycaps for every position - uniform-profile
  (same shape regardless of position) or blank keycaps are the simplest
  option unless a custom set is planned.

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
