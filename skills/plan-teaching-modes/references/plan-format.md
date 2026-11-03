# Saved plan format

Write one JSON plan and generate the readable view from it, so the two cannot disagree.

```json
{
  "title": "",
  "main_point": "the outline's main point, in one sentence",
  "brief": {"summary": "one line: who, how long, the goal", "learner": "", "goal": "", "depth": "", "tone": "", "time": "", "delivery": "", "assumptions": []},
  "lessons": [{
    "id": "L1",
    "title": "",
    "minutes": 10,
    "items": [
      {"course": "Opener", "minutes": 1, "modes": [
        {"mode": "Big question", "job": "the job this mode does here, in one line", "explains": [], "practices": [], "assesses": []}
      ]},
      {"unit": "TU-01", "minutes": 4, "modes": [
        {"mode": "Interactive question", "job": "", "explains": [], "practices": [], "assesses": []}
      ],
       "exercises": [{"activity_id": "A01", "use": "how it is used"}],
       "left_out_components": [{"record": "C001", "reason": ""}]}
    ]
  }],
  "left_out": [{"unit": "TU-07", "reason": ""}],
  "added_modes": [{"name": "", "definition": ""}],
  "questions_for_user": [{"id": "Q1", "about": "TU-01 or a record ID", "question": "", "options": [], "meanwhile": "what the plan assumes until answered"}],
  "format_suggestions": [{"what": "", "why": "", "used_in": ""}]
}
```

- A lesson's `items` are in teaching order. A unit item holds that unit's modes; a `course` item (an opener, a closing explain-back) holds modes that serve the course or several units.
- Each unit in the outline appears once, either as an item or in `left_out`. Units taught together sit next to each other.
- `explains`, `practices` and `assesses` name the outline's component records that mode really does that with. A course item can cover components of any unit.
- Omit optional fields you don't use. When this format lacks something you need, add your own field and record it in `format_suggestions`.

## What the check covers

`scripts/plan_tool.py check` (commands in `SKILL.md`) confirms that every unit is placed or left out with a reason, every component is covered or left out with a reason, every source exercise is used, and all references exist. `render` writes `view.md`: the course by lesson, each unit's modes and jobs, what was left out, and the questions.
