---
name: mermaid-to-excalidraw
description: "Convert every Mermaid diagram in a Markdown document into its own editable Excalidraw document. Use when asked to export, redraw, or convert Markdown Mermaid diagrams to Excalidraw (.excalidraw)."
argument-hint: "Markdown file to convert"
---

# Markdown Mermaid to Excalidraw

Create one native, editable Excalidraw document for every Mermaid diagram in the requested Markdown file.

## Workflow

1. Identify the Markdown source from the user's request or `$ARGUMENTS`. If it is ambiguous, ask which file to convert.
2. Read the entire source and find every fenced code block whose info string starts with `mermaid` (case-insensitive). Preserve their source order. Do not mistake other code blocks or inline Mermaid snippets for diagrams.
3. If there are no Mermaid blocks, report that and do not create output files.
4. Before drawing, inspect any user-provided `.excalidraw` examples or expected-output files. Treat their per-element style and binding patterns as the visual and structural reference, and apply those patterns consistently to every Mermaid diagram type while keeping each diagram's appropriate layout. If no reference is provided, use the shared style and binding rules below.
5. Translate each diagram into Excalidraw's native scene elements: shapes, text, lines, and arrows. Do not use a screenshot, flattened SVG, or Mermaid source as the diagram; users must be able to select and edit its parts in Excalidraw.
6. Preserve the diagram's labels, participants/nodes, relationships, direction, grouping, and meaningful visual distinctions. Choose a readable layout with enough spacing to avoid overlaps. Keep connectors behind nodes and labels where possible.
7. Save one `.excalidraw` file per block beside the Markdown source. Use `<source-name>-diagram-<two-digit-number>-<short-title>.excalidraw`; derive the short title from the diagram or its nearest Markdown heading, and make it filesystem-safe. Never overwrite an existing file: choose an available numbered suffix and report the actual path.
8. Validate every output by parsing it as JSON, checking that it has an Excalidraw scene structure (`type: "excalidraw"`, `elements` array, `appState` object, and `files` object), and checking unique element IDs, finite geometry, valid element types, and valid element references. Fix validation errors before reporting success.
9. Report the number of diagrams converted and link every generated file. Mention any syntax or visual detail that could not be represented faithfully; never silently omit content.

## Sample fixtures

- Use the Markdown files in [`./samples/`](./samples/README.md) as representative source fixtures when exercising or checking Mermaid diagram-type coverage. Each diagram family has its own file and may contain multiple examples.
- These fixtures are inputs for conversion, not expected Excalidraw outputs; do not overwrite or convert them unless the user asks.

## Shared style

- When the supplied reference scenes use `fontFamily: 5`, use that same value for every meaningful text element: node labels, connector labels, participant names, section titles, notes, attributes, and chart labels. Do not fall back to a different font family or leave the property missing on text elements.
- Use `roughness: 1` as the default for shapes, lines, arrows, and text so different diagram types have a consistent hand-drawn appearance. Match the reference's semantic exceptions: for example, use `roughness: 2` for broad grouping frames and their headings when the reference distinguishes those from the `roughness: 1` component nodes and connectors. A reference may instead use `roughness: 1` throughout, as in a sequence diagram.
- Apply these rules to all diagram types, not only flowcharts. Preserve explicit per-role font and roughness choices from a supplied reference across nodes, sequence participants, class compartments, states, entities, timeline tracks, chart labels, and connector annotations.
- Set style properties explicitly on every element. Do not rely on Excalidraw defaults or copy accidental helper/artifact elements (such as a stray single-character label) from a reference.

## Bindings and labels

- Use native Excalidraw bindings whenever elements have a real containment or connector relationship; do not leave related labels floating when the reference binds them.
- Text inside a node, participant header, class compartment, state, entity, or grouping frame must set its `containerId` to the containing shape's ID. Add the reciprocal `{ "id": "<text-id>", "type": "text" }` entry to that shape's `boundElements`.
- A connector label must set its `containerId` to the arrow/line ID, and the connector must list the label in `boundElements` as `{ "id": "<text-id>", "type": "text" }`. Keep connector labels legible and positioned with their connector.
- Bind arrow/line endpoints to the actual node shapes they connect to using `startBinding` and `endBinding` objects with valid `elementId`, `focus`, and `gap` values. Add the reciprocal `{ "id": "<connector-id>", "type": "arrow" }` entry to each bound shape's `boundElements`. Use `"line"` instead of `"arrow"` when the bound connector is a line.
- Binding is semantic, not decorative: do not bind unrelated items just to reproduce a pattern. For example, free-standing annotations can remain unbound, and sequence lifelines need not bind to participant boxes unless that connection is meaningful.
- Keep every binding reciprocal and valid: each `containerId`, `elementId`, and `boundElements` ID must point to an existing, non-deleted element of the expected type. Remove stale, empty, or one-sided references. Ensure each relationship appears only once in `boundElements`.

## Diagram translation

- **Flowcharts and graphs:** map process nodes to rectangles, decisions to diamonds, terminators to ellipses, and relationships to arrows. Preserve edge direction and labels; bind node text and arrow labels as described above.
- **Sequence diagrams:** use participant headers, vertical lifelines, horizontal message arrows, and activation boxes when present. Distinguish synchronous, asynchronous, and return messages where possible; retain message order and notes. Bind participant names to headers and message labels to their arrows.
- **Class diagrams:** use class/interface boxes with separate name, attribute, and operation sections; preserve inheritance, implementation, association, multiplicity, and labels. Bind text to its class box or compartment.
- **State diagrams:** represent states as labeled shapes, initial/final states as filled/target circles, and transitions as directed, labeled arrows. Bind state names to states and transition labels to their connectors.
- **ER diagrams:** render each entity exactly once as a native, editable table/card. Use a distinct header with the entity name and one attribute row per Mermaid attribute; do not place a second compact entity box or duplicate attribute summary beneath/over the table.
  - Make the table structure explicit and readable: each attribute row has separate cells for data type, attribute name, and key markers. Preserve every declared attribute and its source order. Mark `PK`, `FK`, and `UK` in the key cell; combine applicable markers (for example, `PK, FK`) and leave the cell visually empty when there is no key constraint. Represent composite keys correctly across all participating attributes.
  - Use the supplied ER reference's hand-drawn visual language: `fontFamily: 5` and `roughness: 1`; pale blue entity/header framing with dark slate borders/text and white attribute cells. Keep a consistent column grid, row heights, padding, and readable spacing. Size each table to its content and leave enough room between tables for relationship labels; never let table rows or labels overlap.
  - Draw exactly one native connector for each Mermaid relationship. Bind its endpoints to the corresponding entity table/card, preserve the relationship direction and name, and attach explicit cardinality labels at the correct ends (for example, `1` and `0..*`). Do not create a second connector to duplicate the same relationship. Keep the relationship name and both cardinalities legible and bound to that connector; route connectors behind tables and avoid crossing labels or attribute rows where possible.
  - Keep all table parts individually selectable and semantically bound: bind each cell's text to its cell shape and each cell shape/row to the entity table when supported by the chosen Excalidraw structure; bind the entity title to its header. Use reciprocal references, and bind relationship endpoints to the outer entity shapes rather than to attribute cells. Do not use a single multiline text block as a substitute for separately editable attribute rows.
- **Mind maps:** place the root prominently and arrange branches hierarchically, keeping each parent-child relationship clear. Bind branch labels to their nodes and connectors to the nodes they join.
- **Other Mermaid diagram types:** represent their data and relationships with the closest clear native Excalidraw primitives (for example, axes and marks for charts, lanes and bars for timelines). Preserve all meaningful text and values, apply the same font/roughness and binding rules, and disclose any unavoidable loss of specialized styling.

## Excalidraw scene requirements

- Write a standalone `.excalidraw` JSON scene, not Markdown containing a diagram.
- Use unique IDs for all elements and valid native element types. Give every element explicit finite `x`, `y`, `width`, and `height` values (line/arrow paths must also have valid points). Keep dimensions positive where the element type requires them.
- Create diagram text as native text elements with readable font sizes. Position labels with their nodes/connectors; do not rely on Mermaid fonts, CSS, or external assets.
- Use native arrows/lines for connections and retain arrowheads and connector labels as scene elements. Avoid external assets.
- Include the standard top-level Excalidraw fields (`type`, `version`, `source`, `elements`, `appState`, and `files`) and the required standard fields for each chosen element type. Use an established Excalidraw serializer or an available converter if one is already present; otherwise construct and validate the JSON carefully. Do not add dependencies or send source content to external services just to perform the conversion.
- Before saving, validate all binding references in both directions, along with the JSON, scene structure, element IDs, and geometry. Do not report success if a binding points to a missing, deleted, or wrong-type element.

The generated file can be opened directly in Excalidraw. To insert its editable elements into another canvas, open the generated file, select and copy the elements, then paste them into the target canvas.
