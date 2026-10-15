---
name: mermaid-to-images
description: "Extract Mermaid diagrams from Markdown files and render each as a PNG image. Defaults to the professional dark style; use --style sketch for the hand-drawn pastel and paper style. Supports flowchart, ER, sequence, class, state, mindmap, timeline, kanban, pie, git, gantt, quadrant, XY, and journey diagrams."
argument-hint: "[--style sketch] Markdown file(s) or folder [--out output-folder]"
user-invocable: true
---

# Mermaid to Images

Extract every fenced `mermaid` block from Markdown and render each supported diagram as a PNG. The rendering style is the only behavior selected by `--style`:

- **Default (`diagram`)**: professional dark mode, Segoe UI, dark panels, and vivid accent colors.
- **`--style sketch`**: hand-drawn appearance, Patrick Hand lettering, pastel fills, and paper lines.

Both styles use the same Mermaid parsing, layout, supported diagram types, file naming, and output-folder behavior. The internal renderers are bundled as style backends; use the unified entry point rather than invoking them directly.

## Usage

```powershell
# Professional dark style (default)
python "$env:USERPROFILE\.copilot\skills\mermaid-to-images\mermaid_to_images.py" diagram.md [more.md]

# Explicitly select the default style
python "$env:USERPROFILE\.copilot\skills\mermaid-to-images\mermaid_to_images.py" diagram.md --style diagram

# Hand-drawn sketch style
python "$env:USERPROFILE\.copilot\skills\mermaid-to-images\mermaid_to_images.py" --style sketch diagram.md

# Process the Markdown files directly in a folder
python "$env:USERPROFILE\.copilot\skills\mermaid-to-images\mermaid_to_images.py" C:\path\to\folder --style sketch

# Choose an output folder
python "$env:USERPROFILE\.copilot\skills\mermaid-to-images\mermaid_to_images.py" diagram.md --out C:\path\to\output
```

`--style` may appear before or after the input paths. Supported values are `diagram` and `sketch`; an unknown value is an error. Output files are named `<markdown-filename>-diagramm-<n>.png`, where `n` is the Mermaid block's position in the file. By default, images are written beside each Markdown file.

## Requirements

- Python 3 and Pillow (`py -m pip install pillow`).
- The default style uses Segoe UI on Windows and falls back to DejaVuSans.
- Sketch style bundles [Patrick Hand](./renderers/sketch/fonts/PatrickHand-Regular.ttf), with Comic Sans (Windows) and DejaVuSans fallbacks.

## Supported Mermaid Syntax

- **Flowcharts** (`flowchart` / `graph`): `TD`/`TB`, `LR`/`RL` (`BT` is treated as `TB`); stadium, rectangle, sub-process, parallelogram, decision, circle, and cylinder nodes; labeled and chained edges.
- **ER diagrams** (`erDiagram`): entity tables, attributes, key markers, crow's-foot relationships, cardinality, and relationship labels.
- **Sequence diagrams** (`sequenceDiagram`): participants and actors; solid/dashed messages and replies; self-messages; notes; nested `loop`, `alt`, `opt`, `par`, `critical`, and `break` blocks. `autonumber`, `activate`, and `deactivate` are ignored.
- **Class diagrams** (`classDiagram`): class attributes and methods, visibility, stereotypes, inheritance, composition, aggregation, association, dependency, realization, cardinality, and labels.
- **State diagrams** (`stateDiagram` / `stateDiagram-v2`): states, start/end symbols, aliases, descriptions, and transitions. Composite states are flattened.
- **Mindmaps** (`mindmap`): indentation-based trees, common node shapes, and depth-based colors.
- **Timelines** (`timeline`): title, periods, and events.
- **Kanban** (`kanban`): columns, cards, and nested text.
- **Pie charts** (`pie`): slices, optional `showData`, values, and legend.
- **Git graphs** (`gitGraph`): commits, branches, checkout, merges, IDs, and tags.
- **Gantt charts** (`gantt`): sections, tasks, status flags, milestones, dates, and `after` dependencies.
- **Quadrant charts** (`quadrantChart`): axes, quadrants, and points.
- **XY charts** (`xychart` / `xychart-beta`): axes, bars, and lines.
- **User journeys** (`journey`): sections, scored tasks, and actors.

Other diagram types (for example, Sankey, C4, and Packet) are skipped with a notice. `classDef`, `style`, `linkStyle`, `subgraph`, and `click` directives are ignored.

## Rendering Notes

- Both styles render antialiased PNGs with 2x supersampling and share a layered layout heuristic. Dense or deeply nested diagrams may still have crossing edges; simplify their Mermaid source or increase `SX`/`SY` spacing in the relevant bundled renderer if needed.
- Inspect generated images for clipped labels, readability, and arrow direction.
- Unsupported diagram types or blocks without usable elements are skipped with a notice. The layout is a lightweight renderer, not a full Mermaid implementation.
