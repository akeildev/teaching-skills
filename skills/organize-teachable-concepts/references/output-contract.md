# Saved inventory and outline

Keep the inventory (`inventory.json`, the evidence) and the outline (`overlay.json`, the teaching structure) as separate files. When an input inventory already has its own schema, keep its field names and build the outline around it.

## Inventory (`inventory.json`)

- `source`: identity, location, fingerprint, and coverage limits.
- `records`: one object per record, with `id`, `label`, meaning, `evidence` (a list of `source_id`, `line_start`, `line_end`, `exact_text`), status, and any `review_ids` and `gap_ids`.
- `activities`: source exercises, including any invitation to try something, with `id`, `label`, `url`, `source_line`, and execution status.
- `figures`: embedded media, with location and inspection status.
- `resources`: every other link, with `url`, line, kind (for example further reading, reference, product), related units, and inspection status.
- `review_queue`: `id`, `issue`, `action`, `applies_to`.
- `missing_prerequisites`: `id`, `gap`, `applies_to`, and a label saying it is inferred.
- `relations`, `coverage_ledger`, as the source requires.

Additions to an existing inventory go in a separate addendum file with the same fields, new IDs, and a version note. Add a `reason` to any record whose meaning is deliberately narrower than its evidence.

## Outline (`overlay.json`)

- `main_point`: the source's main point in one sentence.
- `input`: inventory and source fingerprints, plus coverage limits.
- `families`: `id`, `label`, `unit_ids`.
- `teaching_units`: `id`, `family_id`, `target`, `success_check`, `component_record_ids`, `supporting_record_ids`, `activity_ids`, `review_ids`, `gap_ids`, `readiness`, and instructional provenance.
- `placements`: `record_id`, `unit_id`, `role` (`component`, `supporting_material`, `course_level` for orientation that serves no one unit, or `unresolved`), `subtype` for supporting material (for example example, exercise, evidence, measurement, qualification, orientation, reference snapshot), and a reason where classification is consequential. A record may have several placements.
- `activity_attachments`: `activity_id`, `unit_id`, `purpose`, `url`, source line, and execution status. Display labels may clarify vague link text; the original label stays in the inventory.
- `unresolved_activities`: `activity_id`, reason, and next action, for any activity that cannot be attached yet.
- `unresolved_teaching_needs`: `id`, `record_ids`, `label`, `reason`, related units, `next_action`. These sit outside the unit count. A topic whose location is clear can still lack the content to teach it.
- `unit_migrations`, when revising a prior hierarchy: old ID, status (retained, merged, split, retired), successors, reason. Retired IDs are never reused.
- `relations`: typed links and labeled inferred prerequisites, kept apart from parentage.
- `questions_for_user`: `id`, `about`, `question`, `options`, `meanwhile`, for each ambiguity and provisional unit.
- `format_suggestions`: `what`, `why`, `used_in`, for each field you added beyond this contract.

A bare ID mapping is not self-contained: reference a durable inventory snapshot or embed it unchanged.

## Readable view

Save it as `outline.md` beside the data files. Write it for a person who has not seen the source, in plain words, leading each part with its point. Any code that appears comes with its meaning. IDs go in small tags at the end of a line (`R14`), so every line still traces to the evidence.

1. **What this source teaches:** the `main_point`, then a map of each family and its units, one line each.
2. **One block per unit:**
   - A numbered title and its status: ✅ ready, or ⚠️ not final, with the reason in a few words.
   - **You'll be able to:** the target. **How to check:** the success check, as a task.
   - **Checklist:** the components, one ☐ line each.
   - **Helps teach it:** supporting material, each saying which checklist item it helps, or "whole unit". 💡 for anything that helps explain (examples, evidence, analogies, motivation, orientation); ⚠️ for caveats, qualifications and open issues.
   - **Source exercises:** each attached exercise, or "none in the source".
   - **You'll need to know first:** assumed background, by name.
3. **What needs you:** the questions, numbered, each with its options and what was done meanwhile; then teaching needs, what was not inspected, what was left out and why, and the important split and merge choices.
4. **Details:** course-level records, counts, the source file and its fingerprint, and, when reorganizing an earlier outline, the old-to-new ID mappings.

## Check

`scripts/check_overlay.py` (command in `SKILL.md`; add `--addendum FILE` when there is an addendum) confirms that every record and exercise is placed, references resolve, each unit has a target and success check, earlier unit IDs are accounted for, and evidence text matches the source. It cannot see a lost caveat.
