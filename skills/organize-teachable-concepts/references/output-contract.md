# Saved inventory and hierarchy

Keep the inventory (evidence) and the overlay (teaching organization) as separate files. When an input inventory already has its own schema, keep its field names and add the overlay around it.

## Inventory

- `source`: identity, location, fingerprint, and coverage limits.
- `units` (or `records`): one object per record, with `id`, `label`, meaning, `evidence` (a list of `source_id`, `line_start`, `line_end`, `exact_text`), status, and any `review_ids` and `gap_ids`.
- `activities`: source exercises, including any invitation to try something, with `id`, `label`, `url`, `source_line`, and execution status.
- `figures`: embedded media, with location and inspection status.
- `resources`: every other link, with `url`, line, kind (for example further reading, reference, product), related units, and inspection status.
- `review_queue`: `id`, `issue`, `action`, `applies_to`.
- `missing_prerequisites`: `id`, `gap`, `applies_to`, and a label saying it is inferred.
- `relations`, `coverage_ledger`, as the source requires.

Additions to an existing inventory go in a separate addendum file with the same fields, new IDs, and a version note. Add a `reason` to any record whose meaning is deliberately narrower than its evidence.

## Overlay

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

Show each family with its units; each unit's target, success check, and components; attached examples, exercises, evidence, and qualifications, visibly distinct from components; provisional units and missing explanations; and, when reorganizing, original-ID mappings and a coverage summary. An overview can collapse detail as long as the records stay reachable.

## Check

```bash
python3 scripts/check_overlay.py inventory.json overlay.json --source source.md [--addendum addendum.json]
```

The script compares record and activity ID sets exactly, rejects dangling references, confirms each unit has a target and success check, accounts for prior unit IDs, matches evidence text against the source snapshot, and lists source links with no individual disposition. A pass establishes accounting and reference integrity only. It cannot see a dropped clause, because quotes can be longer than meanings; teaching granularity and extraction recall need review by a reader.
