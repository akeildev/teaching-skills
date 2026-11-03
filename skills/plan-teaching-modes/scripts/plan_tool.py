#!/usr/bin/env python3
"""Check a teaching-mode plan's references, or render its readable view.

Usage:
  plan_tool.py check PLAN --hierarchy overlay.json --inventory inventory.json
  plan_tool.py render PLAN --hierarchy overlay.json --inventory inventory.json --out view.md

PLAN is a JSON file or a directory of JSON parts. check exits 1 on any failure.
It verifies connections only; it cannot tell whether the plan teaches.
A plan is lessons -> items in teaching order -> each item's modes with a one-line job.
An item is a unit ("unit": "TU-01") or a course-level item ("course": "Opener").
"""
import argparse
import glob
import json
import os
import sys

CATALOG = {
    "Hook", "Big question", "Objectives", "Definition", "Concept", "Model/diagram", "Process",
    "Timeline", "Comparison", "Analogy", "Worked example", "Case study", "Interactive question",
    "Practice", "Reflection", "Teach-it", "Summary", "Memory anchor", "Study sheet", "Animated scene",
}
LIST_KEYS = ("lessons", "left_out", "added_modes", "questions_for_user", "format_suggestions")
TREATMENTS = ("explains", "practices", "assesses")


def load_json(path):
    with open(path, encoding="utf-8") as handle:
        return json.load(handle)


def load_plan(path):
    if not os.path.isdir(path):
        return load_json(path)
    plan = {}
    for part in sorted(glob.glob(os.path.join(path, "*.json"))):
        for key, value in load_json(part).items():
            if key in LIST_KEYS:
                plan.setdefault(key, []).extend(value)
            else:
                plan[key] = value
    return plan


def load_context(args):
    hierarchy, inventory = load_json(args.hierarchy), load_json(args.inventory)
    if args.addendum:
        for key, value in load_json(args.addendum).items():
            if isinstance(value, list):
                inventory.setdefault(key, []).extend(value)
    records = {r["id"]: r for r in inventory.get("units", inventory.get("records", []))}
    return hierarchy, inventory, records


def items_of(plan):
    return [item for lesson in plan.get("lessons", []) for item in lesson.get("items", [])]


def item_name(item):
    return item.get("unit") or item.get("course") or "?"


def covered_by(mode):
    return [r for field in TREATMENTS for r in mode.get(field, [])]


def attached_exercises(hierarchy, unit_id, h_unit):
    attached = set(h_unit.get("activity_ids", []))
    attached |= {a["activity_id"] for a in hierarchy.get("activity_attachments", []) if a.get("unit_id") == unit_id}
    return attached


def fmt_minutes(value):
    return f"{value:g}" if isinstance(value, (int, float)) else str(value)


def check(plan, hierarchy, inventory, records):
    fails, notes = [], []
    h_units = {u["id"]: u for u in hierarchy["teaching_units"]}
    known_modes = CATALOG | {m["name"] for m in plan.get("added_modes", [])}
    known_activities = {a["id"] for a in inventory.get("activities", [])}
    items = items_of(plan)

    # Every unit appears exactly once: as an item or in left_out.
    unit_items = {}
    for item in items:
        if bool(item.get("unit")) == bool(item.get("course")):
            fails.append(f"item {item_name(item)} must have exactly one of 'unit' or 'course'")
        if item.get("unit"):
            unit_items.setdefault(item["unit"], []).append(item)
    left_out = {}
    for entry in plan.get("left_out", []):
        left_out.setdefault(entry.get("unit"), []).append(entry)
        if not entry.get("reason", "").strip():
            fails.append(f"left-out unit {entry.get('unit')} has no reason")
    for unit_id in sorted(set(unit_items) | set(left_out), key=str):
        if unit_id not in h_units:
            fails.append(f"unknown unit {unit_id}")
            continue
        count = len(unit_items.get(unit_id, [])) + len(left_out.get(unit_id, []))
        if count > 1:
            fails.append(f"{unit_id} appears {count} times (items and left_out together)")
    for unit_id in sorted(set(h_units) - set(unit_items) - set(left_out)):
        fails.append(f"{unit_id} is neither a lesson item nor left out")

    # Modes, record references, exercises.
    covered, used_exercises = set(), set()
    for item in items:
        where = item_name(item)
        modes = item.get("modes", [])
        if not modes:
            fails.append(f"{where} has no modes")
        for number, mode in enumerate(modes, 1):
            if not mode.get("mode", "").strip():
                fails.append(f"{where} mode {number} has no name")
            elif mode["mode"] not in known_modes:
                notes.append(f"{where}: mode '{mode['mode']}' is not in the catalog or added_modes")
            if not mode.get("job", "").strip():
                fails.append(f"{where} mode {number} ({mode.get('mode', '?')}) has no job")
            for record_id in covered_by(mode):
                if record_id not in records:
                    fails.append(f"{where}: unknown record {record_id}")
            covered |= set(covered_by(mode))
        for exercise in item.get("exercises", []):
            activity_id = exercise.get("activity_id")
            if activity_id not in known_activities:
                fails.append(f"{where}: unknown activity {activity_id}")
            if not exercise.get("use", "").strip():
                fails.append(f"{where}: exercise {activity_id} has no use")
            else:
                used_exercises.add(activity_id)
        for entry in item.get("left_out_components", []):
            if entry.get("record") not in records:
                fails.append(f"{where}: unknown left-out record {entry.get('record')}")
            if not entry.get("reason", "").strip():
                fails.append(f"{where}: left-out component {entry.get('record')} has no reason")

    # Per placed unit: components accounted for, exercises used, something practised or assessed.
    sequences = {}
    for unit_id, unit_item_list in unit_items.items():
        if unit_id not in h_units:
            continue
        h_unit, item = h_units[unit_id], unit_item_list[0]
        components = h_unit["component_record_ids"]
        excused = {e.get("record") for e in item.get("left_out_components", []) if e.get("reason", "").strip()}
        missing = [r for r in components if r not in covered | excused]
        if missing:
            fails.append(f"{unit_id} components not explained, practised or assessed anywhere, nor left out: {missing}")
        for activity_id in sorted(attached_exercises(hierarchy, unit_id, h_unit) - used_exercises):
            fails.append(f"{unit_id} source exercise {activity_id} is not used in any item")
        own = any(m.get("practices") or m.get("assesses") for m in item.get("modes", []))
        elsewhere = any(set(m.get("practices", []) + m.get("assesses", [])) & set(components)
                        for i in items for m in i.get("modes", []))
        if not (own or elsewhere):
            notes.append(f"{unit_id}: no mode practises or assesses it")
        sequence = []
        for mode in item.get("modes", []):
            if not sequence or sequence[-1] != mode.get("mode"):
                sequence.append(mode.get("mode"))
        sequences.setdefault(" → ".join(map(str, sequence)), []).append(unit_id)

    for lesson in plan.get("lessons", []):
        minutes = [item.get("minutes") for item in lesson.get("items", [])]
        if lesson.get("minutes") is not None and minutes and None not in minutes:
            total = sum(minutes)
            if abs(total - lesson["minutes"]) > 1e-9:
                notes.append(f"{lesson.get('id')} is {fmt_minutes(lesson['minutes'])} minutes "
                             f"but its items add up to {fmt_minutes(total)}")

    for shape, unit_ids in sequences.items():
        if len(unit_ids) > 1 and shape:
            notes.append(f"{', '.join(unit_ids)} share the mode sequence {shape}; read them together")

    summary = (f"lessons {len(plan.get('lessons', []))}, items {len(items)}, "
               f"units placed {len(unit_items)}, units left out {len(left_out)}")
    return summary, fails, notes


def unit_label(h_unit):
    return h_unit.get("label") or h_unit.get("title") or h_unit.get("target", "")


def render(plan, hierarchy, path):
    h_units = {u["id"]: u for u in hierarchy["teaching_units"]}
    out = [f"# {plan.get('title', 'Teaching plan')}", ""]
    summary = plan.get("brief", {}).get("summary")
    if summary:
        out += [f"**For:** {summary}", ""]
    if plan.get("main_point"):
        out += [f"**Main point:** {plan['main_point']}", ""]

    for lesson in plan.get("lessons", []):
        minutes = f" ({fmt_minutes(lesson['minutes'])} min)" if lesson.get("minutes") is not None else ""
        out += [f"## {lesson.get('id', '')} · {lesson.get('title', '')}{minutes}", ""]
        for item in lesson.get("items", []):
            item_minutes = f" ({fmt_minutes(item['minutes'])} min)" if item.get("minutes") is not None else ""
            if item.get("unit"):
                label = unit_label(h_units.get(item["unit"], {}))
                out.append(f"**{item['unit']} · {label}**{item_minutes}")
            else:
                out.append(f"**{item.get('course', '')}**{item_minutes}")
            out.append("")
            for number, mode in enumerate(item.get("modes", []), 1):
                tags = " ".join(f"`{r}`" for r in dict.fromkeys(covered_by(mode)))
                out.append(f"{number}. **{mode.get('mode', '')}:** {mode.get('job', '')}" + (f" {tags}" if tags else ""))
            extras = [f"- Exercise {e.get('activity_id')}: {e.get('use', '')}" for e in item.get("exercises", [])]
            extras += [f"- Left out {e.get('record')}: {e.get('reason', '')}" for e in item.get("left_out_components", [])]
            if item.get("note"):
                extras.append(f"- Note: {item['note']}")
            if extras:
                out.append("")
                out += extras
            out.append("")

    if plan.get("left_out"):
        out += ["## Left out", ""]
        for entry in plan["left_out"]:
            label = unit_label(h_units.get(entry.get("unit"), {}))
            out.append(f"- **{entry.get('unit')} · {label}:** {entry.get('reason', '')}")
        out.append("")

    if plan.get("questions_for_user"):
        out += ["## Questions for you", ""]
        for number, question in enumerate(plan["questions_for_user"], 1):
            about = f" ({question['about']})" if question.get("about") else ""
            out.append(f"{number}. **{question.get('id', '')}{about}:** {question.get('question', '')}")
            if question.get("options"):
                out.append(f"   - Options: {'; '.join(question['options'])}")
            if question.get("meanwhile"):
                out.append(f"   - Meanwhile: {question['meanwhile']}")
        out.append("")

    if plan.get("added_modes"):
        out += ["## Added modes", ""]
        out += [f"- **{m['name']}:** {m.get('definition', '')}" for m in plan["added_modes"]]
        out.append("")

    out.append("Components and evidence: see the organize outline.")
    with open(path, "w", encoding="utf-8") as handle:
        handle.write("\n".join(out) + "\n")


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("command", choices=("check", "render"))
    parser.add_argument("plan")
    parser.add_argument("--hierarchy", required=True)
    parser.add_argument("--inventory", required=True)
    parser.add_argument("--addendum", help="versioned additions kept apart from the inventory")
    parser.add_argument("--out", help="output path for render")
    args = parser.parse_args()

    plan = load_plan(args.plan)
    hierarchy, inventory, records = load_context(args)
    if args.command == "render":
        render(plan, hierarchy, args.out or "view.md")
        print("wrote", args.out or "view.md")
        return

    summary, fails, notes = check(plan, hierarchy, inventory, records)
    print(summary)
    for note in notes:
        print("NOTE:", note)
    for fail in fails:
        print("FAIL:", fail)
    print("PASS: references only; read the plan to judge teaching" if not fails else f"{len(fails)} failures")
    sys.exit(1 if fails else 0)


if __name__ == "__main__":
    main()
