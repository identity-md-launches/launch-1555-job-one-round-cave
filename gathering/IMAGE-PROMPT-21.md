# Three Kept Together

Generated with the assignment's installed image tool, using medium quality,
1024×1024 PNG and an opaque background. The first transparent-background
attempt returned HTTP 400, “Transparent background is not supported for this
model.” The successful prompt was:

> Use case: historical-scene. A small prehistoric pigment insert for an existing gathering cave wall. On a pure white flat background only: one rough horizontal charcoal cord loop, enclosing exactly three irregular little pebble marks: one red ochre, one yellow ochre, one chalk white. The pebbles are loosely connected by one worn black line, symbolizing an exact bundle of three observations that travels intact. Very simple burnt-stick and thumb strokes, uneven faded powder, flat earth pigments, gaps where bare rock will show. Motif wide and low, about 3:1 aspect ratio centered with ample white space. No shadows, no glow, no gradient, no backdrop or rock. No frog or new hands: the complete cave wall already has the ancestral Pepe. No letters, numbers, caption, signature, logo, watermark, border, frame, political symbols or people. This insert will occupy only vacant lower stone; all ancestor painting and original lighting will be retained exactly.

`finish_wall21.cjs` read the verified Gathering 20 ancestor and the generated
insert, discarded near-white backdrop pixels and area-averaged only pigment
into the vacant rectangle `(480,1145), 215×65`. The generated image was
overwritten by the final wall; no insert image is retained. Only the finished
wall, its identical continuation PNG, and its required JPEG were saved.

The final PNG is 1254×1254, 8-bit RGB. The thumbnail is 512×512 baseline JPEG.
All 4,729 changed pixels are within the addition rectangle. Every ancestral
mark and pixel outside it is preserved. Local review counted five digits
on each inherited Pepe hand; no new hands or handprints were added. No text,
numbers, logos, watermark, signature, frame or prohibited symbols observed.
No known unmet visual requirement. The inherited rock texture remains as
supplied. Exact dimensions, hashes and review are recorded in
`checks/round-21/image-preservation.json`.
