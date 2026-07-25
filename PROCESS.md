# ErgonomicGamepad Process Checklist (Detailed)

Use this file as the full grind checklist from project prep through fabrication handoff.

## How To Use This Checklist

1. Work from top to bottom.
2. Check items as you complete them.
3. If blocked, add a short note under the blocked item and continue with the next independent item.
4. Commit often.

## 0) Project Setup (One-Time)

- [X] Install KiCad 10.0+.
- [X] Open `ErgonomicGamepad.kicad_pro`.
- [X] Confirm project opens cleanly (no stale lock-file confusion from old sessions).
- [X] Confirm local libraries needed by footprints are available.
- [X] Create a baseline git commit before making major changes.

Verification:
- [X] Open schematic and PCB once each and confirm they load without missing file errors.

## 1) Requirements Freeze (Before Heavy Layout)

- [X] Confirm matrix goal: 4x6 (24 keys).
- [X] Confirm switch/socket strategy (hot-swap MX).
- [X] Confirm USB-C connector part and orientation strategy.
- [X] Confirm power path strategy and required protection parts.
- [ ] Confirm mounting-hole plan and any enclosure constraints.
- [X] Confirm debug/programming connector strategy (ISP).

USB-C connector part + orientation strategy details:
- [X] Pick the exact connector MPN first (mid-mount vs top-mount, horizontal vs vertical, SMT-only vs hybrid with through-hole shell tabs).
- [X] Confirm your use case is USB 2.0 device-only (power + D+/D-), not full USB-C feature set.
- [X] Decide plug orientation behavior:
- [X] Fully reversible: tie A6 to B6 for D+, and A7 to B7 for D- at the connector footprint.
- [X] Confirm CC implementation for device mode (UFP): place 5.1k pull-down resistors from CC1 and CC2 to GND.
- [X] Verify shield/shell connection plan (direct GND or GND through RC/ferrite policy per your EMI goal) and keep it consistent with board grounding strategy.
- [ ] Confirm mechanical robustness: shell-anchor pad dimensions, courtyard/keepout, and cable insertion stress path.
- [ ] Confirm footprint pin numbering and front/back orientation against the datasheet drawing before routing.
- [ ] Confirm nearby ESD protection placement for D+/D- and VBUS (close to connector, short return path to GND).

Verification for USB-C decision:
- [ ] Schematic symbol pins and footprint pins are cross-checked against connector datasheet pin map.
- [X] Chosen orientation strategy is documented in README so future revisions do not accidentally change behavior.

Recommended default for this project (unless a later constraint overrides it):
- [X] Use a USB-C receptacle with hybrid retention (SMT pins + through-hole shell tabs) for stronger cable-insertion durability.
- [X] Implement fully reversible USB 2.0 routing at the connector (A6/B6 joined for D+, A7/B7 joined for D-).
- [X] Use UFP CC pulldowns: 5.1k from CC1 to GND and 5.1k from CC2 to GND.
- [X] Add USB ESD protection array near connector for D+, D-, and VBUS.
- [X] Tie shield/shell to GND through your chosen policy and keep that policy documented consistently in schematic notes.

Final USB-C signoff checklist (release gate):
- [ ] Hard-edge decision locked: USB-C connector (J1) and side reset switch (SWR1) are both placed on north board edge.
- [ ] Panelization decision locked: avoid mouse-bites/V-score stress features near J1 shell tabs and SWR1 body keepout.
- [ ] J1 footprint and connector mechanical drawing are cross-checked (plug overhang, shell tab footprint, insertion clearance).
- [ ] USB 2.0 reversibility confirmed electrically: A6/B6 tied to D+, A7/B7 tied to D-.
- [ ] CC policy confirmed electrically: CC1 -> 5.1k -> GND and CC2 -> 5.1k -> GND.
- [ ] USB data path conditioning confirmed: series resistors on D+ and D- are placed and value-checked.
- [ ] USB ESD array part is added in schematic with explicit MPN/LCSC fields.
- [ ] USB ESD array footprint is placed close to J1 with short traces and short GND return.
- [ ] Shield/shell grounding policy is explicitly selected (direct GND or RC/ferrite policy) and implemented consistently.
- [ ] DRC/ERC re-run after USB/ESD updates with no unresolved manufacturing-blocking issues.

Verification:
- [ ] All above decisions are written in project notes/README.

## 2) Part Selection and Sourcing

- [X] Choose MPN for each symbol.
- [X] Prefer JLC/LCSC in-stock parts for assembled items.
- [X] Fill LCSC + MPN + Manufacturer in `jlcpcb/production_files/jlc_sourcing_bom_template.csv`.
- [X] Track pre-order stock/sourcing risk in `jlcpcb/production_files/verify_stock_before_ordering.csv`.
- [X] Mark DNP and hand-assembly items explicitly.

Verification:
- [X] No critical schematic component is missing a sourcing plan.
- [X] Every JLC-assembled line has a valid LCSC number or documented alternate.

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
