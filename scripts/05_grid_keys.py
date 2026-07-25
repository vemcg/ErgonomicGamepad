#!/usr/bin/env python3
"""Arrange all 24 keys (SW01..SW24 + DM01..DM24 + their connecting traces)
into a uniform grid, on a configurable pitch (default 20mm), by editing
ErgonomicGamepad.kicad_pcb directly.

Usage:
    python scripts/05_grid_keys.py [--dry-run]
    python scripts/05_grid_keys.py --pitch 20 [--dry-run]

Column/row mapping matches the existing matrix numbering (confirmed from
the netlist): key N belongs to column (N-1)//4 + 1, row (N-1)%4 + 1 - i.e.
SW01-SW04 are column 1 (rows 1-4), SW05-SW08 are column 2, etc. Column
increases with X, row increases with Y, matching the board's existing
orientation. The grid's column-1/row-1 anchor is SW01's current position,
so the whole grid regenerates in roughly the same place on the board.

For each of the 24 keys:
    - SW0N is moved to its grid position and forced to 0 degrees rotation
      (a clean, uniformly-oriented grid).
    - DM0N's position/rotation is recomputed from the SW01/DM01 template
      relationship (captured before any moves), same approach as
      03_apply_key_template.py, including the per-pad angle fix for pads
      that carry their own explicit rotation.
    - The 3 connecting trace segments between SW0N and DM0N are deleted
      and redrawn from the template's local geometry at the new position.
    - The KeyNN group's member list is updated to point at the new segment
      UUIDs (the footprint UUIDs don't change, since footprints are moved
      in place, not recreated).

Skips repositioning any key whose switch or diode footprint is locked
(reported, not silently skipped), leaving its traces/group untouched too.
"""
import argparse
import math
import re
import sys
import uuid
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PCB_PATH = ROOT / "ErgonomicGamepad.kicad_pcb"

AT_RE = re.compile(r"\(at\s+(-?[\d.]+)\s+(-?[\d.]+)(?:\s+(-?[\d.]+))?\s*\)")
REFERENCE_RE = re.compile(r'\(property "Reference" "([^"]*)"')
NET_RE = re.compile(r'\(net\s+"([^"]*)"\)')
UUID_RE = re.compile(r'\(uuid\s+"([^"]+)"\)')


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


def rotate(pt, angle_deg):
    x, y = pt
    a = math.radians(angle_deg)
    ca, sa = math.cos(a), math.sin(a)
    return (x * ca - y * sa, x * sa + y * ca)


def normalize_angle(a):
    a = a % 360.0
    if a > 180.0:
        a -= 360.0
    return round(a, 6)


def fmt(n):
    r = round(n, 6)
    if abs(r - round(r)) < 1e-9:
        return str(int(round(r)))
    s = f"{r:.6f}".rstrip("0").rstrip(".")
    return s


def format_at(x, y, angle):
    angle = normalize_angle(angle)
    if abs(angle) < 1e-9:
        return f"(at {fmt(x)} {fmt(y)})"
    return f"(at {fmt(x)} {fmt(y)} {fmt(angle)})"


class Footprint:
    def __init__(self, start, end, text):
        self.start = start
        self.end = end
        self.text = text
        ref_m = REFERENCE_RE.search(text)
        self.reference = ref_m.group(1) if ref_m else None
        self.locked = bool(re.search(r"\(locked\b", text))
        self.at_match = AT_RE.search(text)
        self.pad_nets = {}
        self.pad_at = {}
        for pstart, pend in iter_blocks(text, r"\(pad\b"):
            pad_text = text[pstart:pend + 1]
            num_m = re.match(r'\(pad\s+"([^"]*)"', pad_text)
            net_m = NET_RE.search(pad_text)
            if num_m and net_m:
                self.pad_nets[num_m.group(1)] = net_m.group(1)
            if num_m:
                at_m = AT_RE.search(pad_text)
                if at_m:
                    self.pad_at[num_m.group(1)] = (
                        start + pstart + at_m.start(), start + pstart + at_m.end(),
                        at_m.group(1), at_m.group(2), at_m.group(3),
                    )


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
        width_m = re.search(r"\(width\s+([\d.]+)\)", block)
        layer_m = re.search(r'\(layer\s+"([^"]*)"\)', block)
        net_m = NET_RE.search(block)
        uuid_m = UUID_RE.search(block)
        if not (start_m and end_m and net_m and uuid_m):
            continue
        segments.append({
            "block_start": start, "block_end": end,
            "start": (float(start_m.group(1)), float(start_m.group(2))),
            "end": (float(end_m.group(1)), float(end_m.group(2))),
            "width": width_m.group(1) if width_m else "0.2",
            "layer": layer_m.group(1) if layer_m else "F.Cu",
            "net": net_m.group(1),
            "uuid": uuid_m.group(1),
        })
    return segments


def parse_groups(pcb_text: str):
    groups = []
    for start, end in iter_blocks(pcb_text, r"\(group\b"):
        block = pcb_text[start:end + 1]
        name_m = re.match(r'\(group\s+"([^"]*)"', block)
        members_m = re.search(r"\(members((?:\s+\"[^\"]+\")+)\s*\)", block)
        if not members_m:
            continue
        groups.append({
            "name": name_m.group(1) if name_m else "",
            "members_start": start + members_m.start(1),
            "members_end": start + members_m.end(1),
            "members": re.findall(r'"([^"]+)"', members_m.group(1)),
        })
    return groups


def pad_local_angles(template_fp: Footprint, template_footprint_angle: float) -> dict:
    result = {}
    for num, (_, _, _, _, angle) in template_fp.pad_at.items():
        if angle is None:
            continue
        result[num] = normalize_angle(float(angle) - template_footprint_angle)
    return result


def pad_angle_edits(target_fp: Footprint, new_footprint_angle: float, local_angles: dict) -> list:
    edits = []
    for num, local_angle in local_angles.items():
        if num not in target_fp.pad_at:
            continue
        at_start, at_end, x, y, _ = target_fp.pad_at[num]
        new_angle = normalize_angle(new_footprint_angle + local_angle)
        new_at = f"(at {x} {y} {fmt(new_angle)})"
        edits.append((at_start, at_end, new_at))
    return edits


def apply_edits(text: str, edits: list) -> str:
    for start, end, new_text in sorted(edits, key=lambda e: e[0], reverse=True):
        text = text[:start] + new_text + text[end:]
    return text


def main():
    parser = argparse.ArgumentParser(description=__doc__,
                                      formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--pitch", type=float, default=20.0,
                         help="Grid pitch in mm, both axes (default: 20)")
    args = parser.parse_args()

    pcb_text = read_text(PCB_PATH)
    footprints = parse_footprints(pcb_text)
    segments = parse_segments(pcb_text)
    groups = parse_groups(pcb_text)

    if "SW01" not in footprints or "DM01" not in footprints:
        sys.exit("ERROR: template footprints SW01/DM01 not found on board")

    sw_tpl = footprints["SW01"]
    dm_tpl = footprints["DM01"]
    sx, sy, sa = (float(v) if v else 0.0 for v in
                  (sw_tpl.at_match.group(1), sw_tpl.at_match.group(2), sw_tpl.at_match.group(3) or "0"))
    dx, dy, da = (float(v) if v else 0.0 for v in
                  (dm_tpl.at_match.group(1), dm_tpl.at_match.group(2), dm_tpl.at_match.group(3) or "0"))

    local_offset = rotate((dx - sx, dy - sy), -sa)
    local_rot_delta = da - sa
    dm_pad_local_angles = pad_local_angles(dm_tpl, da)

    tpl_anode_net = dm_tpl.pad_nets.get("2")
    if not tpl_anode_net:
        sys.exit("ERROR: could not determine DM01 pad 2 (anode) net")

    tpl_segments = [s for s in segments if s["net"] == tpl_anode_net]
    if not tpl_segments:
        sys.exit(f"ERROR: no routed trace found on {tpl_anode_net} to use as the template")

    local_segments = []
    for seg in tpl_segments:
        local_segments.append({
            "start": rotate((seg["start"][0] - sx, seg["start"][1] - sy), -sa),
            "end": rotate((seg["end"][0] - sx, seg["end"][1] - sy), -sa),
            "width": seg["width"],
            "layer": seg["layer"],
        })

    # Anchor: grid column 1 / row 1 sits at SW01's current position.
    anchor_x, anchor_y = sx, sy
    pitch = args.pitch

    # edits: (start, end, replacement_text) - replacement_text == "" deletes.
    edits = []
    new_segment_text = []
    group_member_updates = {}  # (members_start, members_end) -> new members list

    moved, skipped_locked, missing = [], [], []

    for n in range(1, 25):
        sw_ref, dm_ref = f"SW{n:02d}", f"DM{n:02d}"
        if sw_ref not in footprints or dm_ref not in footprints:
            missing.append(sw_ref)
            continue

        sw_fp = footprints[sw_ref]
        dm_fp = footprints[dm_ref]

        if sw_fp.locked or dm_fp.locked:
            skipped_locked.append(sw_ref)
            continue

        col = (n - 1) // 4 + 1
        row = (n - 1) % 4 + 1
        gx = anchor_x + (col - 1) * pitch
        gy = anchor_y + (row - 1) * pitch

        # Switch: moved to grid position, forced to 0 degrees.
        new_sw_at = format_at(gx, gy, 0.0)
        edits.append((sw_fp.start + sw_fp.at_match.start(),
                      sw_fp.start + sw_fp.at_match.end(), new_sw_at))

        # Diode: template offset/rotation applied relative to the new (0 deg) switch.
        off = rotate(local_offset, 0.0)
        new_dx, new_dy = gx + off[0], gy + off[1]
        new_dangle = 0.0 + local_rot_delta
        new_dm_at = format_at(new_dx, new_dy, new_dangle)
        edits.append((dm_fp.start + dm_fp.at_match.start(),
                      dm_fp.start + dm_fp.at_match.end(), new_dm_at))
        edits.extend(pad_angle_edits(dm_fp, normalize_angle(new_dangle), dm_pad_local_angles))

        # Traces: delete the old ones on this key's anode net, draw fresh ones.
        key_anode_net = dm_fp.pad_nets.get("2")
        old_uuids = []
        if key_anode_net:
            for seg in segments:
                if seg["net"] == key_anode_net:
                    edits.append((seg["block_start"], seg["block_end"] + 1, ""))
                    old_uuids.append(seg["uuid"])

        new_uuids = []
        if key_anode_net:
            for seg in local_segments:
                abs_start = (gx + seg["start"][0], gy + seg["start"][1])
                abs_end = (gx + seg["end"][0], gy + seg["end"][1])
                new_uuid = str(uuid.uuid4())
                new_uuids.append(new_uuid)
                new_segment_text.append(
                    "\t(segment\r\n"
                    f"\t\t(start {fmt(abs_start[0])} {fmt(abs_start[1])})\r\n"
                    f"\t\t(end {fmt(abs_end[0])} {fmt(abs_end[1])})\r\n"
                    f"\t\t(width {seg['width']})\r\n"
                    f"\t\t(layer \"{seg['layer']}\")\r\n"
                    f"\t\t(net \"{key_anode_net}\")\r\n"
                    f"\t\t(uuid \"{new_uuid}\")\r\n"
                    "\t)\r\n"
                )

        # Update this key's group membership: swap old segment uuids for new ones.
        key_name = f"Key{n:02d}"
        for g in groups:
            if g["name"] == key_name:
                updated = [m for m in g["members"] if m not in old_uuids] + new_uuids
                group_member_updates[(g["members_start"], g["members_end"])] = updated

        moved.append(sw_ref)

    for (mstart, mend), updated in group_member_updates.items():
        # members_start/end span the captured (\s+"...")+ group, which begins
        # with the whitespace before the first quoted item - so the
        # replacement must include that leading space too.
        members_str = " " + " ".join(f'"{u}"' for u in updated)
        edits.append((mstart, mend, members_str))

    print(f"Grid pitch: {pitch}mm, anchor (col1/row1) at ({fmt(anchor_x)}, {fmt(anchor_y)})")
    print(f"Repositioned {len(moved)}: {', '.join(moved) or '(none)'}")
    if skipped_locked:
        print(f"Skipped (locked): {', '.join(skipped_locked)}")
    if missing:
        print(f"Missing footprints, skipped: {', '.join(missing)}")

    if args.dry_run:
        print("Dry run: no changes written.")
        return

    new_text = apply_edits(pcb_text, edits)
    if new_segment_text:
        marker = "\t(embedded_fonts no)\r\n)\r\n"
        insert = "".join(new_segment_text) + marker
        if marker not in new_text:
            sys.exit("ERROR: could not find end-of-file marker to insert new segments")
        new_text = new_text.replace(marker, insert, 1)

    write_text(PCB_PATH, new_text)
    print(f"Wrote changes to {PCB_PATH.name}")


if __name__ == "__main__":
    main()
