#!/usr/bin/env python3
"""Move one key (SW0N + DM0N + its connecting trace) so it lines up with
another key along one axis - e.g. "move Key09 up/down to line up with
Key05" sets Key09's Y to match Key05's Y, leaving X untouched. Edits
ErgonomicGamepad.kicad_pcb directly.

Usage:
    python scripts/07_align_key.py --key 9 --with 5 --direction up
    python scripts/07_align_key.py --key SW17 --with Key21 --direction left [--dry-run]

--direction picks which axis to align on, not a literal direction with a
distance - up and down both mean "match Y (vertical alignment)"; left and
right both mean "match X (horizontal alignment)". The actual sign/distance
of the move is computed automatically from the two keys' current switch
positions, then applied as a pure translation (position only, no rotation
change) to the target key's switch, diode, and connecting trace - same
approach as 06_move_key.py.

Alignment is based on the two keys' SWITCH positions. Skips (reported, not
silently) if the target key's switch or diode footprint is locked.
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

AXIS_BY_DIRECTION = {"up": "y", "down": "y", "left": "x", "right": "x"}


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
    parser.add_argument("--key", required=True, help="Key to move, e.g. '9', 'SW09', 'Key09'")
    parser.add_argument("--with", dest="reference", required=True,
                         help="Key to align with (stays put), e.g. '5', 'SW05', 'Key05'")
    parser.add_argument("--direction", required=True, choices=sorted(AXIS_BY_DIRECTION),
                         help="up/down = match Y (vertical); left/right = match X (horizontal)")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    axis = AXIS_BY_DIRECTION[args.direction]
    target_num = normalize_key(args.key)
    ref_num = normalize_key(args.reference)

    pcb_text = read_text(PCB_PATH)
    footprints = parse_footprints(pcb_text)
    segments = parse_segments(pcb_text)

    sw_ref, dm_ref = f"SW{target_num}", f"DM{target_num}"
    ref_sw_ref = f"SW{ref_num}"

    for ref in (sw_ref, dm_ref, ref_sw_ref):
        if ref not in footprints:
            sys.exit(f"ERROR: {ref} not found on board")

    sw_fp = footprints[sw_ref]
    dm_fp = footprints[dm_ref]
    ref_sw_fp = footprints[ref_sw_ref]

    if sw_fp.locked or dm_fp.locked:
        sys.exit(f"Key{target_num} is locked (switch or diode) - not moving. "
                 f"Unlock it first if this is intentional.")

    tx, ty = float(sw_fp.at_match.group(1)), float(sw_fp.at_match.group(2))
    rx, ry = float(ref_sw_fp.at_match.group(1)), float(ref_sw_fp.at_match.group(2))

    if axis == "y":
        dx, dy = 0.0, ry - ty
    else:
        dx, dy = rx - tx, 0.0

    edits = []
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

    axis_word = "vertically (Y)" if axis == "y" else "horizontally (X)"
    print(f"Aligning Key{target_num} with Key{ref_num} {axis_word}: "
          f"moving ({fmt(dx)}, {fmt(dy)}) mm")

    if args.dry_run:
        print("Dry run: no changes written.")
        return

    write_text(PCB_PATH, apply_edits(pcb_text, edits))
    print(f"Wrote changes to {PCB_PATH.name}")


if __name__ == "__main__":
    main()
