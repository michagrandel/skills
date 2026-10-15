# Copilot skills

A collection of personal GitHub Copilot agent skills. Each folder contains a `SKILL.md` that tells the agent what the skill does and when to use it. Some skills also ship templates, scripts, or assets.

## Skills

| Skill | Purpose |
|-------|---------|
| [clean-code](clean-code/SKILL.md) | Apply Robert C. Martin's Clean Code principles when writing, reviewing, or refactoring code. |
| [commit-message](commit-message/SKILL.md) | Generate a concise commit message from staged Git changes or Perforce workspace changes. |
| [convert-feature-plan-to-obsidian](convert-feature-plan-to-obsidian/SKILL.md) | Convert HTML plans from `plan-feature` into Obsidian Markdown notes. Includes `scripts/convert-plan-html.ps1`. |
| [learning-path](learning-path/SKILL.md) | Create project-based learning plans as self-contained HTML, with confirmed learner goals and tasks of at most two hours. |
| [mermaid-to-excalidraw](mermaid-to-excalidraw/SKILL.md) | Convert each Mermaid diagram in a Markdown file into its own editable `.excalidraw` document. Sample diagrams are in `samples/`. |
| [mermaid-to-images](mermaid-to-images/SKILL.md) | Render Mermaid diagrams from Markdown as PNG images, in a dark professional style or a hand-drawn sketch style (`--style sketch`). |
| [plan-feature](plan-feature/SKILL.md) | Produce a pre-implementation feature plan as a single HTML page with Mermaid diagrams and a sticky table of contents. |
| [tdd](tdd/SKILL.md) | Write unit tests first using strict Test-Driven Development, following the Three Laws of TDD and F.I.R.S.T. |

## Layout

```text
<skill-name>/
  SKILL.md          entry point with name and description frontmatter
  references/       templates and contracts used by the skill
  scripts/          helper scripts (where applicable)
  samples/, renderers/, fonts/   assets for specific skills
.github/
  copilot-instructions.md   guidance for working on this repository
```

## Usage

Copy or link the folder into your Copilot skills directory (for example `~/.copilot/skills/`). The agent loads a skill when a request matches its `description`.

Some skills need external tools:

- `mermaid-to-images` is a Python script (`mermaid_to_images.py`) that renders Mermaid diagrams.
- `convert-feature-plan-to-obsidian` is a PowerShell script (`scripts/convert-plan-html.ps1`).

See each skill's `SKILL.md` for setup and options.

## Contributing

Read [.github/copilot-instructions.md](.github/copilot-instructions.md) before changing or adding a skill.
