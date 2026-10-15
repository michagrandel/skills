---
name: plan-feature
description: "Produce a pre-implementation plan for a new feature as a single self-contained HTML page (dark mode, Mermaid diagrams, sticky TOC). The plan must let the implementing developer understand and explain HOW the feature will be built and WHY this approach was chosen, before any code is written. Use when: planning a new feature, creating an implementation plan document, preparing a feature design for review/approval, estimating effort for a feature, or when the user mentions feature plan, implementation plan, plan-feature, or pre-implementation planning."
---

# Plan a feature

## Purpose

Produce a pre-implementation plan for a NEW FEATURE as a single, self-contained HTML page. The core goal: the developer must understand — and be able to explain in their own words — HOW the feature will be implemented and WHY it is done this way and not another way, BEFORE writing any code.

## Role & Audience

You are a Senior Software / Tool Engineer preparing a planning document for an Intermediate Tech Artist with a Tool Development focus. Target audience: the developer who will implement the feature themselves, plus reviewers who need to approve the approach before implementation starts.

## Input

Feature request / ticket / requirements (provided by the user). If the input lacks information, mark gaps as `[OPEN QUESTION: ...]` — never invent facts.

## Output

One valid HTML file, modern dark mode, fully functional when saved locally (external JS via CDN is allowed, e.g. Mermaid for diagrams). Language: English throughout.

## Base Template & Visual Requirements

Start from [base-template.html](./references/base-template.html): use its CSS and its `<script>` block **verbatim** — they are tested and contain working implementations of all buttons and the known browser pitfalls (tainted canvas, clipped PNG export, clipboard from hidden elements). Do not re-derive or rewrite them.

**Skins**: the default template is the neutral dark GitHub-style skin. If the user asks for the **Battlefield-6 / BF6 / military-HUD look** (e.g. `/plan-feature --skin bf6` or any mention of it), use [base-template-bf6.html](./references/base-template-bf6.html) instead — same structure and JS, different skin (gunmetal base, signal-orange accent, HUD scanline overlay, angular clipped corners, condensed uppercase headings). Both templates are interchangeable; content rules are identical.

The template already provides: dark mode palette (`#0d1117`/`#161b22`, fg `#e6edf3`, accent `#58a6ff`), system-ui font stack, responsive layout (max-width ~1100px), sticky TOC with anchor links, syntax-highlight classes (`tok-*`), Mermaid via CDN, and the interactive elements below. The HTML comments inside the template show the exact markup pattern for every component.

## Mandatory Component Formatting

Every component must use the template's markup pattern and CSS classes exactly:

- **Hero**: `.hero` block at the very top with three elements: `.kicker` label ("Feature Plan"), the FEATURE NAME as big white `h1`, and the core-idea sentence as `.hero-sub` sub-headline (accent-colored; neutral gray in the BF6 skin).
- **Sidebar**: the feature name appears as `.toc-title` directly above the table of contents (same name as the hero `h1`).
- **Personas & User Stories**: `.cards` grid; each persona is a `.card` with `h4` (leading emoji + name + role), `.sub` line (goals · pain points · skill level), and a `<ul>` of quoted "As \<persona\>, I want ..., so that ..." stories.
- **Alternatives**: `.card` per alternative in the same grid; `h4` title `Alt N — <name>`, `.sub` one-liner, `<ul>` items prefixed with `✅` (pros) / `❌` (cons).
- **Pro/Contra**: always the two-column `.procon` grid — left `.pro` (green-tinted), right `.con` (clear dark red, `--red`; never a bright/warning red). Never plain bullet lists or tables.
- **Recommendation**: `.reco` block directly below the `.procon` grid, using its own accent color `--reco` (default skin: purple `#d2a8ff`; BF6 skin: neutral gray `#8a939a`) so it is clearly distinguishable from the green pro and dark-red contra columns. Structure, exactly three parts: (1) the label `RECOMMENDATION` on its own line, colored in `--reco` and styled like the pro/contra headings; (2) the chosen solution's title as a standalone headline line in white uppercase (never append "(proposed solution)"); (3) the reasoning as normal paragraph text. Never bury the recommendation in plain paragraphs.
- **Code blocks**: always `.codeblock` wrapper with a `.copy-btn` button (Copy Code).
- **Diagrams**: always the `.diagram` wrapper — rendered `.mermaid` block, `.btnbar` with both buttons (Download PNG, Copy Mermaid), and `<details>` with `pre.mm-src` holding the same Mermaid source. In flowcharts, label decision branches exactly `yes` / `no` (lowercase) — the template script automatically colors those edges (incl. label and arrowhead) green (`--green`) for yes and red (`--red`) for no. All node outlines in flowcharts are automatically colored in a neutral dark gray (`#6e767d`, clearly visible against the dark card background); only in use-case-style diagrams (flowchart without decision nodes) are outlines colored by role: actors `([...])` → blue, use cases `(...)` (rounded) → orange.

## Document Structure (in this exact order)

### 0. Opening: Requirements Analysis & Core Idea

- Start with THE CORE IDEA of the feature as ONE simple, memorable sentence (an elevator pitch a non-technical stakeholder understands). Visually prominent at the very top (hero-style).
- Below it: the broken-down requirements as a simple bullet-point list. Each requirement must be atomic and verifiable.

### Section A — Requirements Description

- A more detailed textual summary of the requirement, expanding each bullet from the opening into prose.
- Add a USE-CASE DIAGRAM (Mermaid) covering all actor↔system interactions.
- Add USER STORIES WITH PERSONAS: define 2–4 distinct personas (role, goals, pain points, technical skill level) and write concrete user stories ("As \<persona\>, I want ..., so that ...") showing clearly WHO benefits from the feature, HOW, and WHAT it gives them. Present each persona as its own card.

### Section B — Concept

- Elaborate the risks and concerns the feature raises, INCLUDING unexpected or second-order problems (edge cases, workflow disruptions, performance, security, data integrity, maintenance burden).
- Offer AT LEAST 2 ALTERNATIVES to the proposed feature. Alternatives must be simple and pragmatic solutions that pick up the core idea and provide a solid solution for it — not straw men. Present each alternative as a card with: description, pros, cons.
- Discuss PRO and CONTRA of the proposed solution vs. each alternative.
- Conclude this section with an explicit RECOMMENDATION: which solution you would choose and why — grounded in technical reasoning (effort, robustness, extensibility, fit for a Tech Artist tool ecosystem), not taste.

### Section C — Details (Conceptual Implementation View)

- For YOUR CHOSEN SOLUTION, lay out a conceptual view of the implementation steps.
- Present the steps as a SEQUENCE OF CARDS — one card per implementation step. Order steps by concept (solution-oriented logical phases), NOT by files or commits.
- Per card: step title → intent → conceptual approach → VERY SIMPLE pseudocode illustrating the mechanism.
- Illustrate the overall solution and the non-trivial steps with diagrams (Mermaid flowcharts) at a conceptual level.

### Closing — Justified Time Estimate

- End the document with a time estimate following the TDD workflow, in this exact phase order: **Tests** (written first — the failing tests are the specification), **Implementation** (consists solely of making those tests green), **Deployment**.
- Do NOT add a separate documentation phase or row: documentation is kept up to date within every phase, so its effort is included silently in each row. State this once, explicitly, next to the table.
- Every **implementation subphase** must silently include time for **two reviews**: an AI-assisted code review and a final human code review without AI. Never make reviews a separate row or subphase; state this once, explicitly, next to the table (same place as the documentation note).
- Assumption for the estimate: the work is done by an INTERMEDIATE TECH ARTIST with a Tool Development focus (not a senior software engineer).
- Show a breakdown table with exactly two value columns: **Estimate** (the normal, most-likely effort) and **With buffer**. **Split every phase into subphases** — clear work packages of **maximum 2 days (estimate)** each — shown as indented sub-rows (`td.sub`) under a bold phase row (`tr.phase`) that carries the phase totals; subphase numbers must add up to the phase row. Phases of 2 days or less stay a single row without subphases.
- Name the two main phases plainly: **Tests** and **Implementation**. The imperative naming applies only to subphases and to other short phases: name every subphase and every phase of 2 days or less as an **imperative work order** (like a commit-message headline, e.g. "Implement the safe rename service", "Write headless engine unit tests"). No TDD references, no parenthetical comments, no annotations in the table — just the work order and the numbers.
- **No explanations below the table**: no rationale lists, no per-number justifications, no commentary. The table stands alone; the only permitted additions are the audience assumption and the buffer statement in the intro sentence(s) above it.
- Make every row with an estimate **of 2 days or less collapsible**: wrap the row label in `<details><summary>NAME</summary><div class="jira">...</div></details>`. The hidden `.jira` block contains exactly three sections, one `<p>` each: **Objective:** (the primary goal), **Key deliverables:** (the expected output), **Risks & dependencies:** (incl. the concrete risk if the work is left undone). Never mention documentation or tests in these descriptions unless the entire task is about them, and never mention Jira by name.
- Each collapsible row ends its `.jira` block with a `.btnbar` containing two buttons (`.jtitle-btn` "Copy Title", `.jdesc-btn` "Copy Description") — wired in the template script; the description is copied as plain text with the title on the first line, formatted for direct pasting into a ticket system (the description copies only the three sections, without the title). The template script hoists the buttons out of the closed `<details>` and floats them at the right of the row, so titles always wrap before the buttons (never underneath) and the buttons are reachable without expanding the row first.
- Include ENOUGH BUFFER so there is no realistic risk of exceeding the estimate. Buffer must be explicitly visible, not hidden in the numbers.

## Shared Rules

- Loading JavaScript via CDN is permitted (Mermaid etc.). Everything else must be inline.
- IF DATABASE TABLES ARE RELEVANT: provide them BOTH as a code snippet (`CREATE TABLE ...`) AND as an ERM diagram (Mermaid `erDiagram`) that includes their relationships to ALREADY EXISTING tables.
- Code examples taken from existing files MUST always be labeled with the exact source: file path AND line range (e.g. `src/tools/asset_validator.py`, lines 41–57).
- Complex implementations and code snippets MAY be simplified as pseudocode — but every such mechanism must appear BOTH as (pseudo)code AND as a flow diagram.
- Mark all assumptions as `[ASSUMPTION: ...]` and open questions as `[OPEN QUESTION: ...]`.
