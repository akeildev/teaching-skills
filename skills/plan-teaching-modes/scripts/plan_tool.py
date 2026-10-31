#!/usr/bin/env python3
"""Check a teaching-mode plan's references, or render its family-first view.

Usage:
  plan_tool.py check PLAN --hierarchy overlay.json --inventory inventory.json
  plan_tool.py render PLAN --hierarchy overlay.json --inventory inventory.json --out view.md

PLAN is a JSON file or a directory of JSON parts. check exits 1 on any failure.
It verifies connections only; it cannot tell whether the content teaches.
"""
import argparse
import glob
import json
import os
import re
import sys
from collections import Counter

CATALOG = {
    "Hook", "Big question", "Objectives", "Definition", "Concept", "Model/diagram", "Process",
    "Timeline", "Comparison", "Analogy", "Worked example", "Case study", "Interactive question",
    "Practice", "Reflection", "Teach-it", "Summary", "Memory anchor", "Study sheet", "Animated scene",
}
LIST_KEYS = ("lessons", "sections", "units", "added_modes", "gaps", "proposed_hierarchy_changes",
             "questions_for_user", "format_suggestions")
TREATMENTS = ("explains", "practices", "assesses")
PLACEHOLDER = r"\{\{([^{}]+)\}\}"


def load_json(path):
    with open(path, encoding="utf-8") as handle:
        return json.load(handle)


def load_plan(path):
    if not os.path.isdir(path):
        return load_json(path)
    plan = {}
    for part in sorted(glob.glob(os.path.join(path, "*.json"))):
        data = load_json(part)
        for key, value in data.items():
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


def sequence(unit):
    modes = []
    for entry in unit.get("combination", []):
        if not modes or modes[-1] != entry["mode"]:
            modes.append(entry["mode"])
    return modes


def unit_records(hierarchy_unit):
    return hierarchy_unit["component_record_ids"], hierarchy_unit.get("supporting_record_ids", [])


def check(plan, hierarchy, inventory, records):
    fails, notes = [], []
    h_units = {u["id"]: u for u in hierarchy["teaching_units"]}
    sections = {s["id"]: s for s in plan.get("sections", [])}
    units = {u["id"]: u for u in plan.get("units", [])}
    modes = CATALOG | {m["name"] for m in plan.get("added_modes", [])}

    if len(sections) != len(plan.get("sections", [])):
        fails.append("duplicate section IDs")
    if len(units) != len(plan.get("units", [])):
        fails.append("duplicate unit entries")
    if set(units) != set(h_units):
        fails.append(f"plan units differ from hierarchy: missing {sorted(set(h_units) - set(units))}, unknown {sorted(set(units) - set(h_units))}")

    ordered = [s for lesson in plan.get("lessons", []) for s in lesson["section_ids"]]
    for section_id, count in Counter(ordered).items():
        if count > 1:
            fails.append(f"section {section_id} is ordered {count} times")
        if section_id not in sections:
            fails.append(f"lesson references unknown section {section_id}")
    for section_id in set(sections) - set(ordered):
        fails.append(f"section {section_id} is in no lesson")

    for section_id, section in sections.items():
        unit_ids = section.get("unit_ids", [])
        if not section.get("content", "").strip():
            fails.append(f"{section_id} has no content")
        if not unit_ids and not section.get("course_purpose"):
            fails.append(f"{section_id} has neither units nor a course purpose")
        for unit_id in unit_ids:
            used = any(e["section"] == section_id for e in units.get(unit_id, {}).get("combination", []))
            if not used:
                fails.append(f"{section_id} lists {unit_id}, but that unit's combination omits it")
        for activity in section.get("activities", []):
            if activity.get("origin") == "authored":
                for field in ("prompt", "success", "feedback"):
                    if not activity.get(field, "").strip():
                        fails.append(f"{section_id} authored activity {activity.get('id')} lacks {field}")
            elif activity.get("origin") == "source":
                if not activity.get("use", "").strip():
                    fails.append(f"{section_id} source activity {activity.get('activity_id')} lacks use")
            else:
                fails.append(f"{section_id} has an activity without a valid origin")
        keys = {activity_key(a) for a in section.get("activities", [])}
        for marker in re.findall(PLACEHOLDER, section.get("content", "")):
            if marker not in keys:
                fails.append(f"{section_id} places unknown activity {marker}")
        scene = section.get("scene")
        if scene:
            if not scene.get("teaching_point", "").strip() or not scene.get("beats"):
                fails.append(f"{section_id} scene lacks a teaching point or beats")
            for number, beat in enumerate(scene.get("beats", []), 1):
                if not beat.get("visual", "").strip() or not beat.get("narration", "").strip():
                    fails.append(f"{section_id} beat {number} lacks visual or narration")

    for unit_id, unit in units.items():
        if unit_id not in h_units:
            continue
        h_unit = h_units[unit_id]
        components, supporting = unit_records(h_unit)
        combination = unit.get("combination", [])
        if not unit.get("difficulty", "").strip():
            fails.append(f"{unit_id} has no difficulty statement")
        if len({e["mode"] for e in combination}) == 1 and not unit.get("single_mode_reason", "").strip():
            fails.append(f"{unit_id} uses one mode without a single_mode_reason")
        asked = json.dumps(plan.get("questions_for_user", []))
        if str(h_unit.get("readiness", "")).startswith("provisional") and unit_id not in asked:
            notes.append(f"{unit_id} is provisional and has no question for the user")
        covered = set()
        for entry in combination:
            where = f"{unit_id}/{entry.get('section')}"
            section = sections.get(entry.get("section"))
            if section is None:
                fails.append(f"{where}: unknown section")
                continue
            if entry.get("mode") == "Interactive question" and "{{" not in section.get("content", ""):
                notes.append(f"{where}: Interactive question is not placed inside the content")
            if unit_id not in section.get("unit_ids", []):
                fails.append(f"{where}: section does not list this unit")
            if entry.get("mode") not in modes:
                fails.append(f"{where}: unknown mode {entry.get('mode')}")
            if entry.get("mode") == "Animated scene" and not section.get("scene"):
                fails.append(f"{where}: Animated scene without a scene")
            if not entry.get("contribution", "").strip():
                fails.append(f"{where}: no contribution")
            for field in TREATMENTS + ("context",):
                for record_id in entry.get(field, []):
                    if record_id not in records:
                        fails.append(f"{where}: unknown record {record_id}")
            for field in TREATMENTS:
                covered |= set(entry.get(field, []))
        deferred = {d["record"] for d in unit.get("deferred", [])}
        uncovered = set(components) - covered - deferred
        if uncovered:
            fails.append(f"{unit_id} components not explained, practiced, or assessed: {sorted(uncovered)}")
        scene_sections = {s for s, sec in sections.items() if sec.get("scene")}
        for section_id in scene_sections:
            if unit_id in sections[section_id].get("unit_ids", []):
                labelled = any(e["section"] == section_id and e["mode"] == "Animated scene" for e in combination)
                if not labelled:
                    notes.append(f"{unit_id} uses scene section {section_id} under another mode only")
        claimed = [set(sum((e.get(f, []) for f in TREATMENTS), [])) for e in combination]
        if len(components) >= 3 and len(claimed) >= 2 and all(c >= set(components) for c in claimed):
            notes.append(f"{unit_id}: every entry claims every component; confirm each really teaches them")
        in_sections = {
            a.get("activity_id")
            for s in sections.values() if unit_id in s.get("unit_ids", [])
            for a in s.get("activities", []) if a.get("origin") == "source"
        }
        unused = {u["activity_id"] for u in unit.get("unused_exercises", [])}
        for activity_id in h_unit.get("activity_ids", []):
            if activity_id not in in_sections | unused:
                fails.append(f"{unit_id} lost source exercise {activity_id}")

    known_activities = {a["id"] for a in inventory.get("activities", [])}
    for section in sections.values():
        for activity in section.get("activities", []):
            if activity.get("origin") == "source" and activity.get("activity_id") not in known_activities:
                fails.append(f"{section['id']} references unknown activity {activity.get('activity_id')}")

    placed = {p["record_id"] for p in hierarchy.get("placements", [])}
    if placed != set(records):
        fails.append(f"hierarchy placements differ from inventory: {sorted(placed ^ set(records))}")

    return fails, notes


def describe(plan):
    shapes = Counter(" → ".join(sequence(u)) for u in plan.get("units", []))
    lengths = Counter(len(u.get("combination", [])) for u in plan.get("units", []))
    print(f"sections {len(plan.get('sections', []))}, units {len(plan.get('units', []))}, "
          f"scenes {sum(1 for s in plan.get('sections', []) if s.get('scene'))}")
    print("entries per unit (description, not a target):", dict(sorted(lengths.items())))
    recurring = {shape: count for shape, count in shapes.items() if count > 1}
    print("recurring sequences to read together:", recurring or "none")


def anchor(text):
    return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")


def lines_of(record):
    spans = sorted({(e["line_start"], e["line_end"]) for e in record.get("evidence", [])})
    return ", ".join(f"{a}" if a == b else f"{a}-{b}" for a, b in spans)


def item_text(item):
    for key in ("issue", "gap", "question", "description", "note"):
        if item.get(key):
            return item[key]
    return json.dumps(item, ensure_ascii=False)


def short_label(activity_id, inventory, section_note=""):
    activity = next(a for a in inventory["activities"] if a["id"] == activity_id)
    label = (activity.get("display_label") or activity.get("label") or activity.get("original_label", "")).replace("*", "")
    return f"**{activity_id} {label}** ([link]({activity.get('url', '')}), source line {activity.get('source_line', '?')}, not executed){section_note}"


def activity_key(activity):
    return activity.get("id") or activity.get("activity_id")


def render_activity(activity, inventory, out):
    if activity["origin"] == "source":
        out.append(f"- Source exercise: {short_label(activity['activity_id'], inventory)}. {activity['use']}")
        if activity.get("success"):
            out.append(f"  - Success: {activity['success']}")
        if activity.get("feedback"):
            out.append(f"  - Feedback: {activity['feedback']}")
    else:
        out.append(f"- Authored activity {activity.get('id', '')}: {activity['prompt']}")
        out.append(f"  - Success: {activity['success']}")
        out.append(f"  - Feedback: {activity['feedback']}")


def render_section(section, inventory, out):
    out.append(f"<a id=\"{section['id'].lower()}\"></a>")
    out.append(f"**{section['id']} · {section['title']}**")
    out.append("")
    activities = {activity_key(a): a for a in section.get("activities", [])}
    placed = set()
    for piece in re.split(PLACEHOLDER, section["content"].strip()):
        if piece in activities:
            render_activity(activities[piece], inventory, out)
            placed.add(piece)
        elif piece.strip():
            out.append(piece.strip())
        out.append("")
    remaining = [a for a in section.get("activities", []) if activity_key(a) not in placed]
    for activity in remaining:
        render_activity(activity, inventory, out)
    if remaining:
        out.append("")
    scene = section.get("scene")
    if scene:
        out.append(f"Scene teaching point: {scene['teaching_point']}")
        out.append("")
        if scene.get("invented"):
            out.append(f"Invented: {scene['invented']}")
            out.append("")
        if scene.get("metaphor_limits"):
            out.append(f"Metaphor limits: {scene['metaphor_limits']}")
            out.append("")
        out.append("| Beat | On screen | Narration |")
        out.append("| --- | --- | --- |")
        for number, beat in enumerate(scene["beats"], 1):
            visual = beat["visual"].replace("|", "\\|").replace("\n", " ")
            narration = beat["narration"].replace("|", "\\|").replace("\n", " ")
            out.append(f"| {number} | {visual} | {narration} |")
        out.append("")


def render(plan, hierarchy, inventory, records, path):
    h_units = {u["id"]: u for u in hierarchy["teaching_units"]}
    units = {u["id"]: u for u in plan["units"]}
    sections = {s["id"]: s for s in plan["sections"]}
    reviews = {r["id"]: r for r in inventory.get("review_queue", [])}
    gaps = {g["id"]: g for g in inventory.get("missing_prerequisites", [])}
    needs = hierarchy.get("unresolved_teaching_needs", [])
    display = {a["activity_id"]: a.get("display_label") for a in hierarchy.get("activity_attachments", [])}
    for activity in inventory.get("activities", []):
        activity["display_label"] = display.get(activity["id"])
    out = [f"# {plan.get('title', 'Teaching plan')}", ""]

    brief = plan.get("brief", {})
    for key in ("learner", "goal", "depth", "tone", "time", "delivery"):
        if brief.get(key):
            out.append(f"- **{key.capitalize()}:** {brief[key]}")
    for assumption in brief.get("assumptions", []):
        out.append(f"- **Assumption:** {assumption}")
    out.append("")
    out.append("Everything authored here is a plan. Source exercises were not executed, nothing was rendered, and no learner has used it.")
    out.append("")

    if plan.get("questions_for_user"):
        out.append("## Questions for you")
        out.append("")
        for question in plan["questions_for_user"]:
            options = f" Options: {'; '.join(question['options'])}." if question.get("options") else ""
            out.append(f"- **{question.get('id', '')} ({question.get('about', '')}):** {question['question']}{options} Meanwhile: {question.get('meanwhile', '')}")
        out.append("")

    if plan.get("format_suggestions"):
        out.append("## Format suggestions")
        out.append("")
        for item in plan["format_suggestions"]:
            out.append(f"- **{item['what']}** ({item.get('used_in', '')}): {item.get('why', '')}")
        out.append("")

    out.append("## Overview")
    out.append("")
    for family in hierarchy["families"]:
        out.append(f"### {family['label']}")
        out.append("")
        out.append("| Unit | Mode combination |")
        out.append("| --- | --- |")
        for unit_id in family["unit_ids"]:
            shape = " + ".join(sequence(units[unit_id]))
            target = h_units[unit_id]["target"]
            out.append(f"| [{unit_id} · {target}](#{unit_id.lower()}) | {shape} |")
        out.append("")

    out.append("## Course order")
    out.append("")
    for lesson in plan.get("lessons", []):
        out.append(f"**{lesson['id']} · {lesson['title']}.** {lesson.get('purpose', '')}")
        out.append("")
        for section_id in lesson["section_ids"]:
            section = sections[section_id]
            tags = ", ".join(section.get("unit_ids", [])) or "course"
            out.append(f"- [{section_id}](#{section_id.lower()}) {section['title']} ({tags})")
        out.append("")

    placed = set()
    course_only = [s for s in plan["sections"] if not s.get("unit_ids")]
    if course_only:
        out.append("## Course-level sections")
        out.append("")
        for section in course_only:
            out.append(f"Purpose: {section.get('course_purpose', '')}")
            out.append("")
            render_section(section, inventory, out)
            placed.add(section["id"])

    out.append("## Families, units, and combinations")
    out.append("")
    for family in hierarchy["families"]:
        out.append(f"### {family['label']}")
        out.append("")
        for unit_id in family["unit_ids"]:
            h_unit, unit = h_units[unit_id], units[unit_id]
            out.append(f"<a id=\"{unit_id.lower()}\"></a>")
            out.append(f"#### {unit_id} · {h_unit['target']}")
            out.append("")
            out.append(f"**Success check:** {h_unit['success_check']}")
            out.append("")
            out.append(f"**What needs to happen:** {unit['difficulty']}")
            out.append("")
            if unit.get("why_this_combination"):
                out.append(f"**Why this combination:** {unit['why_this_combination']}")
                out.append("")
            if unit.get("single_mode_reason"):
                out.append(f"**Why one mode:** {unit['single_mode_reason']}")
                out.append("")
            if unit.get("alternative"):
                out.append(f"**Alternative considered:** {unit['alternative']}")
                out.append("")
            out.append("**Combination:**")
            out.append("")
            treated = {}
            for number, entry in enumerate(unit["combination"], 1):
                bits = []
                for field in TREATMENTS:
                    if entry.get(field):
                        bits.append(f"{field} {', '.join(entry[field])}")
                        for record_id in entry[field]:
                            treated.setdefault(record_id, []).append(f"{field} in {entry['section']}")
                detail = f" ({'; '.join(bits)})" if bits else ""
                out.append(f"{number}. **{entry['mode']}** [{entry['section']}](#{entry['section'].lower()}): {entry['contribution']}{detail}")
            out.append("")
            out.append("**Components:**")
            out.append("")
            deferred = {d["record"]: d["reason"] for d in unit.get("deferred", [])}
            for record_id in h_unit["component_record_ids"]:
                record = records[record_id]
                status = "; ".join(treated.get(record_id, [])) or f"deferred: {deferred.get(record_id, '')}"
                out.append(f"- {record_id} {record['label']} (lines {lines_of(record)}): {status}")
            out.append("")
            if h_unit.get("supporting_record_ids"):
                out.append("**Supporting material:**")
                out.append("")
                for record_id in h_unit["supporting_record_ids"]:
                    record = records[record_id]
                    out.append(f"- {record_id} {record['label']} (lines {lines_of(record)})")
                out.append("")
            out.append("**Source exercises:** " + (", ".join(h_unit.get("activity_ids", [])) or "none attached"))
            out.append("")
            for item in unit.get("unused_exercises", []):
                out.append(f"- {short_label(item['activity_id'], inventory)} kept attached, not used in a section: {item['reason']}")
            if unit.get("unused_exercises"):
                out.append("")
            open_items = [f"{r}: {item_text(reviews[r])}" for r in h_unit.get("review_ids", []) if r in reviews]
            open_items += [f"{g}: {item_text(gaps[g])}" for g in h_unit.get("gap_ids", []) if g in gaps]
            if open_items:
                out.append("<details><summary>Open reviews and gaps</summary>")
                out.append("")
                out.extend(f"- {item}" for item in open_items)
                out.append("")
                out.append("</details>")
                out.append("")
            out.append("**Sections:**")
            out.append("")
            seen = []
            for entry in unit["combination"]:
                section_id = entry["section"]
                if section_id in seen:
                    continue
                seen.append(section_id)
                if len(sections[section_id].get("unit_ids", [])) > 1:
                    out.append(f"{section_id} · {sections[section_id]['title']}: shared, see [Shared sections](#{section_id.lower()}).")
                    out.append("")
                elif section_id not in placed:
                    render_section(sections[section_id], inventory, out)
                    placed.add(section_id)

    shared = [s for s in plan["sections"] if len(s.get("unit_ids", [])) > 1]
    if shared:
        out.append("## Shared sections")
        out.append("")
        out.append("Each of these serves several units and is taught once, at its place in the course order.")
        out.append("")
        lesson_of = {section_id: lesson["id"] for lesson in plan.get("lessons", []) for section_id in lesson["section_ids"]}
        for section in shared:
            links = ", ".join(f"[{unit_id}](#{unit_id.lower()})" for unit_id in section["unit_ids"])
            out.append(f"Serves {links}. Taught in {lesson_of.get(section['id'], 'the course')}.")
            out.append("")
            render_section(section, inventory, out)

    if needs or plan.get("gaps"):
        out.append("## Gaps and teaching needs")
        out.append("")
        for need in needs:
            out.append(f"- {need['id']} {need['label']} ({', '.join(need['record_ids'])}): {need['reason']} {need.get('next_action', '')}")
        for gap in plan.get("gaps", []):
            out.append(f"- {gap.get('id', '')} {gap['note']}")
        out.append("")

    if plan.get("proposed_hierarchy_changes"):
        out.append("## Proposed hierarchy changes (not applied)")
        out.append("")
        for change in plan["proposed_hierarchy_changes"]:
            out.append(f"- {change['change']} Mapping: {change.get('mapping', '')}. Reason: {change.get('reason', '')}")
        out.append("")

    out.append("## Record ledger")
    out.append("")
    out.append("Exact evidence text stays in the inventory file.")
    out.append("")
    out.append("| Record | Label | Status | Lines | Placement |")
    out.append("| --- | --- | --- | --- | --- |")
    placements = {}
    for placement in hierarchy.get("placements", []):
        placements.setdefault(placement["record_id"], []).append(
            f"{placement.get('unit_id') or 'teaching need'} {placement['role']}"
        )
    for record_id, record in records.items():
        where = "; ".join(placements.get(record_id, []))
        label = record["label"].replace("|", "\\|")
        out.append(f"| {record_id} | {label} | {record.get('status', '')} | {lines_of(record)} | {where} |")
    out.append("")

    with open(path, "w", encoding="utf-8") as handle:
        handle.write("\n".join(out))


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
        render(plan, hierarchy, inventory, records, args.out or "view.md")
        print("wrote", args.out or "view.md")
        return

    fails, notes = check(plan, hierarchy, inventory, records)
    describe(plan)
    for note in notes:
        print("NOTE:", note)
    for fail in fails:
        print("FAIL:", fail)
    print("PASS: references only; read the content to judge teaching" if not fails else f"{len(fails)} failures")
    sys.exit(1 if fails else 0)


if __name__ == "__main__":
    main()
