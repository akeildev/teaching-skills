# Saved plan format

Author one JSON plan and generate the readable view from it, so the two cannot disagree. Sections hold the teaching; units say how they use those sections.

```json
{
  "title": "",
  "brief": {"learner": "", "goal": "", "depth": "", "tone": "", "time": "", "delivery": "", "assumptions": []},
  "lessons": [{"id": "L1", "title": "", "purpose": "", "section_ids": ["S01"]}],
  "sections": [{
    "id": "S01",
    "title": "",
    "unit_ids": ["T01"],
    "course_purpose": "only for course-level sections with no unit",
    "content": "the teaching itself: what the learner sees, hears, reads, and does",
    "activities": [
      {"id": "X01", "origin": "authored", "prompt": "", "success": "", "feedback": ""},
      {"origin": "source", "activity_id": "A01", "use": "how this section uses it"}
    ],
    "scene": {
      "teaching_point": "",
      "invented": "what is illustration rather than source",
      "metaphor_limits": "",
      "beats": [{"visual": "", "narration": ""}]
    }
  }],
  "units": [{
    "id": "T01",
    "difficulty": "what must become understandable or doable, and where this learner may go wrong",
    "combination": [{
      "section": "S01",
      "mode": "Worked example",
      "contribution": "what this mode adds for this unit",
      "explains": [], "practices": [], "assesses": [], "context": []
    }],
    "why_this_combination": "",
    "alternative": "optional: a real alternative and why it lost",
    "single_mode_reason": "required only when one mode is used",
    "deferred": [{"record": "C001", "reason": ""}],
    "unused_exercises": [{"activity_id": "A01", "reason": ""}]
  }],
  "added_modes": [{"name": "", "definition": ""}],
  "questions_for_user": [{"id": "Q1", "about": "T01 or a record ID", "question": "", "options": [], "meanwhile": "what the plan does until answered"}],
  "format_suggestions": [{"what": "", "why": "", "used_in": ""}],
  "gaps": [{"id": "", "note": ""}],
  "proposed_hierarchy_changes": [{"change": "", "mapping": "", "reason": ""}]
}
```

- `combination` is the learner's order for that unit. Two entries may name one section with different modes; that is how a section's several functions stay visible.
- `explains`, `practices`, and `assesses` name only the records that entry's content really does that with. Everything else the section merely draws on goes in `context`.
- A course-level section has an empty `unit_ids` and a `course_purpose`. A capstone or retrieval section that revisits units lists them, and each adds an entry.
- `activities` and `scene` are optional per section. An Animated scene entry requires a `scene` on its section.
- An Interactive question is written as an activity, and `{{X01}}` in `content` places it at that exact spot, before the text that reveals the answer. Any activity can be placed this way, using its `id` or `activity_id`; unplaced activities appear after the content.
- When this format lacks something you need, add your own field and record it in `format_suggestions`.
- Omit optional fields you do not use.

A long plan can be authored as several files in one directory, each holding part of `sections`, `units`, or `lessons`, with `brief` and the rest in any one file. The script merges them.

## Check and render

```bash
python3 scripts/plan_tool.py check PLAN --hierarchy HIERARCHY --inventory INVENTORY
python3 scripts/plan_tool.py render PLAN --hierarchy HIERARCHY --inventory INVENTORY --out view.md
```

`PLAN` is a file or directory; `HIERARCHY` and `INVENTORY` are the overlay and inventory JSON files. Pass `--addendum FILE` to either command when the inventory has a versioned addendum. `check` confirms references, component accounting, exercise attachment, activity fields, and scene fields, and prints which sequences recur so you can read those units together. It has no opinion on how many modes, sections, or scenes a plan should have. `render` writes the family-first view, joining in components, supporting records, evidence locations, open reviews, and a full record ledger. Sections serving several units print once in a Shared sections part, linked from each unit.
