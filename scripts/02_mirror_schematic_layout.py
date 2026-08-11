#!/usr/bin/env python3
"""Sync footprint positions/rotations from the schematic onto the PCB, and manage
footprint locking, by editing the .kicad_sch / .kicad_pcb S-expression files directly.

Usage:
    python scripts/02_mirror_schematic_layout.py sync [--dry-run]
    python scripts/02_mirror_schematic_layout.py lock-all [--dry-run]
    python scripts/02_mirror_schematic_layout.py unlock-all [--dry-run]

sync:
    For every footprint whose reference designator matches a schematic symbol,
    copy that symbol's schematic (x, y, rotation) onto the footprint's own
    (at ...) - UNLESS the footprint is already locked, or has routed copper
    (a track segment, arc, or via) on one of its pads' nets, in which case it
    is left untouched and reported instead.

lock-all / unlock-all:
    Add or remove the `(locked yes)` flag on every footprint, without touching
    position. Use lock-all as a checkpoint after arranging a placement pass, so
    a later `sync` only touches new, not-yet-arranged footprints.

Only footprint/symbol positions are ever rewritten. Net assignments, pads, and
tracks are never modified, so schematic connectivity can't be affected.
"""
import argparse
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SCH_PATHS = sorted(ROOT.glob("*.kicad_sch"))
PCB_PATH = ROOT / "ErgonomicGamepad.kicad_pcb"

AT_RE = re.compile(r"\(at\s+(-?[\d.]+)\s+(-?[\d.]+)(?:\s+(-?[\d.]+))?\s*\)")
REFERENCE_RE = re.compile(r'\(property "Reference" "([^"]*)"')
NET_RE = re.compile(r"\(net\s+(\d+)")
LOCKED_LINE_RE = re.compile(r"[ \t]*\(locked\b[^)]*\)\r?\n")


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", newline="")


def write_text(path: Path, text: str) -> None:
    path.write_text(text, encoding="utf-8", newline="")


def find_matching_paren(text: str, open_idx: int) -> int:
    """Return the index of the ')' matching the '(' at open_idx, respecting quoted strings."""
    depth = 0
    in_string = False
    i = open_idx
    n = len(text)
    while i < n:
        c = text[i]
        if in_string:
            if c == "\\":
                i += 2
                continue
            if c == '"':
                in_string = False
        else:
            if c == '"':
                in_string = True
            elif c == "(":
                depth += 1
            elif c == ")":
                depth -= 1
                if depth == 0:
                    return i
        i += 1
    raise ValueError(f"Unbalanced parentheses starting at index {open_idx}")


def iter_blocks(text: str, open_pattern: str):
    """Yield (start, end) char spans for each block whose opening matches open_pattern."""
    for m in re.finditer(open_pattern, text):
        start = m.start()
        yield start, find_matching_paren(text, start)


def parse_schematic_positions(sch_texts: list) -> dict:
    """Map reference designator -> (x_str, y_str, angle_str) from placed schematic symbols,
    across every sheet in the hierarchy. Reference designators are unique project-wide, so
    positions from all sheets are merged into a single lookup."""
    positions = {}
    for sch_text in sch_texts:
        for start, end in iter_blocks(sch_text, r"\(symbol\s+\(lib_id"):
            block = sch_text[start:end + 1]
            at_m = AT_RE.search(block)
            ref_m = REFERENCE_RE.search(block)
            if not at_m or not ref_m:
                continue
            ref = ref_m.group(1)
            if ref in positions:
                continue  # first occurrence wins (multi-unit symbols)
            positions[ref] = (at_m.group(1), at_m.group(2), at_m.group(3) or "0")
    return positions


def find_routed_nets(pcb_text: str) -> set:
    """Net numbers that already have copper (track segments, arcs, or vias) routed."""
    nets = set()
    for pattern in (r"\(segment\b", r"\(arc\b", r"\(via\b"):
        for start, end in iter_blocks(pcb_text, pattern):
            net_m = NET_RE.search(pcb_text[start:end + 1])
            if net_m:
                nets.add(net_m.group(1))
    return nets


class Footprint:
    def __init__(self, start, end, text):
        self.start = start
        self.end = end
        self.text = text
        ref_m = REFERENCE_RE.search(text)
        self.reference = ref_m.group(1) if ref_m else None
        self.locked = bool(re.search(r"\(locked\b", text))
        self.at_match = AT_RE.search(text)
        self.pad_nets = set()
        for pstart, pend in iter_blocks(text, r"\(pad\b"):
            net_m = NET_RE.search(text[pstart:pend + 1])
            if net_m:
                self.pad_nets.add(net_m.group(1))


def parse_footprints(pcb_text: str):
    return [Footprint(start, end, pcb_text[start:end + 1])
            for start, end in iter_blocks(pcb_text, r'\(footprint\s+"')]


def format_at(x: str, y: str, angle: str) -> str:
    try:
        angle_is_zero = float(angle) == 0.0
    except ValueError:
        angle_is_zero = False
    return f"(at {x} {y})" if angle_is_zero else f"(at {x} {y} {angle})"


def apply_edits(text: str, edits: list) -> str:
    for start, end, new_text in sorted(edits, key=lambda e: e[0], reverse=True):
        text = text[:start] + new_text + text[end:]
    return text


def cmd_sync(args):
    sch_texts = [read_text(p) for p in SCH_PATHS]
    pcb_text = read_text(PCB_PATH)

    sch_positions = parse_schematic_positions(sch_texts)
    routed_nets = find_routed_nets(pcb_text)
    footprints = parse_footprints(pcb_text)

    edits = []
    synced, skipped_locked, skipped_routed, unmatched = [], [], [], []

    for fp in footprints:
        if fp.reference is None:
            continue
        if fp.locked:
            skipped_locked.append(fp.reference)
            continue
        if fp.pad_nets & routed_nets:
            skipped_routed.append(fp.reference)
            continue
        if fp.reference not in sch_positions:
            unmatched.append(fp.reference)
            continue
        if fp.at_match is None:
            print(f"WARNING: {fp.reference}: no (at ...) found on footprint - skipping", file=sys.stderr)
            continue
        x, y, angle = sch_positions[fp.reference]
        new_at = format_at(x, y, angle)
        edits.append((fp.start + fp.at_match.start(), fp.start + fp.at_match.end(), new_at))
        synced.append(fp.reference)

    print(f"Sync {len(synced)} footprint(s): {', '.join(sorted(synced)) or '(none)'}")
    if skipped_locked:
        print(f"Skipped, locked: {', '.join(sorted(skipped_locked))}")
    if skipped_routed:
        print(f"Skipped, has routed copper: {', '.join(sorted(skipped_routed))}")
    if unmatched:
        print(f"No schematic match, left untouched: {', '.join(sorted(unmatched))}")

    if args.dry_run:
        print("Dry run: no changes written.")
        return

    write_text(PCB_PATH, apply_edits(pcb_text, edits))
    print(f"Wrote {len(synced)} updated position(s) to {PCB_PATH.name}")


def cmd_lock(args, lock: bool):
    pcb_text = read_text(PCB_PATH)
    footprints = parse_footprints(pcb_text)

    edits = []
    changed = []
    for fp in footprints:
        if lock and not fp.locked:
            insert_at = fp.start + fp.text.index("\r\n") + 2
            edits.append((insert_at, insert_at, "\t\t(locked yes)\r\n"))
            changed.append(fp.reference)
        elif not lock and fp.locked:
            m = LOCKED_LINE_RE.search(fp.text)
            if m:
                edits.append((fp.start + m.start(), fp.start + m.end(), ""))
                changed.append(fp.reference)

    action = "Would lock" if (lock and args.dry_run) else "Locked" if lock else \
        "Would unlock" if args.dry_run else "Unlocked"
    print(f"{action} {len(changed)} footprint(s): {', '.join(sorted(r for r in changed if r)) or '(none)'}")

    if args.dry_run:
        print("Dry run: no changes written.")
        return

    write_text(PCB_PATH, apply_edits(pcb_text, edits))
    print(f"Wrote changes to {PCB_PATH.name}")


def main():
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest="command", required=True)

    p_sync = sub.add_parser("sync", help="Copy positions/rotations from schematic to unlocked, unrouted footprints")
    p_sync.add_argument("--dry-run", action="store_true", help="Report what would change without writing")

    p_lock = sub.add_parser("lock-all", help="Lock every footprint in place")
    p_lock.add_argument("--dry-run", action="store_true")

    p_unlock = sub.add_parser("unlock-all", help="Unlock every footprint")
    p_unlock.add_argument("--dry-run", action="store_true")

    args = parser.parse_args()
    {
        "sync": cmd_sync,
        "lock-all": lambda a: cmd_lock(a, lock=True),
        "unlock-all": lambda a: cmd_lock(a, lock=False),
    }[args.command](args)


if __name__ == "__main__":
    main()
