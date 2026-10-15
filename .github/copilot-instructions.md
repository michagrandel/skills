# Copilot instructions for this repository

This repository is a collection of Copilot agent skills. Each top-level folder is one skill and is self-contained.

## Repository layout

- Each skill lives in its own folder, e.g. `tdd/`, `clean-code/`, `plan-feature/`.
- Every skill has a `SKILL.md` entry point with YAML frontmatter:
  - `name`: must match the folder name.
  - `description`: states what the skill does and the trigger phrases/situations in which it applies. Keep it specific, because it decides when the skill is loaded.
- Supporting material goes into subfolders of the skill:
  - `references/` for templates and contracts (HTML templates, `task-contract.md`).
  - `scripts/` or top-level `.py`/`.ps1` files for executable helpers.
  - `renderers/`, `samples/`, `fonts/` for assets used by a skill.
- Skills must not depend on each other's files. Copy shared material instead of referencing another skill's folder.

## Working on skills

- Edit an existing `SKILL.md` instead of creating a parallel file. Use relative paths for references to files inside the same skill.
- When changing a skill's behavior, update its `description` if the trigger conditions change.
- When adding a skill, create a folder with a `SKILL.md` that has both `name` and `description` frontmatter, then add it to the skill table in [README.md](../README.md).
- Keep `SKILL.md` instructions imperative and specific. Do not add generic advice that the model already knows.
- Do not add planning, notes, or tracking Markdown files to the repository unless asked.

## Scripts and assets

- Python helpers (`mermaid-to-images`) and PowerShell helpers (`convert-feature-plan-to-obsidian`) should run from the skill folder with relative paths and print clear errors.
- Do not commit generated output such as rendered PNGs, `.excalidraw` files, or converted notes unless a skill's documentation says to ship them.
- Do not commit secrets, tokens, or machine-specific paths.

## Validation before committing

- For Python changes in `mermaid-to-images/`, render a diagram from `mermaid-to-images/samples/` or a small Markdown file containing a Mermaid block, and confirm that the output image is produced.
- For PowerShell changes in `convert-feature-plan-to-obsidian/scripts/`, run the script against an HTML plan and check the Markdown output.
- For Markdown-only changes, check that the frontmatter is still valid and that relative links resolve.

## Commits

- Use short, imperative commit messages describing the skill or area changed, e.g. `Add tdd skill` or `Clarify clean-code review scope`.
- Include the `Co-authored-by: Copilot <223556219+Copilot@users.noreply.github.com>` trailer unless told otherwise.
