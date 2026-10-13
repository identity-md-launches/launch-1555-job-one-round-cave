# Pepeolithic cave wall site

Static export of the Pepeolithic cave wall: four story lines and one gathering
wall, each a folder of numbered records (`NN.json`) and thumbnails (`NN.jpg`)
under `dist/`. The site is served exactly as committed; there is no build step,
no framework, no bundler and no runtime dependency.

Hosted name: `pepeolithic-base-naij.site.identitymd.eth`.

## What this round changed

The previous export saved the records of rounds 2 to 21 of every line under the
numbers 22 to 41, while slots 02 to 21 still held a placeholder record named
"Not painted yet". This round fills those slots and changes nothing else:

- For each line `N` in 1 to 4 and each slot `02` to `21`, `dist/line-N/<slot>.json`
  is a copy of `dist/line-N/<slot+20>.json` whose `Number` attribute is the slot
  number (source number minus 20). Name, image and every other attribute are
  unchanged; the source file's own JSON formatting (pretty or compact) is kept.
- `dist/line-N/<slot>.jpg` is a byte-identical copy of `dist/line-N/<slot+20>.jpg`.
- 80 JSON files and 80 JPEG files were written. The sources 22 to 41 are untouched.
- `dist/index.html`, `dist/goals.json`, `dist/zero.json`, `dist/collection.json`,
  `dist/gathering/`, slot 01 of every line, and everything under `artifacts/`,
  `line-1/` to `line-4/`, `gathering/` and `shared/` are byte-identical to the parent.

No image was generated, downloaded, converted or modified.

## Install

Nothing to install. The export is plain HTML, JSON and JPEG. Clone the
repository and serve `dist/` with any static file server.

## Preview

From the repository root:

```sh
python3 -m http.server --directory dist 8080
```

Then open `http://localhost:8080/`. All asset URLs in `dist/index.html` are
relative (`line-1/22.jpg`, `goals.json`), so the export also works from a
gateway subpath or an ENS name.

## Rebuild

The gallery page is produced by `gathering/build_gallery.py`, which reads the
records under `dist/` and rewrites `dist/index.html` and `dist/goals.json`:

```sh
python3 -B gathering/build_gallery.py
```

This round deliberately did **not** run it: the assignment required
`dist/index.html` to stay byte-identical to the parent's. A future round that is
allowed to regenerate the page should run the command above so the page lists
the now-filled slots 02 to 21 as painted records instead of under the
"unpainted places" disclosure.

## Validation performed in this round

Commands were run from the repository root. Checking scripts lived in
`test/scratch/`, which is not part of the submission.

| Check | Command | Result |
| --- | --- | --- |
| Fill slots | `python3 -I test/scratch/fill_slots.py "$PWD"` | wrote 80 json + 80 jpg files; aborts before writing if any source is missing or named "Not painted yet" (none were) |
| Verify slots | `python3 -I test/scratch/verify_slots.py "$PWD"` | checked 80 slots, 0 failures: same name and image as source, Number equals slot as an integer, every other attribute equal, JPEG sha256 equal to source |
| Scope check | `git status --short` filtered | only the 80 modified `.json` and 80 new `.jpg` under `dist/line-{1..4}/{02..21}` plus this README and `DESIGN.md`; nothing else changed |
| Bundle size | trial commit + `git bundle create` | about 22 KB for the change set, because identical JPEG copies share one Git blob with their source |
| Production build | none | not applicable: static export, no build step |
| Typecheck | none | not applicable: no TypeScript or JavaScript source |
| Design probe | `IMD_PLAYWRIGHT=$HOME/.imd-taste/node_modules/playwright/index.mjs node .imd/reads/skills/design-critic/scripts/taste.mjs --out test/scratch/taste` | ran at 320, 390 and 1440 wide; results below |

### Design probe results

Passed: render (no script errors, no missing local files), layout (no
horizontal scroll at any width, no overlaps, no clipped text), targets,
contrast (all measured text meets 4.5:1), type-sizes, type-faces, glyphs,
slogans, copy-budget, chrome, motion.

Failed, all located in `dist/index.html`, which this assignment requires to
stay byte-identical, so they are recorded and not fixed:

- `casing`, `tracking`, `eyebrows`: the `.eyebrow` kicker (uppercase, 0.12em
  tracking) sits above the page heading and above every card heading.
- `repetition`: the disclosure summary "20 unpainted places · newest slot first"
  appears once per wall. After this round those slots are in fact painted, but
  the page text cannot be regenerated in this round (see Rebuild).
- `share`: no favicon, description, og:title or og:image in the head.

First screen at 390 wide (confirmed on the probe's screenshot): kicker, the
headline "Four lines. One gathering.", one line of explanation, and the wall
links Line 1 to Gathering plus Goals JSON. The first card of Line 1 begins
below the fold. Horizontal scroll: none at 320, 390 or 1440.

### Better Interface review

Coverage: the six domains were checked without a browser against the source of
`dist/index.html`, and with the probe's rendered measurements above.

- Accessibility: skip link, `lang`, viewport meta, landmark `nav` with
  `aria-label`, sections labelled by their headings, descriptive `alt` text on
  every card image, visible focus outline. Pass.
- Layout: single column up to the auto-fit grid minimum, no fixed widths, no
  overflow. Pass.
- Writing: short headline and one plain line; the repeated disclosure label is
  the one finding (above).
- Typography: two families, six sizes with one-offs; kicker tracking finding
  (above).
- Colors: four-token dark palette, measured contrast passes.
- UI: cards, links and disclosures only; no custom controls.

Findings in `dist/index.html` cannot be applied in this round; they are listed
above for the next round that may regenerate the page.

### Limitations

- `dist/index.html` still presents slots 02 to 21 under "unpainted places" and
  links them to the record JSON. The linked JSON now holds the painted records.
- Primary interactions (anchor navigation, disclosure toggles, record links)
  were checked by reading the source and by the probe's render pass; no manual
  click-through was recorded.
- The share metadata and kicker findings remain in the page by assignment scope.
