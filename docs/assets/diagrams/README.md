# Diagrams

> Theme-aware SVG diagrams of the `minephys` docs. · Part of: [docs home](../../README.md)

| Diagram | Shows |
|---|---|
| [minephys-modules.svg](minephys-modules.svg) | The planned domain modules, the knowledge tables they read, and the runtimes that use them |

Every diagram is a hand-written SVG with no colour literals in drawing elements: fills and strokes use the palette
tokens declared once in its `<style>` block (light by default, dark under `prefers-color-scheme: dark`), with
`role="img"`, a `<title>` and a `<desc>`. The rules are the same as in the PitStudio documentation
(`https://github.com/fsantibanezleal/PitStudio/blob/main/docs/assets/diagrams/README.md`).

More diagrams are added in the build phase, one per module where a figure helps.
