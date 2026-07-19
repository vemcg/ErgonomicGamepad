# Ergonomic Gamepad — Unresolved Part Specification Punch List

Source: `ErgonomicGamepad.kicad_sch`
Generated: 2026-07-19

Every symbol placed on the schematic that would actually be soldered to the
board by the manufacturer should carry five fields: **Datasheet**,
**Manufacturer**, **Manufacturer Part Number (MPN)**, **Supplier**, and
**LCSC** (LCSC part number).

Of the 118 symbols in the schematic, 82 are real, board-mounted, BOM-relevant
parts (power symbols and PWR_FLAGs were excluded — they aren't physical
components). **77 of those 82 are missing at least one of the five fields.**
Only **D1, J1, J5, J7, and Y1** are fully resolved — use them as templates
for the field structure.

## Unresolved, grouped by part type

| Group | Refs | Missing |
|---|---|---|
| Diodes (1N4148WS) | D2–D24, D09 (23 total) | Manufacturer, MPN, LCSC (Datasheet & Supplier="LCSC" already filled) |
| ↳ worse subset | D14, D18, D19 | also missing **Supplier** — the property isn't defined at all on these three, unlike the rest |
| Resistors | R1–R7 (7) | Datasheet, Manufacturer, MPN, LCSC |
| Capacitors | C1–C5 (5) | Datasheet, Manufacturer, MPN, LCSC |
| DIP switches / hotswap sockets | SW01–SW24, SWR1 (25) | Datasheet, Manufacturer, MPN, LCSC |
| 8-pin headers | J2, J3, J4, J6 (4) | Datasheet, Manufacturer, MPN, LCSC |
| Test points | TP1–TP7 (7) | all 5 fields |
| LEDs | D25 (Pwr), D26 (Dbg) | Datasheet, Manufacturer, MPN, LCSC |
| MCU | U1 (ATmega32U4-A) | Manufacturer, MPN, LCSC (has datasheet) |
| ESD protection IC | U2 (USBLC6-2SC6) | just **LCSC** part number |
| Solder jumper | JP1 | all 5 fields — bare PCB pad jumper (`in_bom = no`), not a stocked part |

## Fully resolved (no action needed)

D1, J1 (USB-C receptacle), J5 (ISP header), J7 (power connector), Y1 (crystal)

## Flagged for review

- **D09 vs D9** — both exist as separate reference designators for the same
  1N4148WS diode. Only diode using a leading zero; likely an inconsistent
  naming pattern rather than an intentional duplicate part — confirm it's
  correct.
- **JP1 and TP1–TP7** — pad-only footprints (solder jumper, test points)
  with no real manufacturer part behind them. Consider marking these
  DNP / excluded from BOM rather than filling in Manufacturer/MPN/LCSC,
  since there's no physical component to source.
