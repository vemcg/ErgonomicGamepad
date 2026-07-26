#!/usr/bin/env python3
"""Move one or more whole keys (SW0N + DM0N + their connecting trace) up,
down, left, or right by a specified distance, by editing
ErgonomicGamepad.kicad_pcb directly. Meant for ergonomic adjustments
(columnar stagger, per-key nudges, etc.) after the initial grid layout.

Usage:
    python scripts/06_move_key.py --keys 9,10,11,12 --direction up --distance 7
    python scripts/06_move_key.py --keys SW05 --direction left --distance 2.5 [--dry-run]

--keys accepts a comma-separated list of key numbers (with or without
leading zeros) or SW/DM/Key-prefixed references - "9", "09", "SW09", and
"Key09" all mean the same key.

--direction is up/down/left/right, matching standard on-screen orientation
(KiCad's Y axis increases downward, so "up" is negative Y, "right" is
positive X).

This is a pure translation - the switch, diode, and trace all move by the
identical (dx, dy) with no rotation change, so no pad-angle fix is needed
(unlike 03/05, which reposition diodes to a new rotated offset). Skips any
key whose switch or diode footprint is locked (reported, not silently
skipped).
"""
import argparse
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PCB_PATH = ROOT / "ErgonomicGamepad.kicad_pcb"

AT_RE = re.compile(r"\(at\s+(-?[\d.]+)\s+(-?[\d.]+)(?:\s+(-?[\d.]+))?\s*\)")
REFERENCE_RE = re.compile(r'\(property "Reference" "([^"]*)"')
NET_RE = re.compile(r'\(net\s+"([^"]*)"\)')

DIRECTIONS = {
    "up": (0.0, -1.0),
    "down": (0.0, 1.0),
    "left": (-1.0, 0.0),
    "right": (1.0, 0.0),
}


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", newline="")


def write_text(path: Path, text: str) -> None:
    path.write_text(text, encoding="utf-8", newline="")


def find_matching_paren(text: str, open_idx: int) -> int:
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
    for m in re.finditer(open_pattern, text):
        start = m.start()
        yield start, find_matching_paren(text, start)


def fmt(n):
    r = round(n, 6)
    if abs(r - round(r)) < 1e-9:
        return str(int(round(r)))
    s = f"{r:.6f}".rstrip("0").rstrip(".")
    return s


def format_at(x, y, angle_str):
    if angle_str is None or abs(float(angle_str)) < 1e-9:
        return f"(at {fmt(x)} {fmt(y)})"
    return f"(at {fmt(x)} {fmt(y)} {angle_str})"


class Footprint:
    def __init__(self, start, end, text):
        self.start = start
        self.end = end
        ref_m = REFERENCE_RE.search(text)
        self.reference = ref_m.group(1) if ref_m else None
        self.locked = bool(re.search(r"\(locked\b", text))
        self.at_match = AT_RE.search(text)
        self.pad_nets = {}
        for pstart, pend in iter_blocks(text, r"\(pad\b"):
            pad_text = text[pstart:pend + 1]
            num_m = re.match(r'\(pad\s+"([^"]*)"', pad_text)
            net_m = NET_RE.search(pad_text)
            if num_m and net_m:
                self.pad_nets[num_m.group(1)] = net_m.group(1)


def parse_footprints(pcb_text: str):
    by_ref = {}
    for start, end in iter_blocks(pcb_text, r'\(footprint\s+"'):
        fp = Footprint(start, end, pcb_text[start:end + 1])
        if fp.reference:
            by_ref[fp.reference] = fp
    return by_ref


def parse_segments(pcb_text: str):
    segments = []
    for start, end in iter_blocks(pcb_text, r"\(segment\b"):
        block = pcb_text[start:end + 1]
        start_m = re.search(r"\(start\s+(-?[\d.]+)\s+(-?[\d.]+)\)", block)
        end_m = re.search(r"\(end\s+(-?[\d.]+)\s+(-?[\d.]+)\)", block)
        net_m = NET_RE.search(block)
        if not (start_m and end_m and net_m):
            continue
        segments.append({
            "block_start": start,
            "start_match": start_m, "end_match": end_m,
            "net": net_m.group(1),
        })
    return segments


def apply_edits(text: str, edits: list) -> str:
    for start, end, new_text in sorted(edits, key=lambda e: e[0], reverse=True):
        text = text[:start] + new_text + text[end:]
    return text


def normalize_key(token: str) -> str:
    m = re.search(r"(\d+)", token)
    if not m:
        sys.exit(f"ERROR: could not parse key reference {token!r}")
    return f"{int(m.group(1)):02d}"


def main():
    parser = argparse.ArgumentParser(description=__doc__,
                                      formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--keys", required=True,
                         help="Comma-separated key numbers/references, e.g. '9,10,11,12' or 'SW09,SW10'")
    parser.add_argument("--direction", required=True, choices=sorted(DIRECTIONS),
                         help="up/down/left/right (screen-relative: up = -Y, right = +X)")
    parser.add_argument("--distance", type=float, required=True, help="Distance in mm")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    ux, uy = DIRECTIONS[args.direction]
    dx, dy = ux * args.distance, uy * args.distance

    key_nums = [normalize_key(t) for t in args.keys.split(",") if t.strip()]

    pcb_text = read_text(PCB_PATH)
    footprints = parse_footprints(pcb_text)
    segments = parse_segments(pcb_text)

    edits = []
    moved, skipped_locked, missing = [], [], []

    for num in key_nums:
        sw_ref, dm_ref = f"SW{num}", f"DM{num}"
        if sw_ref not in footprints or dm_ref not in footprints:
            missing.append(f"Key{num}")
            continue

        sw_fp = footprints[sw_ref]
        dm_fp = footprints[dm_ref]

        if sw_fp.locked or dm_fp.locked:
            skipped_locked.append(f"Key{num}")
            continue

        for fp in (sw_fp, dm_fp):
            x, y, angle = fp.at_match.group(1), fp.at_match.group(2), fp.at_match.group(3)
            new_at = format_at(float(x) + dx, float(y) + dy, angle)
            edits.append((fp.start + fp.at_match.start(), fp.start + fp.at_match.end(), new_at))

        key_anode_net = dm_fp.pad_nets.get("2")
        if key_anode_net:
            for seg in segments:
                if seg["net"] != key_anode_net:
                    continue
                sx, sy = seg["start_match"].group(1), seg["start_match"].group(2)
                ex, ey = seg["end_match"].group(1), seg["end_match"].group(2)
                new_start = f"(start {fmt(float(sx) + dx)} {fmt(float(sy) + dy)})"
                new_end = f"(end {fmt(float(ex) + dx)} {fmt(float(ey) + dy)})"
                seg_base = seg["block_start"]
                edits.append((seg_base + seg["start_match"].start(),
                              seg_base + seg["start_match"].end(), new_start))
                edits.append((seg_base + seg["end_match"].start(),
                              seg_base + seg["end_match"].end(), new_end))

        moved.append(f"Key{num}")

    print(f"Direction: {args.direction} ({fmt(dx)}, {fmt(dy)}) mm")
    print(f"Moved {len(moved)}: {', '.join(moved) or '(none)'}")
    if skipped_locked:
        print(f"Skipped (locked): {', '.join(skipped_locked)}")
    if missing:
        print(f"Missing footprints, skipped: {', '.join(missing)}")

    if args.dry_run:
        print("Dry run: no changes written.")
        return

    write_text(PCB_PATH, apply_edits(pcb_text, edits))
    print(f"Wrote changes to {PCB_PATH.name}")


if __name__ == "__main__":
    main()
