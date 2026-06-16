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

✅ **Schematic**: Complete with electrical rule check (ERC) passing  
✅ **Footprints**: All components assigned production-grade footprints  
🟨 **PCB Layout**: Scaffold created, ready for board layout  
🟨 **Firmware**: Not yet started (placeholder for future development)  

### Latest Changes

- Initial project commit with verified USB power path
- ATmega32U4 microcontroller integration
- 24-switch matrix with anti-ghosting support
- All connector and component footprints assigned
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
