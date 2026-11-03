# Paper notes

Read Paper's current tool guide first. These notes come from earlier builds; check them against what the tools do now.

- **Reusing artwork across files:** copy the markup with `get_jsx` and write it into the new file. Copy whole `<svg>` elements; a bare SVG group once failed to render. Reuse characters or objects, not whole reference slides.
- **Text:** check fonts are available before choosing them. SVG text can ignore font settings, code ligatures can change operators, and text without a width won't wrap; use HTML text where SVG text misbehaves.
- **New artboards:** set `left` and `top` with `update_styles` after creating one, then confirm the position.
- **While building:** work in visual groups and screenshot as you go. After a fix, check the whole slide, because layer order can change meaning (an arrow behind a tile, a prop outside a hand).
- **Several builders in one file:** each touches only its own artboards. `finish_working_on_nodes` releases the nodes; it is not visual approval.
- **File size:** files past roughly 20,000 layers risk data loss. If Paper warns that the file is too large, stop writing to it and continue in a new file.
