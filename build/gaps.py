"""
gaps.py -- Data-completeness audit for PocketOP-Database shards.

Run from the repo root with no arguments:
    python3 build/gaps.py

Writes build/gap-report.md and prints a short summary to the terminal.
"""

import json
import pathlib
import sys
from collections import defaultdict

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent
SHARD_DIRS = [
    "source/broadcast-lenses",
    "source/broadcast-details",
    "source/cine-lenses",
    "source/cine-details",
    "source/ptz-cameras",
    "source/ptz-details",
]
OUTPUT_FILE = REPO_ROOT / "build" / "gap-report.md"


def find_list_key(data):
    """Return the name and value of the single list-valued top-level key."""
    for key, value in data.items():
        if isinstance(value, list):
            return key, value
    return None, []


def collect_shards():
    """Return sorted list of shard paths across all target directories."""
    paths = []
    for d in SHARD_DIRS:
        target = REPO_ROOT / d
        if target.exists():
            paths.extend(sorted(target.rglob("*.json")))
    return paths


def relative_path(path):
    return str(path.relative_to(REPO_ROOT))


def scan_shards(shard_paths):
    """
    Scan every shard and return:
      - unconfirmed: list of dicts per finding
      - unknowns: list of dicts per finding
      - nulls: {rel_path: {field: count}}
    """
    unconfirmed = []
    unknowns = []
    nulls = defaultdict(lambda: defaultdict(int))

    for path in shard_paths:
        with open(path, encoding="utf-8") as fh:
            data = json.load(fh)

        _array_key, entries = find_list_key(data)
        if not entries:
            continue

        rel = relative_path(path)

        for entry in entries:
            entry_id = entry.get("id", "(no id)")
            sources = entry.get("sources")
            sources_is_dict = isinstance(sources, dict)

            for field, value in entry.items():
                if field in ("id", "sources", "webSources"):
                    continue

                # Section A: unconfirmed
                if sources_is_dict:
                    conf_key = f"{field}_confidence"
                    if sources.get(conf_key) == "unconfirmed":
                        source_desc = sources.get(field, "")
                        unconfirmed.append(
                            {
                                "shard": rel,
                                "id": entry_id,
                                "field": field,
                                "value": value,
                                "source_desc": source_desc,
                            }
                        )

                # Section B: unknown
                if value == "unknown":
                    source_note = ""
                    if sources_is_dict:
                        source_note = sources.get(field, "")
                    unknowns.append(
                        {
                            "shard": rel,
                            "id": entry_id,
                            "field": field,
                            "source_note": source_note,
                        }
                    )

                # Section C: nulls
                if value is None:
                    nulls[rel][field] += 1

    return unconfirmed, unknowns, nulls


def group_by_shard(items):
    """Group a list of dicts by their 'shard' key, preserving order."""
    groups = {}
    for item in items:
        shard = item["shard"]
        groups.setdefault(shard, []).append(item)
    return groups


def render_report(unconfirmed, unknowns, nulls, shard_count):
    lines = []

    total_unconfirmed = len(unconfirmed)
    total_unknowns = len(unknowns)
    total_nulls = sum(count for fields in nulls.values() for count in fields.values())

    lines.append("# PocketOP Database Gap Report")
    lines.append("")
    lines.append(
        f"Shards scanned: {shard_count} | "
        f"Unconfirmed values: {total_unconfirmed} | "
        f"Unknown values: {total_unknowns} | "
        f"Null occurrences: {total_nulls}"
    )
    lines.append("")

    # Section A
    lines.append("---")
    lines.append("")
    lines.append("## A. Unconfirmed Values")
    lines.append("")
    lines.append(
        "Fields flagged with `_confidence: unconfirmed` in the sources object. "
        "These are best-estimate values that need verification."
    )
    lines.append("")

    if not unconfirmed:
        lines.append("_No unconfirmed values found._")
        lines.append("")
    else:
        groups = group_by_shard(unconfirmed)
        for shard, items in groups.items():
            lines.append(f"### {shard}")
            lines.append("")
            lines.append("| Entry ID | Field | Current Value | Source Description |")
            lines.append("|---|---|---|---|")
            for item in items:
                val = str(item["value"]) if item["value"] is not None else "null"
                desc = item["source_desc"].replace("|", "\\|") if item["source_desc"] else ""
                lines.append(f"| {item['id']} | {item['field']} | {val} | {desc} |")
            lines.append("")

    # Section B
    lines.append("---")
    lines.append("")
    lines.append("## B. Unknown Values")
    lines.append("")
    lines.append(
        "Fields whose value is exactly `\"unknown\"`: investigated, but no source was found."
    )
    lines.append("")

    if not unknowns:
        lines.append("_No unknown values found._")
        lines.append("")
    else:
        groups = group_by_shard(unknowns)
        for shard, items in groups.items():
            lines.append(f"### {shard}")
            lines.append("")
            lines.append("| Entry ID | Field | Source Note |")
            lines.append("|---|---|---|")
            for item in items:
                note = item["source_note"].replace("|", "\\|") if item["source_note"] else ""
                lines.append(f"| {item['id']} | {item['field']} | {note} |")
            lines.append("")

    # Section C
    lines.append("---")
    lines.append("")
    lines.append("## C. Null Inventory")
    lines.append("")
    lines.append(
        "Count of null-valued fields per shard. "
        "Sorted by occurrence count, highest first. "
        "Policy judgement on which nulls are actionable belongs to Tim."
    )
    lines.append("")

    if not nulls:
        lines.append("_No null values found._")
        lines.append("")
    else:
        for shard in sorted(nulls.keys()):
            field_counts = nulls[shard]
            lines.append(f"### {shard}")
            lines.append("")
            lines.append("| Field | Null Count |")
            lines.append("|---|---|")
            for field, count in sorted(field_counts.items(), key=lambda x: -x[1]):
                lines.append(f"| {field} | {count} |")
            lines.append("")

    return "\n".join(lines) + "\n"


def main():
    shard_paths = collect_shards()
    shard_count = len(shard_paths)

    unconfirmed, unknowns, nulls = scan_shards(shard_paths)

    report = render_report(unconfirmed, unknowns, nulls, shard_count)
    OUTPUT_FILE.write_text(report, encoding="utf-8")

    total_unconfirmed = len(unconfirmed)
    total_unknowns = len(unknowns)
    total_nulls = sum(count for fields in nulls.values() for count in fields.values())

    print(f"Gap report written to {OUTPUT_FILE.relative_to(REPO_ROOT)}")
    print(f"  Shards scanned:     {shard_count}")
    print(f"  Unconfirmed values: {total_unconfirmed}")
    print(f"  Unknown values:     {total_unknowns}")
    print(f"  Null occurrences:   {total_nulls}")


if __name__ == "__main__":
    main()
