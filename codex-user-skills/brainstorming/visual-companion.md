# Codex Visual Companion Guide

Use this guide when a brainstorming step benefits more from a visual artifact than from plain text.

## When to Use

Use a visual companion only when the user is choosing between layouts, diagrams, flows, or other spatial/visual alternatives. Keep purely conceptual or technical tradeoff discussions in the terminal.

## Codex-Oriented Approach

1. Create a lightweight visual artifact such as HTML, SVG, or a diagram file inside the workspace.
2. Prefer static artifacts first. If the user needs live iteration, you may use the local helper scripts in this directory.
3. If you run the helper server, manage it explicitly with shell commands and confirm where its output files live.
4. Summarize in the terminal what is being shown and what decision the user should make.
5. Return to terminal-first interaction as soon as the visual decision is resolved.

## Practical Guidance

- Default to small, disposable artifacts.
- Use semantic file names and keep versions separate instead of overwriting the same file repeatedly.
- Avoid long-lived local servers unless they materially improve the interaction.
- If the helper scripts in `scripts/` are used, treat them as local utilities rather than product-integrated workflow requirements.

## Output Expectations

- A concise summary of what the visual shows
- The exact decision the user should make
- The file path or local URL, if one was created
