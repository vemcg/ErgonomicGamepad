# ErgonomicGamepad

A custom-designed ergonomic gaming keypad featuring a 4×6 programmable matrix with hot-swappable switches and USB-C connectivity.

## Overview

ErgonomicGamepad is a KiCad-based hardware project to create an ergonomic, programmable input device inspired by the Periloot Caravel Gaming Keypad and leveraging design principles from the ANAVI Macro Pad 8. The device uses an ATmega32U4 microcontroller to provide USB HID functionality with full programmability.

### Key Features

- **24 Hot-Swappable Key Switches**: 4 rows × 6 columns matrix layout for customizable key bindings
- **ATmega32U4 MCU**: Native USB 2.0 support with built-in keyboard/mouse HID profiles
- **USB-C Power & Data**: Modern connector standard for charging and communication
- **Programmable Matrix**: Firmware-upgradeable key mappings and macros
- **Ergonomic Design**: Optimized layout for gaming and productivity workflows
- **Anti-Ghosting Diodes**: Matrix diodes prevent simultaneous key press errors

## Hardware Specifications

| Component | Details |
|-----------|---------|
| Microcontroller | ATmega32U4 (TQFP-44) |
| USB Interface | USB-C Receptacle (16-pin) |
| Clock | 16 MHz Crystal (SMD) |
| Matrix Layout | 4 rows × 6 columns (24 switches) |
| Switch Type | MX Cherry-compatible hot-swap sockets |
| Decoupling | Multiple 0603 SMD capacitors & resistors |
| Diodes | 1N4148 (anti-ghosting) + 1N5819WS (Schottky) |

## Project Structure

```
ErgonomicGamepad/
├── README.md                      # This file
├── .gitignore                      # Git exclusions (history, backups, locks)
├── ErgonomicGamepad.kicad_sch    # Live schematic (4 rows × 6 cols + USB + MCU)
├── ErgonomicGamepad.kicad_pcb    # PCB layout placeholder
├── ErgonomicGamepad.kicad_pro    # KiCad project settings
└── ErgonomicGamepad.kicad_prl    # Project layout rules
```

## Current Status

🟨 **Schematic**: Component-complete. RESET net fixed (see below); MISO/SCK/MOSI on the ISP header still need a deliberate pass. See "Known Issues" below  
🟦 **Vendor**: JLCPCB selected for fabrication/assembly, sourcing parts via its LCSC catalog  
✅ **Footprints**: 82 of 83 components assigned. SW1–SW24 → `Switch_Keyboard_Hotswap_Kailh:SW_Hotswap_Kailh_MX_Plated_1.00u` (Kailh CPG151101S11 / LCSC C2803348, via the [kiswitch](https://github.com/kiswitch/kiswitch) footprint library). J1 → `Connector_USB:USB_C_Receptacle_HRO_TYPE-C-31-M-12` (HRO TYPE-C-31-M-12 / LCSC C165948, stock KiCad footprint). R1–R7 → `Resistor_SMD:R_0603_1608Metric`. C1–C5 → `Capacitor_SMD:C_0603_1608Metric`. D25/D26 → `LED_SMD:LED_0603_1608Metric`. TP1–TP7 → `TestPoint:TestPoint_Pad_D1.5mm`. J2/J3/J4/J6 → `PinHeader_1x08_P2.54mm_Vertical`. J7 → `PinHeader_1x02_P2.54mm_Vertical`. J5 → `PinHeader_2x03_P2.54mm_Vertical` (matches the ANAVI Macro Pad 8 reference design). JP1 → `SolderJumper-2_P1.3mm_Open_Pad1.0x1.5mm`. Y1 → `Crystal_SMD_3225-4Pin_3.2x2.5mm` (also matches ANAVI reference). Only SWR1 (reset switch) remains — target part is TS24CA (SHOU HAN, LCSC/JLCPCB C393942), footprint still needs sourcing from the datasheet or KiCad's JLCPCB Tools plugin  
🟨 **PCB Layout**: Scaffold created, ready for board layout  
🟨 **Firmware**: Not yet started (placeholder for future development)  

### Known Issues

- **RESET net — fixed.** SWR1, J5 pin 5 (physical `~RST`), and U1 pin 13 (`~RESET`) now all share one "RESET" net. J5 pin 4 (physical MOSI, previously mislabeled "RESET") is now explicitly `no_connect` rather than silently wrong.
- **ISP MISO/SCK/MOSI still not wired to U1's real SPI pins.** Full current matrix/SPI pin map, verified directly against the schematic:

  | Signal | Pin | Port |
  |---|---|---|
  | ROW1–ROW4 | PB6, PB5, PB4, PB3 | B |
  | COL1–COL3 | PF4, PF1, PF0 | F |
  | COL4–COL6 | PD2, PD1, PD0 | D |
  | Nets literally named "SCK"/"MOSI"/"MISO" | PF7, PF6, PF5 | F |
  | **PB1, PB2 (the chip's actual hardware SPI pins)** | — | **unused, `no_connect`** |

  The nets named "SCK"/"MOSI"/"MISO" are **not** on the ATmega32U4's real hardware SPI pins (fixed in silicon as PB1/PB2/PB3) — they're a red herring on PF5–7 that can't make ISP programming work regardless of how J5 is wired. The pins ISP actually needs (PB1/PB2/PB3) are currently free of any matrix duty.
- **Reset switch (TS24CA/SWR1) is a side-actuated part meant for a board-edge cutout near J1**, so it's reachable without opening the case — footprint still pending real pad dimensions.

### Next Step (planned, not yet done)

Re-layout the matrix pin assignments to resolve the ISP wiring issue above, consolidating each signal group onto one port for simpler firmware (single-port scan instead of bits scattered across three ports):

| Signal | Planned pin | Port |
|---|---|---|
| ROW1–4 | 4 of PF0/PF1/PF4/PF5/PF6/PF7 | F (moved off Port B) |
| COL1–6 | PD0–PD7 (6 of 8) | D (consolidated from split PF/PD) |
| ISP SCK/MOSI/MISO | PB1/PB2/PB3 | B (already free — just needs wiring to J5) |

This touches all 10 row/column nets across the 24-switch matrix — a bigger change than the RESET fix, so it's being done as its own deliberate pass rather than folded into this commit. The stray "SCK"/"MOSI"/"MISO" labels currently on PF5–7 will be removed as part of this work since they don't reflect real hardware SPI wiring.

### Latest Changes

- Initial project commit with verified USB power path
- ATmega32U4 microcontroller integration
- 24-switch matrix with anti-ghosting support
- 82 of 83 component footprints assigned (JLCPCB/LCSC-sourced parts); SWR1 pending
- Discovered and documented ISP header wiring defect (see Known Issues)
- Project-wide `.gitignore` rules for KiCad local history

## Getting Started

### Prerequisites

- **KiCad 10.0+**: Download from [kicad.org](https://www.kicad.org/download/)
- **Git**: For version control and cloning
- **Optional**: Gerber viewer or PCB fabrication service account (e.g., JLCPCB, OSHPark)

### Cloning the Repository

```bash
git clone https://github.com/vemcg/ErgonomicGamepad.git
cd ErgonomicGamepad
```

### Viewing the Schematic

1. Open KiCad
2. File → Open Project → Select `ErgonomicGamepad.kicad_pro`
3. Double-click `ErgonomicGamepad.kicad_sch` to open the schematic editor

### Verifying the Design

1. In the schematic editor: **Inspect** → **Electrical Rules Checker**
2. Confirm no blocking errors (warnings may exist for unassigned switches during early PCB layout phases)

## Design Inspiration

This project draws from:
- **Periloot Caravel**: Ergonomic form factor and key layout
- **ANAVI Macro Pad 8**: Compact programmable pad reference
- **Cherry MX Standard**: Wide ecosystem of third-party switches and keycaps

## Roadmap

- [ ] Complete PCB layout
- [ ] Generate production Gerbers
- [ ] Firmware development (Arduino IDE or QMK)
- [ ] First prototype assembly and testing
- [ ] Documentation for assembly and flashing

## Contributing

This is a personal project, but feedback and suggestions are welcome. Please open an issue or discussion to share ideas.

## License

This project is provided as-is for personal and educational use. No specific license is currently assigned.

## Contact

For questions or suggestions, please reach out via GitHub issues.

---

**Last Updated**: June 2026  
**Project Status**: Early Development (Schematic Complete)
