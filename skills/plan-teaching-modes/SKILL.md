---
name: plan-teaching-modes
description: Chooses how to teach the units of a teaching outline for a specific learner and brief - the combination of teaching modes for each unit - and arranges the units into timed lessons. Use when an outline from organize-teachable-concepts exists and the question is how to teach it. For a raw source, run organize-teachable-concepts first.
---

# Plan teaching modes

Decide which teaching modes each unit gets, give each mode its job, and arrange the units into lessons. The plan stops there: the wording, examples, questions, pictures and scenes belong to whoever builds the lesson (for slides, `design-teaching-slides`).

```
- [ ] 1. Read the inputs and the mode catalog
- [ ] 2. Choose modes for each unit
- [ ] 3. Arrange the course
- [ ] 4. Save and check until it passes
- [ ] 5. Report
```

## 1. Read the inputs and the mode catalog

Read the outline from `organize-teachable-concepts` (`overlay.json` and `inventory.json`, readable as `outline.md`), including its `main_point`, and the learner's brief: who they are, their goal, depth, tone, time and delivery. State an assumption wherever the brief is silent. Read [the mode catalog](references/mode-catalog.md).

Keep the outline as supplied and suggest changes separately, with reasons. A gap stays a gap: a mode cannot supply missing evidence.

## 2. Choose modes for each unit

For each unit, work out what must become understandable or doable and where this learner will likely go wrong. Choose the modes that get them there, usually a few that complement each other. Give each mode one line naming its teaching job: what it makes the learner understand or do about the unit's key idea. The lesson builder decides the picture and the wording. Name the components each mode explains, practises or checks, and cover every component or leave it out with a reason.

Each unit includes at least one mode where the learner answers, practises or explains, pitched to their level and goal. Source exercises stay attached by ID. A provisional unit still gets modes, plus a question about it.

## 3. Arrange the course

Build the course around the outline's main point: the opening raises it, every unit's modes serve it, and the course closes with the learner saying it in their own words. Copy it into the plan as `main_point`.

Put the units into lessons in teaching order, with rough minutes when the brief sets a time limit. A lesson can also hold course-level items, such as an opener or a closing explain-back, each with its own modes. Units taught together sit next to each other. When time runs short, leave out whole units with a one-line reason each.

Then read the units side by side and vary any sequence that repeats out of habit.

## 4. Save and check until it passes

Save `plan.json` in [the saved format](references/plan-format.md), then run this skill's script:

```bash
python3 scripts/plan_tool.py check plan.json --hierarchy overlay.json --inventory inventory.json
python3 scripts/plan_tool.py render plan.json --hierarchy overlay.json --inventory inventory.json --out view.md
```

Fix what the check reports and run it again until it passes. Add `--addendum FILE` to both commands when the inventory has an addendum.

## 5. Report

End your reply with the lessons in order, each unit's modes, the units left out and why, and one question per open issue with what the plan assumes meanwhile.
