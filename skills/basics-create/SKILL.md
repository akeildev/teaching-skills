---
name: basics-create
description: Turns an uploaded document into a finished teaching slide deck by running organize-teachable-concepts, plan-teaching-modes and design-teaching-slides in order.
disable-model-invocation: true
---

# Basics create

The user supplies a document and says who the lesson is for. Run the three skills in order, each on the previous one's output, and keep all outputs in one folder named after the document:

```
- [ ] 1. organize-teachable-concepts on the document
- [ ] 2. plan-teaching-modes on that outline, with the user's description of the learner, goal and time
- [ ] 3. design-teaching-slides on the plan and the outline
```

Between stages, keep going: note each skill's questions for the user, continue on the default it states, and ask them all at the end. The design skill's style choice still applies.

Finish with the deck link, the collected questions, and what each stage left unverified.
