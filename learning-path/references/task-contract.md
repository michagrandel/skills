# Two-hour solo task contract

## Budget

Use a **maximum 120-minute session**, not an optimistic promise that a feature will be finished in two hours. A practical task breakdown is:

- 10 minutes: recall, predict, check prerequisites.
- 65 minutes: bounded implementation or deliberate drawing practice.
- 20 minutes: observe, run checks or compare against references.
- 10 minutes: explain and record learning evidence.
- 15 minutes: one focused recovery attempt.

Shorter tasks scale these components down. Never add a recovery exercise on top of a 120-minute total.

If the output cannot plausibly fit, split the task BEFORE publishing the plan. Installing a full toolchain, learning networking, building a GUI or painting a complete character are not single tasks.

## Dependency and entry gate

Every task names:

- Earlier task IDs actually required; `none` for a genuine root.
- Concrete available inputs, tools and passed evidence.
- A prerequisite check before any task depending on uncertain prior knowledge.

A task with an unmet prerequisite does not begin. Save its blocked status and revisit the dependency; do not silently substitute generated artifacts.

## Shortcut cost

Be specific:

- "Generating this move/aim state machine skips reasoning about legal transitions and irreversible actions."
- "Copying a pybind11 wrapper skips ownership, lifetime and exception-boundary practice."
- "Tracing this gesture skips deciding the action line and weight distribution; use a new pose from reference afterward."

Do not claim all AI assistance damages learning. Syntax lookups, accessibility aids, setup troubleshooting and critique can be productive. The loss occurs when a helper performs the skill the task was intended to train.

## Evidence and recovery

A concrete artifact plus a short explanation are the default. At least some checks require rebuilding a tiny example, diagnosing a seeded failure or transferring to an unseen reference.

If a full solution was necessary, flag "assisted; mastery pending" and spend the reserved check/recovery minutes on a new, smaller independent exercise. If this still fails, stop and revisit the named prerequisite in a separate bounded session. Do not infer incompetence or demand indefinite grinding.

## Domain-specific notes

- **Programming:** use tests, small fixtures, state diagrams and measured profiles; full AI-generated implementations are not learner evidence.
- **Networks:** use local two-process tests first; distinguish actual transport behavior from a mocked message log. Avoid depending on another person's availability.
- **Art:** use real observation, timed sketches, silhouette/value checks and concrete corrections; AI praise and attractive generated references are not anatomy evidence. Use licensed anatomical/photo references; compare structure, not worth.
- **Professional skills:** hypotheses, failure reports and "why this boundary?" explanations matter as much as polished UI or final rendering.

## Example task

**LP-07 - Reject stale turn messages (120 minutes)**

- Dependencies: LP-05 command model, LP-06 two-process message transport.
- Before start: a working local host/client pair and a recorded valid turn packet.
- Partial goal: explain sequencing and idempotency in a turn-based network game.
- Work: predict duplicate behavior, implement one turn-ID check, replay a recorded packet.
- Output/check: valid packet applied once; duplicate/stale packet rejected with an explicit reason; explain the invariant without reading generated code.
- Shortcut cost: copying the entire networking handler prevents learning where ordering and replay protection belong.
- Allowed support: protocol/API lookup and a hint after an independent attempt.
- Stop/recovery: reserve the final 15 minutes for a three-message paper timeline; save remaining failures and revisit LP-05 if unresolved.
