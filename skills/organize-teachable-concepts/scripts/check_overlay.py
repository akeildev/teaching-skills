#!/usr/bin/env python3
"""Check an inventory/overlay pair for accounting and reference integrity.

Usage: check_overlay.py inventory.json overlay.json [--source source.md]
Exits 1 on any failure. A pass says nothing about teaching quality or recall.
"""
import argparse
import json
import re
import sys
from collections import Counter


def load(path):
    with open(path, encoding="utf-8") as handle:
        return json.load(handle)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("inventory")
    parser.add_argument("overlay")
    parser.add_argument("--source", help="source snapshot; evidence text is matched against it")
    parser.add_argument("--addendum", help="versioned additions kept apart from the inventory")
    args = parser.parse_args()

    inventory, overlay = load(args.inventory), load(args.overlay)
    if args.addendum:
        addendum = load(args.addendum)
        for key, value in addendum.items():
            if isinstance(value, list):
                inventory.setdefault(key, []).extend(value)
    fails, notes = [], []

    records = inventory.get("units", inventory.get("records", []))
    record_ids = {r["id"] for r in records}
    activity_ids = {a["id"] for a in inventory.get("activities", [])}
    review_ids = {r["id"] for r in inventory.get("review_queue", [])}
    gap_ids = {g["id"] for g in inventory.get("missing_prerequisites", [])}
    units = {u["id"]: u for u in overlay["teaching_units"]}

    placed = {p["record_id"] for p in overlay.get("placements", [])}
    if placed != record_ids:
        fails.append(f"placements differ from records: missing {sorted(record_ids - placed)}, unknown {sorted(placed - record_ids)}")

    for placement in overlay.get("placements", []):
        unit_id = placement.get("unit_id")
        if placement.get("role") not in ("unresolved", "course_level") and unit_id not in units:
            fails.append(f"placement of {placement['record_id']} points at unknown unit {unit_id}")

    for family in overlay["families"]:
        for unit_id in family["unit_ids"]:
            if unit_id not in units:
                fails.append(f"family {family['id']} lists unknown unit {unit_id}")
    in_family = Counter(u for f in overlay["families"] for u in f["unit_ids"])
    for unit_id in units:
        if in_family[unit_id] != 1:
            fails.append(f"unit {unit_id} appears in {in_family[unit_id]} families")

    for unit_id, unit in units.items():
        if not unit.get("target") or not unit.get("success_check"):
            fails.append(f"unit {unit_id} lacks a target or success check")
        for field in ("component_record_ids", "supporting_record_ids"):
            for record_id in unit.get(field, []):
                if record_id not in record_ids:
                    fails.append(f"unit {unit_id} references unknown record {record_id}")
        for field, known in (("activity_ids", activity_ids), ("review_ids", review_ids), ("gap_ids", gap_ids)):
            for item in unit.get(field, []):
                if item not in known:
                    fails.append(f"unit {unit_id} references unknown {field[:-4]} {item}")

    attached = {a["activity_id"] for a in overlay.get("activity_attachments", [])}
    unresolved_activities = {a.get("activity_id") for a in overlay.get("unresolved_activities", [])}
    if activity_ids - attached - unresolved_activities:
        fails.append(f"activities without attachment: {sorted(activity_ids - attached - unresolved_activities)}")
    for attachment in overlay.get("activity_attachments", []):
        if attachment["activity_id"] not in activity_ids:
            fails.append(f"attachment of unknown activity {attachment['activity_id']}")
        if attachment.get("unit_id") not in units:
            fails.append(f"activity {attachment['activity_id']} attached to unknown unit {attachment.get('unit_id')}")

    for need in overlay.get("unresolved_teaching_needs", []):
        for record_id in need.get("record_ids", []):
            if record_id not in record_ids:
                fails.append(f"teaching need {need['id']} references unknown record {record_id}")
        if need.get("id") in units:
            fails.append(f"teaching need {need['id']} is counted as a unit")

    for migration in overlay.get("unit_migrations", []):
        status = str(migration.get("status", ""))
        old_id = migration.get("old_id", migration.get("old_unit_id"))
        if status.startswith("retired") and old_id in units:
            fails.append(f"retired unit ID {old_id} was reused")

    if args.source:
        with open(args.source, encoding="utf-8") as handle:
            text = handle.read()
        lines = text.split("\n")
        accounted = {
            item.get("url")
            for key in ("activities", "figures", "resources")
            for item in inventory.get(key, [])
        }
        unaccounted = sorted(set(re.findall(r"\]\((https?://[^)\s]+)\)", text)) - accounted)
        if unaccounted:
            notes.append(f"{len(unaccounted)} source links have no individual disposition; attach them or list them in resources")
        for record in records:
            for evidence in record.get("evidence", []):
                span = lines[evidence["line_start"] - 1 : evidence["line_end"]]
                if evidence["exact_text"] not in "\n".join(span):
                    fails.append(f"evidence of {record['id']} does not match source lines {evidence['line_start']}-{evidence['line_end']}")

    print(f"records {len(record_ids)}, placed {len(placed)}, activities {len(activity_ids)}, "
          f"attachments {len(overlay.get('activity_attachments', []))}, "
          f"families {len(overlay['families'])}, units {len(units)}")
    for note in notes:
        print("NOTE:", note)
    for fail in fails:
        print("FAIL:", fail)
    print("PASS: accounting and references only" if not fails else f"{len(fails)} failures")
    sys.exit(1 if fails else 0)


if __name__ == "__main__":
    main()
