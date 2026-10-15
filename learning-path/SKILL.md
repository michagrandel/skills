---
name: learning-path
description: "Create project-based learning plans as detailed, self-contained HTML documents with confirmed learner-owned goals, AI coaching, Mermaid diagrams and solo learning tasks of at most two hours. Use when: the user requests learning-path, a Lernplan, Lernpfad, project-based learning, a curriculum, or a learning project. Clarify goals before planning; never infer or silently add related learning goals."
argument-hint: "[learning project or goals] [--skin=BF6] [--language=de|en]"
user-invocable: true
---

# Create a project-based learning path

## Purpose and role

Act as an experienced educator and practitioner in the requested domain. Produce a project-based learning path with the conceptual depth of a feature plan, not a delivery schedule or a list of tutorials. A completed artifact is not proof that the learner acquired its underlying skills.

The learner owns the goals. Your job is to propose, clarify, structure and verify learning, not decide what the learner ought to want.

## 1. Mandatory goal gate - before planning

1. Extract only goals explicitly stated or selected by the learner. Distinguish:
   - **Learning goal:** an observable ability the learner wants to acquire.
   - **Project outcome:** the artifact used to practice that ability.
   - **Prerequisite:** an ability or resource required to start.
   - **Implementation choice:** a proposed means, not a new learning goal.
2. If a goal is vague, ask the learner using the available question tool. Offer concrete, plausible alternatives, including related goals where useful. Ask one focused question at a time. Mark related goals as suggestions and let the learner select, reject or modify them.
3. Never infer a goal from a job title, project name, familiar software or the AI's preferred stack. Do not treat an unanswered question as permission.
4. Clarify material ambiguities in project rules, scope, learner baseline, devices and intended end result. Ask about implementation choices only when they materially change the learning scope.
5. Summarize confirmed goals, exclusions and baseline. Existing explicit answers count as confirmation; do not ask the same question again.
6. **Hard stop:** do not generate a final curriculum, prerequisite chain or finished HTML plan until goals are sufficiently clear. An `[OPEN QUESTION]` marker is not a substitute for goal agreement. A neutral draft of the user's already-stated goals is allowed while waiting.

After goals are confirmed, unresolved non-blocking implementation details may be marked `[OPEN QUESTION: ...]`. Record provisional choices as `[PROPOSAL: ...]`; do not label invented preferences as facts. Scope expansion requires a new learner decision.

## 2. Choose the practice project and evidence

- Design the smallest meaningful project that exercises all confirmed goals.
- Define observable mastery evidence for each goal, including at least one explanation, reconstruction or transfer task without generated solutions.
- Record baseline and prerequisite checks. The learner's professional experience is context, not proof of skill in a new domain.
- Map every goal to practice tasks and an independent exit check. Map project-only setup tasks explicitly to `No new learning goal; prerequisite preparation`.
- Separate must-have practice from optional extensions. Optional extensions must not become hidden prerequisites.
- Avoid invented facts about named games or software. Use learner-supplied rules or verified references; otherwise ask. Use original or appropriately licensed assets rather than copied commercial assets.

## 3. Output and templates

One valid HTML file per learning project. Default language is the learner's language; `--language` overrides it. Support `--skin=BF6` and `--skin bf6`, case-insensitively.

- Neutral dark template: [base-template.html](./references/base-template.html).
- BF6/HUD template: [base-template-bf6.html](./references/base-template-bf6.html).
- Preserve the selected template's CSS and module script **verbatim**. Replace real `<main>` content, title and navigation; do not replace `<main>` occurrences inside template comments.
- No external fonts, images or style sheets; Mermaid via the template CDN is permitted. Explain that rendering/export requires access to that CDN. Narrative and source diagrams remain readable without it.
- Keep plans independently readable. Multiple requested plans may link to each other, but must not depend on another document for their learning goals or task definitions.
- Save in the user-requested location, or a clearly named `learning-paths` folder in the workspace. Do not put generated learner projects in the user skill folder unless requested; that folder holds the reusable workflow and templates.

## 4. Exact document order

### 0. Confirmed learning goals - first

The first substantive content must be the learner's clearly formulated goals, with stable IDs `LG-01`, `LG-02`, etc. Use a hero with `.kicker` = `Learning Path`, project title as white `h1`, and a one-sentence `.hero-sub`. Place the goal list immediately below the hero, before project details or the curriculum.

For each goal: observable ability, independent proof, and relevant task IDs. Include confirmed baseline, agreed exclusions and resources. Distinguish project acceptance from learning mastery.

### A. How to learn with AI support

Describe a concrete domain-specific coaching protocol:

1. Predict or sketch an approach yourself.
2. Make a bounded independent attempt.
3. Ask AI for a question or small hint, not the completed target exercise.
4. Check advice against official references, execution results or observable drawing evidence.
5. Explain the result in your own words.
6. Reconstruct or transfer it without generated answers.

Use an assistance ladder: question -> hint -> diagnostic explanation -> partial worked example of a different problem -> full solution only after the learner deliberately chooses the trade-off. If a full solution was used, add a small independent recovery exercise rather than pretending mastery.

Allow helpers for incidental setup, boilerplate or already-mastered work, but distinguish this from outsourcing the actual target skill. Include sample coaching prompts, timeboxes, practical feedback and domain-specific limitations of AI. Do not force coding/TDD practices onto visual art learning.

### B. Detailed learning project

Describe requirements and interactions as thoroughly as a feature plan:

- Atomic, verifiable project requirements and complete user-supplied rules.
- Learner/practice personas in `.cards`, without inventing additional users' goals.
- Use-case diagram covering meaningful interactions.
- Deliverable, scope boundaries, constraints and acceptance checks.
- Rights, privacy, safety and resource prerequisites as relevant.

### C. Concept, alternatives and risks

- At least two pragmatic alternatives, presented as `.card` elements with pros and cons.
- Chosen approach compared to each alternative in the two-column `.procon` grid.
- `.reco` block: `RECOMMENDATION` label, white uppercase solution title, grounded rationale.
- Include cognitive overload, copied-solution illusion, workflow disruptions and domain-specific technical/artistic risks.
- Explain why the choice teaches the confirmed goals; do not optimize exclusively for delivery speed.

### D. Conceptual implementation or creation

Use sequential cards: intent -> mechanism -> very simple pseudocode or creation procedure -> evidence. Include an overall architecture/process diagram and flow diagrams for non-trivial mechanisms. Every non-trivial pseudocode mechanism must have a corresponding diagram.

For art: use observation/construction/painting steps, annotated layer procedures and critique criteria rather than fabricated code.

If database tables are relevant, include both a `CREATE TABLE` example and an ER diagram showing relationships to known existing tables. State when no existing schema is available. Code quoted from an existing project must cite its exact source and line range; otherwise label as conceptual pseudocode.

### E. Solo learning plan - replaces estimates

No person-day estimate table, Tests/Implementation/Deployment budget, guaranteed completion date or hidden buffers. Use a dependency-aware curriculum of individually completable tasks.

**Every task must fit within 120 minutes total**, including its check, reflection and recovery allowance. See the [task contract](./references/task-contract.md).

- Stable task ID; imperative title; minute budget; explicit dependency IDs or `none`.
- Exact start prerequisites and required tools/files/evidence.
- One bounded action sequence, not an entire feature disguised as a two-hour task.
- Partial learning goal ID and observable ability, or explicitly no new goal.
- Concrete output and acceptance evidence.
- What the learner loses by using AI, tutorials, tracing, purchased assets or other shortcuts on this particular exercise.
- Allowed support and an independent explanation/rebuild/transfer check.
- Stop rule: what to save after the timebox; a bounded recovery activity, never "keep going until complete".
- Dependencies refer only to defined required tasks and form an acyclic graph. Record all true prerequisites, not assumed list order.

Include a Mermaid dependency diagram and a task-to-goal coverage table. Keep tasks small enough for one person. Integration/peer tests must have a solo two-process or device fallback; a friend may be an optional usability tester, never a required worker.

Use spaced repetition and deliberate practice where useful. Each required repetition gets a bounded task/timebox; do not hide an unlimited practice loop behind "repeat until good".

### F. Independent mastery and continuation

End with explicit goal-based exit checks, a small transfer challenge, self-evaluation and a learner-controlled next-step decision. Independent means no generated solution, not a ban on necessary execution/drawing tools. State whether API documentation or references are allowed per check.

No passing simply because an app runs or an illustration looks finished. A failed exit check points to specific recovery tasks; it does not become a judgment about the learner's intelligence or worth.

## Component formatting

- Sidebar `.toc-title` matches hero title; sticky anchors follow the above sections.
- Personas, alternatives and conceptual phases use `.cards` / `.card`, `h4`, `.sub`.
- Code/procedure text uses `.codeblock` with `.copy-btn` (`Copy Code` or `Copy Procedure`).
- Diagrams use `.diagram`, `pre.mermaid`, `.btnbar` with `.dl-btn` / `.mm-btn`, and closed `<details>` containing matching `pre.mm-src`.
- Decision edges use exactly `yes` / `no` so the template colors them.
- Learning tasks use table rows with `<td><details><summary>ID - Title</summary><div class="jira">...`.
- To use the existing ticket-copy script, `.jira` contains exactly three `<p>` blocks: **Objective:** (goal and bounded actions), **Key deliverables:** (evidence, independent check), **Risks & dependencies:** (dependencies, prerequisites, shortcut cost, allowed help and stop/recovery).
- Put `.btnbar` containing `.jtitle-btn` (`Copy Title`) and `.jdesc-btn` (`Copy Description`) at the end of `.jira`; the template makes these reachable while details are closed.
- Visible columns: task, duration in minutes, dependencies. Do not overload durations with effort estimates.

## Validation before delivery

Check:
1. Goals and consequential scope were explicitly learner-selected; related goals remain optional.
2. Every goal maps to practice plus independent mastery evidence.
3. Every required task is solo, bounded to at most 120 minutes, has complete prerequisites and task-specific shortcut costs.
4. Dependencies exist, are acyclic and do not point to optional/unselected work.
5. The project does not silently add features or omit learner-supplied rules.
6. CSS/module script match the bundled selected template; HTML structure, anchors and local links are valid.
7. Mermaid source and rendered-block text match; browser rendering works when tools are available.
8. Test representative copy controls and diagram export when possible. Report unverified interactions honestly; do not claim success because the template has been used elsewhere.
9. Skill frontmatter is valid; `name` matches `learning-path`, `description` is meaningful and bundled resources exist.

Deliver linked documents, summarize confirmed goals and disclose significant open questions. Never claim a new user skill is already indexed by every running chat; advise a reload/new session only if discovery needs it.
