# ErgonomicGamepad Process Checklist (Detailed)

Use this file as the full grind checklist from project prep through fabrication handoff.

## How To Use This Checklist

1. Work from top to bottom.
2. Check items as you complete them.
3. If blocked, add a short note under the blocked item and continue with the next independent item.
4. Commit often.

## 0) Project Setup (One-Time)

- [ ] Install KiCad 10.0+.
- [ ] Open `ErgonomicGamepad.kicad_pro`.
- [ ] Confirm project opens cleanly (no stale lock-file confusion from old sessions).
- [ ] Confirm local libraries needed by footprints are available.
- [ ] Create a baseline git commit before making major changes.

Verification:
- [ ] Open schematic and PCB once each and confirm they load without missing file errors.

## 1) Requirements Freeze (Before Heavy Layout)

- [ ] Confirm matrix goal: 4x6 (24 keys).
- [ ] Confirm switch/socket strategy (hot-swap MX).
- [ ] Confirm USB-C connector part and orientation strategy.
- [ ] Confirm power path strategy and required protection parts.
- [ ] Confirm mounting-hole plan and any enclosure constraints.
- [ ] Confirm debug/programming connector strategy (ISP).

Verification:
- [ ] All above decisions are written in project notes/README.

## 2) Part Selection and Sourcing

- [ ] Choose MPN for each symbol.
- [ ] Prefer JLC/LCSC in-stock parts for assembled items.
- [ ] Fill LCSC + MPN + Manufacturer in `jlcpcb/production_files/jlc_sourcing_bom_template.csv`.
- [ ] Queue unresolved parts in `jlcpcb/production_files/jlc_stock_check_queue.csv`.
- [ ] Mark DNP and hand-assembly items explicitly.

Verification:
- [ ] No critical schematic component is missing a sourcing plan.
- [ ] Every JLC-assembled line has a valid LCSC number or documented alternate.

## 3) Footprints and Mechanical Validity

- [ ] Assign footprint for every symbol.
- [ ] Cross-check each footprint against package dimensions in datasheet.
- [ ] Validate orientation for polarity/pin-1 sensitive parts.
- [ ] Confirm switch pitch/spacing and keycap clearance assumptions.
- [ ] Add/confirm mounting holes and keepouts.
- [ ] Add test points for key debug rails if needed.

Verification:
- [ ] No symbol left without footprint.
- [ ] Orientation-sensitive components are visually verified.

## 4) Schematic Electrical Verification (ERC)

- [ ] Run ERC (`Inspect -> Electrical Rules Checker`).
- [ ] Fix all blocking ERC errors.
- [ ] Document intentional warnings so future checks are clear.
- [ ] Review critical nets manually:
- [ ] MCU power and decoupling topology.
- [ ] USB D+ and D- connectivity.
- [ ] Reset and ISP lines.
- [ ] Matrix row/column mapping.

Verification:
- [ ] ERC is clean of blocking issues.
- [ ] Critical net review is complete and documented.

## 5) Schematic -> PCB Sync

- [ ] Run `Tools -> Update PCB from Schematic`.
- [ ] Confirm no missing-footprint errors.
- [ ] Confirm no accidental footprint remaps.
- [ ] Confirm netlist-level changes are expected.

Verification:
- [ ] PCB reflects current schematic exactly.

## 6) PCB Rule Setup Before Placement

- [ ] Define board outline on `Edge.Cuts`.
- [ ] Set clearance/track/via rules to fab-capable values.
- [ ] Define net classes (power, USB, matrix, etc.).
- [ ] Confirm layer stack/thickness target for fabrication.

Verification:
- [ ] Rules are set before routing starts.

## 7) Component Placement

- [ ] Place switch sockets first (mechanical anchor).
- [ ] Place MCU for practical fanout.
- [ ] Place decoupling caps close to MCU power pins.
- [ ] Place USB-C and nearby support/protection parts tightly.
- [ ] Place headers/test points for easy probe/cable access.
- [ ] Confirm mounting/tool clearance.

Verification:
- [ ] Components are placeable/routable without obvious congestion traps.

## 8) Routing

- [ ] Route power rails first.
- [ ] Route USB differential pair with clean geometry and consistent behavior.
- [ ] Route matrix traces with minimal crossover complexity.
- [ ] Add copper zones and refill.
- [ ] Remove weak geometry (needless neck-downs, awkward acute corners).

Verification:
- [ ] No critical net left in ambiguous state.

## 9) PCB Verification (DRC + Visual)

- [ ] Run DRC (`Inspect -> Design Rules Checker`).
- [ ] Fix all fabrication-blocking DRC issues.
- [ ] Confirm unrouted nets are zero before release (unless intentionally documented).
- [ ] Use 3D view for connector/mechanical collision sanity check.
- [ ] Re-run DRC after each major fix set.

Verification:
- [ ] DRC is clean for manufacturing intent.

## 10) Pre-Release Manufacturing Sanity

- [ ] Silkscreen labels are readable and off exposed pads.
- [ ] Polarized component markings are clear.
- [ ] Reference designators are present for assembly/debug.
- [ ] Fiducials/tooling are present if assembly process needs them.
- [ ] Freeze release commit and tag it.

Verification:
- [ ] Board is reviewable by someone else without guesswork.

## 11) Export Gerbers + Drills

In KiCad PCB Editor:

1. `File -> Plot...`
2. Select output format: `Gerber`
3. Plot required layers:
- [ ] F.Cu
- [ ] B.Cu
- [ ] F.SilkS
- [ ] B.SilkS
- [ ] F.Mask
- [ ] B.Mask
- [ ] Edge.Cuts
4. Click `Plot`.
5. Click `Generate Drill Files...`.
6. Generate Excellon drill files (PTH + NPTH as appropriate).
7. Package Gerbers + drills in one zip file.

Verification:
- [ ] Gerber set includes board outline and both mask layers.
- [ ] Drill files are present and non-empty.

## 12) Export Assembly Files (If JLC Assembly)

- [ ] Export BOM CSV.
- [ ] Export CPL/Pick-and-Place file.
- [ ] Ensure BOM refdes matches CPL refdes exactly.
- [ ] Ensure LCSC numbers are present where JLC places parts.
- [ ] Confirm DNP lines are clearly marked.

Verification:
- [ ] BOM/CPL pair imports without obvious mapping issues.

## 13) Upload and Manufacturer Review

- [ ] Upload Gerber zip to JLCPCB.
- [ ] Confirm board preview, dimensions, layer count, drill interpretation.
- [ ] Upload BOM + CPL if ordering assembly.
- [ ] Resolve rotation, offset, and refdes mapping issues.
- [ ] Review substitutions, price, and lead time.

Verification:
- [ ] Quote is valid and manufacturable with acceptable substitutions.

## 14) Final Release Lock

- [ ] Run ERC and DRC one final time on release revision.
- [ ] Confirm no accidental post-check edits.
- [ ] Save final manufacturing outputs under `jlcpcb/gerber/`.
- [ ] Tag release (example: `v0.1-proto1`).

Verification:
- [ ] Repo, outputs, and tag all match the same final revision.

## Daily Progress Loop (When You Feel Stuck)

1. Pick exactly one section above.
2. Complete 1 to 3 checkboxes only.
3. Run the relevant verification items.
4. Commit with a clear message.
5. Stop and continue tomorrow from the next unchecked item.
