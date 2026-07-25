#!/usr/bin/env python3
"""Replicate the SW01/DM01 "key" template (diode position, rotation, and the
short connecting trace to the socket) onto SW02..SW24 / DM02..DM24, by
editing ErgonomicGamepad.kicad_pcb directly.

Usage:
    python scripts/03_apply_key_template.py [--dry-run]
    python scripts/03_apply_key_template.py --template SW01 --targets SW02,SW03 [--dry-run]

For each target key N:
    - Computes DM0N's (x, y, rotation) by taking DM01's position relative to
      SW01 in SW01's own local frame (so SW01's rotation is factored out),
      then re-applying that same local offset/rotation using SW0N's own
      position and rotation. This is a rigid-body transform, not a copy of
      absolute coordinates, so it works even if individual keys end up
      rotated differently on the board.
    - Skips repositioning DM0N if it is locked (reported, not silently
      skipped).
    - Some pads carry their own explicit rotation angle separate from the
      footprint's overall rotation (baked in by KiCad once a footprint has
      been rotated at least once). Those are recomputed fresh from the
      template's local (relative-to-footprint) pad angle on every run, so
      the copper pad shape always stays correctly aligned with the rotated
      body - this is done unconditionally, not as a delta, so it self-heals
      even if a pad's angle was already wrong on disk.
    - Replicates the routed trace segment(s) between SW01 pin 2 and DM01's
      anode pad as new segments between SW0N and DM0N, on that key's own
      anode net - but only if that net doesn't already have any routed
      copper, so re-running the script is safe and won't duplicate traces.

Only footprint positions/rotations and new trace segments are ever written.
Existing traces, other nets, and unrelated footprints are never touched.
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


class Footprint:
    def __init__(self, start, end, text):
        self.start = start
        self.end = end
        self.text = text
        ref_m = REFERENCE_RE.search(text)
        self.reference = ref_m.group(1) if ref_m else None
        self.locked = bool(re.search(r"\(locked\b", text))
        # The footprint's own (at ...) is the first (at ...) in the block,
        # before any pad/property sub-blocks.
        self.at_match = AT_RE.search(text)
        self.pad_nets = {}  # pad number -> net name
        # pad number -> (absolute at-match start, absolute at-match end, x, y, angle-or-None)
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
    """Top-level (segment ...) blocks, as dicts with start/end/width/layer/net."""
    segments = []
    for start, end in iter_blocks(pcb_text, r"\(segment\b"):
        block = pcb_text[start:end + 1]
        start_m = re.search(r"\(start\s+(-?[\d.]+)\s+(-?[\d.]+)\)", block)
        end_m = re.search(r"\(end\s+(-?[\d.]+)\s+(-?[\d.]+)\)", block)
        width_m = re.search(r"\(width\s+([\d.]+)\)", block)
        layer_m = re.search(r'\(layer\s+"([^"]*)"\)', block)
        net_m = NET_RE.search(block)
        if not (start_m and end_m and net_m):
            continue
        segments.append({
            "start": (float(start_m.group(1)), float(start_m.group(2))),
            "end": (float(end_m.group(1)), float(end_m.group(2))),
            "width": width_m.group(1) if width_m else "0.2",
            "layer": layer_m.group(1) if layer_m else "F.Cu",
            "net": net_m.group(1),
        })
    return segments


def routed_net_names(pcb_text: str) -> set:
    """Net names that already have copper (segments, arcs, or vias)."""
    nets = set()
    for pattern in (r"\(segment\b", r"\(arc\b", r"\(via\b"):
        for start, end in iter_blocks(pcb_text, pattern):
            net_m = NET_RE.search(pcb_text[start:end + 1])
            if net_m:
                nets.add(net_m.group(1))
    return nets


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
    # Match the file's existing style: integers without a decimal point,
    # otherwise up to 6 decimal places with no trailing zeros.
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


def pad_local_angles(template_fp: "Footprint", template_footprint_angle: float) -> dict:
    """For each of the template footprint's pads that carries its own explicit
    rotation, compute that rotation *relative to the footprint's own angle*
    (i.e. what the library's local, unrotated pad angle would be). Pads with
    no explicit angle aren't included - they auto-follow the footprint's
    rotation and never need a per-pad edit."""
    result = {}
    for num, (_, _, _, _, angle) in template_fp.pad_at.items():
        if angle is None:
            continue
        result[num] = normalize_angle(float(angle) - template_footprint_angle)
    return result


def pad_angle_edits(target_fp: "Footprint", new_footprint_angle: float, local_angles: dict) -> list:
    """Set each pad's absolute angle to (new_footprint_angle + its template-derived
    local angle), overwriting whatever was previously stored - correct regardless
    of whether the existing value was already stale."""
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


def key_number(ref: str) -> str:
    m = re.match(r"[A-Za-z]+(\d+)", ref)
    return m.group(1) if m else None


def main():
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--dry-run", action="store_true",
                         help="Report what would change without writing")
    parser.add_argument("--template", default="SW01",
                         help="Reference designator of the template switch (default: SW01)")
    parser.add_argument("--targets", default=None,
                         help="Comma-separated switch references to update "
                              "(default: SW02..SW24)")
    args = parser.parse_args()

    template_num = key_number(args.template)
    if args.targets:
        targets = [t.strip() for t in args.targets.split(",")]
    else:
        targets = [f"SW{n:02d}" for n in range(1, 25) if f"{n:02d}" != template_num]

    pcb_text = read_text(PCB_PATH)
    footprints = parse_footprints(pcb_text)
    segments = parse_segments(pcb_text)
    already_routed = routed_net_names(pcb_text)

    sw_tpl_ref = args.template
    dm_tpl_ref = f"DM{template_num}"

    if sw_tpl_ref not in footprints or dm_tpl_ref not in footprints:
        sys.exit(f"ERROR: template footprints {sw_tpl_ref}/{dm_tpl_ref} not found on board")

    sw_tpl = footprints[sw_tpl_ref]
    dm_tpl = footprints[dm_tpl_ref]
    sx, sy, sa = (float(v) if v else 0.0 for v in
                  (sw_tpl.at_match.group(1), sw_tpl.at_match.group(2), sw_tpl.at_match.group(3) or "0"))
    dx, dy, da = (float(v) if v else 0.0 for v in
                  (dm_tpl.at_match.group(1), dm_tpl.at_match.group(2), dm_tpl.at_match.group(3) or "0"))

    # DM position relative to SW, expressed in SW's own local (unrotated) frame.
    local_offset = rotate((dx - sx, dy - sy), -sa)
    local_rot_delta = da - sa
    dm_pad_local_angles = pad_local_angles(dm_tpl, da)

    tpl_anode_net = dm_tpl.pad_nets.get("2")
    if not tpl_anode_net:
        sys.exit(f"ERROR: could not determine {dm_tpl_ref} pad 2 (anode) net")

    tpl_segments = [s for s in segments if s["net"] == tpl_anode_net]
    if not tpl_segments:
        print(f"WARNING: no routed trace found on {tpl_anode_net} - only "
              f"repositioning diodes, no traces will be replicated", file=sys.stderr)

    # Template trace geometry, in SW's local (unrotated) frame.
    local_segments = []
    for seg in tpl_segments:
        local_segments.append({
            "start": rotate((seg["start"][0] - sx, seg["start"][1] - sy), -sa),
            "end": rotate((seg["end"][0] - sx, seg["end"][1] - sy), -sa),
            "width": seg["width"],
            "layer": seg["layer"],
        })

    edits = []
    new_segment_text = []
    moved, skipped_locked_pos, traced, skipped_routed_trace, missing = [], [], [], [], []

    for sw_ref in targets:
        num = key_number(sw_ref)
        dm_ref = f"DM{num}"
        if sw_ref not in footprints or dm_ref not in footprints:
            missing.append(sw_ref)
            continue

        sw_fp = footprints[sw_ref]
        dm_fp = footprints[dm_ref]
        nsx, nsy, nsa = (float(v) if v else 0.0 for v in
                         (sw_fp.at_match.group(1), sw_fp.at_match.group(2), sw_fp.at_match.group(3) or "0"))

        if dm_fp.locked:
            skipped_locked_pos.append(dm_ref)
        else:
            off = rotate(local_offset, nsa)
            new_x, new_y = nsx + off[0], nsy + off[1]
            new_angle = nsa + local_rot_delta
            new_at = format_at(new_x, new_y, new_angle)
            edits.append((dm_fp.start + dm_fp.at_match.start(),
                          dm_fp.start + dm_fp.at_match.end(), new_at))
            # Pads with their own explicit rotation (baked in by KiCad once a
            # footprint has been rotated) don't auto-follow the footprint's
            # own rotation - recompute each one's absolute angle fresh from
            # the template's local (relative-to-footprint) angle, rather than
            # patching whatever value happens to already be on disk.
            edits.extend(pad_angle_edits(dm_fp, normalize_angle(new_angle), dm_pad_local_angles))
            moved.append(dm_ref)

        key_anode_net = dm_fp.pad_nets.get("2")
        if not key_anode_net:
            continue
        if key_anode_net in already_routed:
            skipped_routed_trace.append(dm_ref)
            continue
        if not local_segments:
            continue

        for seg in local_segments:
            abs_start = rotate(seg["start"], nsa)
            abs_end = rotate(seg["end"], nsa)
            abs_start = (nsx + abs_start[0], nsy + abs_start[1])
            abs_end = (nsx + abs_end[0], nsy + abs_end[1])
            new_segment_text.append(
                "\t(segment\r\n"
                f"\t\t(start {fmt(abs_start[0])} {fmt(abs_start[1])})\r\n"
                f"\t\t(end {fmt(abs_end[0])} {fmt(abs_end[1])})\r\n"
                f"\t\t(width {seg['width']})\r\n"
                f"\t\t(layer \"{seg['layer']}\")\r\n"
                f"\t\t(net \"{key_anode_net}\")\r\n"
                f"\t\t(uuid \"{uuid.uuid4()}\")\r\n"
                "\t)\r\n"
            )
        traced.append(dm_ref)

    print(f"Template: {sw_tpl_ref}/{dm_tpl_ref} -> offset {local_offset}, "
          f"rotation delta {round(local_rot_delta, 3)} deg, "
          f"{len(local_segments)} trace segment(s)")
    print(f"Repositioned {len(moved)}: {', '.join(moved) or '(none)'}")
    if skipped_locked_pos:
        print(f"Skipped positioning (locked): {', '.join(skipped_locked_pos)}")
    print(f"Added traces for {len(traced)}: {', '.join(traced) or '(none)'}")
    if skipped_routed_trace:
        print(f"Skipped tracing (net already routed): {', '.join(skipped_routed_trace)}")
    if missing:
        print(f"Missing footprints, skipped entirely: {', '.join(missing)}")

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
