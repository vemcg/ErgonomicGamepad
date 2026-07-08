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
├── ErgonomicGamepad.kicad_pcb    # PCB pre-layout baseline (synced to schematic)
├── ErgonomicGamepad.kicad_pro    # KiCad project settings
├── ErgonomicGamepad.kicad_prl    # Project layout rules
└── jlcpcb/
   ├── production_files/
   │   ├── jlc_sourcing_bom_template.csv  # Master sourcing/assembly table
   │   └── jlc_stock_check_queue.csv      # JLC stock-check working queue
   └── gerber/                            # Generated fab output (ignored in git)
```

## Current Status

✅ **Schematic**: Component-complete and synced to PCB baseline. ISP header labels now align with AVR ISP usage (SCK -> PB1, MOSI -> PB2, MISO -> PB3; RESET on J5 pin 5).  
🟦 **Vendor**: JLCPCB selected for fabrication/assembly, sourcing parts via its LCSC catalog  
✅ **Footprints**: 83 of 83 components assigned. SW1–SW24 -> `Switch_Keyboard_Hotswap_Kailh:SW_Hotswap_Kailh_MX_Plated_1.00u` (Kailh CPG151101S11 / LCSC C2803348, via the [kiswitch](https://github.com/kiswitch/kiswitch) footprint library). J1 -> `Connector_USB:USB_C_Receptacle_HRO_TYPE-C-31-M-12` (HRO TYPE-C-31-M-12 / LCSC C165948, stock KiCad footprint). R1–R7 -> `Resistor_SMD:R_0603_1608Metric`. C1–C5 -> `Capacitor_SMD:C_0603_1608Metric`. D25/D26 -> `LED_SMD:LED_0603_1608Metric`. TP1–TP7 -> `TestPoint:TestPoint_Pad_D1.5mm`. J2/J3/J4/J6 -> `PinHeader_1x08_P2.54mm_Vertical`. J7 -> `PinHeader_1x02_P2.54mm_Vertical`. J5 -> `PinHeader_2x03_P2.54mm_Vertical`. JP1 -> `SolderJumper-2_P1.3mm_Open_Pad1.0x1.5mm`. Y1 -> `Crystal:Crystal_SMD_3215-2Pin_3.2x1.5mm`. SWR1 -> `Button_Switch_SMD:SW_SPST_TL3342`.  
✅ **PCB Layout**: Pre-layout baseline captured and tagged (`pre-layout-baseline`). Unrouted nets are still expected because routing has not started.  
🟦 **Sourcing Workflow**: JLC sourcing tables are tracked in git so manual edits can be diff-reviewed safely before ordering.  
🟨 **Firmware**: Not yet started (placeholder for future development)  



### Verification Checklist

A simple, repeatable walkthrough to confirm nothing's silently broken or unmapped. Run this top to bottom any time you've lost track of where things stand.

1. **Open the project**
   - [ ] KiCad → File → Open Project → `ErgonomicGamepad.kicad_pro`

2. **Schematic check**
   - [ ] Open `ErgonomicGamepad.kicad_sch`
   - [ ] Run **Inspect → Electrical Rules Checker (ERC)**
   - [ ] Confirm there are no new blocking ERC errors. If warnings appear, verify they are intentional and documented.

3. **Sync schematic → PCB**
   - [ ] Tools → Update PCB from Schematic
   - [ ] Confirm it completes with no missing-footprint errors and no unexpected footprint mismatches.

4. **PCB layout check**
   - [ ] Open `ErgonomicGamepad.kicad_pcb`
   - [ ] Run **Inspect → Design Rules Checker (DRC)**
   - [ ] Unrouted nets are expected right now (layout hasn't started) — just confirm the count matches what you'd expect (all nets, since nothing's routed yet), not something smaller/larger that hints at a missing connection.

5. **Sanity-check the pin map**
   - [ ] Compare real net/pin names in the schematic against the "Current Pin Map Baseline" table below.
   - [ ] If they've diverged, update this README first before trusting it for the next step.

### Known Issues

- None currently tracked as blocking for pre-layout baseline.


### Next Step (planned, not yet done)

- Lock a fully sourceable JLC BOM (LCSC populated for all JLC-placed lines).
- Replace any remaining non-SMT assembly blockers before placement/routing.
- Begin component placement refinement and routing pass.
- Run full DRC after first routing pass and document any intentional constraints/exceptions.

### JLC BOM Workflow

Use these two files together and commit frequently so every sourcing edit is reviewable:

- `jlcpcb/production_files/jlc_sourcing_bom_template.csv`
   - Master table for quantity, value, footprint, refs, LCSC, MPN, manufacturer, assembly intent, notes.
- `jlcpcb/production_files/jlc_stock_check_queue.csv`
   - Filtered queue for JLC-placed parts, sorted to prioritize rows missing LCSC (`NeedsLCSC=YES`).

Recommended loop:

1. Pick one row from `jlc_stock_check_queue.csv` with `NeedsLCSC=YES`.
2. Find an in-stock JLC/LCSC part that matches value + footprint + rating requirements.
3. Update both CSV files with LCSC, MPN, and manufacturer.
4. Commit and diff-review before moving to the next row.

### Current Pin Map Baseline

| Signal Group | Pins | Port |
|---|---|---|
| ROW1-ROW4 | PF7, PF6, PF5, PF4 | F |
| COL1-COL6 | PD1, PD2, PD3, PD4, PD5, PD6 | D |
| ISP SCK/MOSI/MISO | PB1, PB2, PB3 | B |
| RESET (ISP) | J5 pin 5 -> U1 ~RESET | RESET net |


### Latest Changes

- Initial project commit with verified USB power path
- ATmega32U4 microcontroller integration
- 24-switch matrix with anti-ghosting support
- Completed footprint assignment pass (83 of 83 assigned)
- Corrected ISP header signal mapping and RESET pin assignment
- Captured definitive pre-layout baseline and tagged it (`pre-layout-baseline`)
- Project-wide `.gitignore` rules for KiCad local history
- Moved entire project out from under OneDrive to avoid version discrepancies.

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
2. In the PCB editor: **Inspect** → **Design Rules Checker**
3. Confirm no blocking errors for the baseline; unrouted nets are expected before routing starts

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

**Last Updated**: July 2026  
**Project Status**: Pre-Layout Baseline Established
