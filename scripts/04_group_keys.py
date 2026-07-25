#!/usr/bin/env python3
"""Group each SW0N/DM0N pair (plus their connecting trace segments) into a
named PCB group "KeyNN", matching the existing SW01/DM01 grouping.

Usage:
    python scripts/04_group_keys.py [--dry-run]

Renames the existing (unnamed) group containing SW01/DM01 to "Key01", and
creates a new named group for each of SW02..SW24 - each group's members are
that key's switch footprint, its diode footprint, and every trace segment
on that diode's anode net (the short switch<->diode connection). Keys that
already have a group are left untouched and reported as skipped.
"""
import argparse
import re
import sys
import uuid
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PCB_PATH = ROOT / "ErgonomicGamepad.kicad_pcb"

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


def footprint_uuids(pcb_text: str) -> dict:
    """reference -> footprint uuid"""
    by_ref = {}
    for start, end in iter_blocks(pcb_text, r'\(footprint\s+"'):
        block = pcb_text[start:end + 1]
        ref_m = REFERENCE_RE.search(block)
        uuid_m = UUID_RE.search(block)
        if ref_m and uuid_m:
            by_ref[ref_m.group(1)] = uuid_m.group(1)
    return by_ref


def segment_uuids_by_net(pcb_text: str) -> dict:
    """net name -> list of segment uuids"""
    by_net = {}
    for start, end in iter_blocks(pcb_text, r"\(segment\b"):
        block = pcb_text[start:end + 1]
        net_m = NET_RE.search(block)
        uuid_m = UUID_RE.search(block)
        if net_m and uuid_m:
            by_net.setdefault(net_m.group(1), []).append(uuid_m.group(1))
    return by_net


def existing_groups(pcb_text: str):
    """list of (start, end, name, name_start, name_end, members: set[str])"""
    groups = []
    for start, end in iter_blocks(pcb_text, r"\(group\b"):
        block = pcb_text[start:end + 1]
        name_m = re.match(r'\(group\s+"([^"]*)"', block)
        members_m = re.search(r"\(members((?:\s+\"[^\"]+\")+)\s*\)", block)
        members = set(re.findall(r'"([^"]+)"', members_m.group(1))) if members_m else set()
        groups.append({
            "start": start, "end": end,
            "name": name_m.group(1) if name_m else "",
            "name_start": start + name_m.start(1),
            "name_end": start + name_m.end(1),
            "members": members,
        })
    return groups


def apply_edits(text: str, edits: list) -> str:
    for start, end, new_text in sorted(edits, key=lambda e: e[0], reverse=True):
        text = text[:start] + new_text + text[end:]
    return text


def main():
    parser = argparse.ArgumentParser(description=__doc__,
                                      formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    pcb_text = read_text(PCB_PATH)
    fp_uuids = footprint_uuids(pcb_text)
    seg_by_net = segment_uuids_by_net(pcb_text)
    groups = existing_groups(pcb_text)

    edits = []
    new_group_text = []
    renamed, created, skipped_existing, missing = [], [], [], []

    for n in range(1, 25):
        key = f"Key{n:02d}"
        sw_ref, dm_ref = f"SW{n:02d}", f"DM{n:02d}"
        net = f"Net-(DM{n:02d}-A)"

        if sw_ref not in fp_uuids or dm_ref not in fp_uuids:
            missing.append(key)
            continue

        member_uuids = {fp_uuids[sw_ref], fp_uuids[dm_ref]}
        member_uuids.update(seg_by_net.get(net, []))

        existing = next((g for g in groups if member_uuids & g["members"]), None)
        if existing is not None:
            if existing["name"] == key:
                skipped_existing.append(key)
                continue
            if existing["name"] == "":
                edits.append((existing["name_start"], existing["name_end"], key))
                renamed.append(key)
                continue
            skipped_existing.append(f"{key} (already named {existing['name']!r})")
            continue

        members_str = " ".join(f'"{u}"' for u in sorted(member_uuids))
        new_group_text.append(
            f'\t(group "{key}"\r\n'
            f'\t\t(uuid "{uuid.uuid4()}")\r\n'
            f'\t\t(members {members_str})\r\n'
            f'\t)\r\n'
        )
        created.append(key)

    print(f"Renamed (untitled -> named): {', '.join(renamed) or '(none)'}")
    print(f"Created {len(created)}: {', '.join(created) or '(none)'}")
    if skipped_existing:
        print(f"Skipped (already grouped/named): {', '.join(skipped_existing)}")
    if missing:
        print(f"Missing footprints, skipped: {', '.join(missing)}")

    if args.dry_run:
        print("Dry run: no changes written.")
        return

    new_text = apply_edits(pcb_text, edits)
    if new_group_text:
        marker = "\t(embedded_fonts no)\r\n)\r\n"
        insert = "".join(new_group_text) + marker
        if marker not in new_text:
            sys.exit("ERROR: could not find end-of-file marker to insert new groups")
        new_text = new_text.replace(marker, insert, 1)

    write_text(PCB_PATH, new_text)
    print(f"Wrote changes to {PCB_PATH.name}")


if __name__ == "__main__":
    main()
