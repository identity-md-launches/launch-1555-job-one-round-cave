# The Sequence and the Bowl

Used the installed `mcp__image__generate_image` tool for an isolated insert.
Exact prompt:

> A small isolated prehistoric cave-pigment mark for compositing onto an existing wall: three irregular ochre pebbles set in a single ascending trail, each connected to the next by a loose charcoal cord, with a shallow red ochre collecting bowl underneath. Flat hand-drawn red ochre, yellow ochre and charcoal black only, worn uneven thumb-painted pigment with lots of bare negative space. Transparent background if possible, otherwise pure white background; no rock backdrop. Simple primitive Lascaux-style symbolic drawing, NOT realistic objects, no shading or 3D rendering. No frog, people, hands or handprints, no letters, numbers, writing, logos, symbols, signatures, watermark, frame or border. Central compact motif with empty margins. The pebbles in sequence and one bowl symbolize checking a sequence and its combined provisions.

The tool returned a 1199×1312 RGBA PNG. It temporarily occupied the mandated
output path and was replaced by the final whole wall; no separate insert image
is retained. `finalize-41.py` used its actual pixels, cropped only transparent
margins, preserved aspect ratio and blended pigment into vacant left stone at
`(65,240)-(220,385)`. Exactly 4,769 pixels changed, none outside that rectangle.
The inherited rock, cracks, light, framing, Pepes and earlier marks are preserved.

Final `artifacts/line-3/wall-v22.png` and continuation `wall.png` are identical
1254×1254 RGB PNGs. `dist/line-3/41.jpg` is a 512×512 baseline JPEG, 76,029
bytes. Both were visually inspected, including in-memory close-ups of the
inherited hands. Each visible inherited Pepe hand has five digits (four fingers
and a thumb); the new mark has no hands or handprints. No text, numerals,
watermarks, borders, political/hateful symbols or real people were observed.
The inherited stone has a photographic texture; preserving it is required,
and the drawings and new mark are flat earth pigments. No known unmet visual
requirement; this is local visual review rather than independent certification.

The corded stones represent nonce order, and their shared bowl represents the
combined native fee/value budget. Detailed formats, hashes and preservation
counts are in `round-41-review.json`. The one-time compositor requires the
record-40 wall and the generated insert as its inputs; the overwritten insert
is not a runtime dependency of the offline transaction tool.
