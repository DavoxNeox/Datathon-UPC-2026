# Review of `ui-young` (on `origin/main` at afc8154): the scan cut in the browser

Scope: `assets/app.js` (scanComponents, classifyParts, trimLabel, cropPart, tinted, loadScan),
`index.html`, `style.css`, the notes in `docs/ui/redesign.md`. Checked on the six demo problems
with the real scans, in sim, at 1280x800 and 390x844, light and dark. Nothing changed by me.

**Executed**: the suite (284 OK, 1 skipped); the sim server on port 7012; the three demo chains
(`Mariona1`/1, `Guillem`/2, `Pau`/3) in the built-in browser; for each problem the crop
re-run on the fetched scan with timing, the rendered figure measured and zoomed in both
themes, the option rows read back, the fallback forced by hand (`scan.whole`), the menu
sidebar geometry, keys P, Enter, Tab and T, the control sizes, the phone layout.
**Only read**: the component classifier's thresholds; the 34-scan check the author reports.

## Executive summary

1. **On five of the six demo problems the cut is right and fast.** `lvl-1_2024_2`: the whole 8x5
   grid, 328x216 px, 7 ms to cut and 7 ms to tint. `lvl-3_2019_18`: the three drawings with the
   arrows and the scissors, 460x140, 3 ms; legible in dark. `lvl-2_2020_4` and `lvl-4_2010_12`
   (text only): no figure, no strip, no whole scan, as it should be. `lvl-5_2022_30`: the hand with
   the three rings, 154x232 drawn at 1.6x, 3 ms. Options as text rows A to E in the right order
   everywhere the OCR was clean. Cut plus tint never passed 14 ms on the laptop.
2. **The sixth fails twice.** `lvl-3_2021_20` (the reserve, known for its garbled OCR): the
   "figure" crop is 912x232 and contains the right half of the scan's option row ("¹¹⁄₂ cm²  D) 6
   cm²  E) 4 cm²") next to the square; and the option rows show the OCR garbage as text ("A 3cm2",
   "C 2 11 cm2", "E 4cm²2") because `optionsClean` accepts any letters, digits and spaces. The
   student reads "2 11 cm2" for an option that is 11/2 cm².
3. **Dark theme inverts the meaning of black.** Every crop is turned into ink-coloured alpha: in
   dark the black corner squares of `lvl-3_2021_20` render light grey while the statement says
   "quadrat petit (negre)". The grey triangles stay grey. Any problem whose text names black,
   white or shaded regions is contradicted by its own figure in dark.
4. **Five option rows of 64 px do not fit above the sheet.** At 1280x800 row E starts at 721 px
   and the fixed sheet at 722: on the first problem of the demo the jury sees four options until
   someone scrolls (with the hand figure, three). At 390x844 two rows are hidden at load; all are
   reachable by scrolling, nothing is covered at the end of the scroll.
5. **The whole-scan fallback is not recognisable.** Forced by hand, the 1653x248 scan is drawn
   408 px wide, 61 px tall, under the same `figure` class: a strip whose text is 7 px tall, with no
   caption, no zoom and nothing that says "this is the original". A ten-year-old sees a smudge.
6. **Rung 0 regression confirmed.** `app.js` and `index.html` have no `translate`; the T key
   leaves `translation` null while `translation_available` is true; the route and the teacher
   section remain. The redesign note states it as a decision ("the language changes in the menu"),
   which loses the bilingual rung the team measured and the Hub draft describes.
7. The rest holds: menu sidebar fixed on the left (16 to 346 px) and the page pushed to 378 px,
   nothing covered; focus ring on Tab; "PISTA · 3" counting down and "LLIÇÓ" on the fourth; hint
   texts as bullets; Pista disables itself at once; every visible control at least 44 px except the
   pre-existing "mostra-ho tot" link (32 px); no horizontal scroll on the phone; no external loads.

## Findings

**Y1 (IMPORTANT). `optionsClean` accepts OCR noise, so garbage reaches the buttons as text.**
`app.js` `CLEAN = /^[\p{L}\p{N}\s....]+$/u`. `lvl-3_2021_20` options `3cm2 / 7 / 2 11 cm2 / 6cm2 /
4cm²2` pass. *Fix:* reject a value with two numbers separated by a space (`\d\s+\d`), a unit glued
to a trailing digit (`cm²\d`, `cm2\d`), or five values whose units disagree; when rejected, fall
through to the per-button cut, which is what the author built for this case.

**Y2 (IMPORTANT). The option band is missed when the options are not evenly spread, and the
leftovers land in the figure.** Same problem: the crop (912x232) holds the square plus "¹¹⁄₂ cm²
D) 6 cm² E) 4 cm²". `classifyParts` groups option bands from text-like components of at least
three pieces spanning 40% of the width; here the fraction and the small superscripts break the
pieces into several heights, so part of the row is text-like and part is not. *Fix:* before
classifying, merge components whose vertical extent overlaps and whose horizontal gap is under
one line height regardless of height; and drop from the figure any component whose top is below
the statement's last line and whose height is under 1.8 line heights when a band was found on
that row. A regression test with this id's scan (kept outside git) would catch it.

**Y3 (IMPORTANT). Ink tinting flips black to light in the dark theme.** `tinted()`: grey pixels
take `--ink`, so black becomes `#e9e7e2` on `#15171c`. Problems that name colours (negre, blanc,
gris, ombrejat) are common in `areas`, `boards` and `spatial`, three of the demo's topics. *Fix:*
keep the white card for the figure in dark (as the previous design did), or tint only line art
(components with low fill ratio) and keep filled regions as they are, or at least detect the
words negre/blanc/gris in the statement and fall back to the white card for that problem.

**Y4 (IMPORTANT). Five rows do not fit above the sheet at 1280x800.** Rows 64 px plus 10 px gaps
under a figure of 150 to 370 px: row E at 721 to 785 behind the sheet (722). On the demo's first
problem the audience sees four options; on `lvl-5_2022_30`, three. *Fix:* when the five options
are short (under 6 characters each, as the demo's are) lay them out as one row of five cards,
as the previous design did; or 48 px rows; or two columns on screens over 1000 px.

**Y5 (IMPORTANT). Rung 0 is gone from the page.** No button, no key, no element for the
translation; `hints.translation`, `/api/translate`, the counters and the teacher section still
exist and the measurement (281/281 pairs, +22% tokens) is in the docs. The redesign note calls it
a consequence of removing the chips. *Fix:* a "Llegeix-lo en anglès" row in the menu sidebar or a
link under the statement, and the T key back; or remove the dead server code and the docs' claim.

**Y6 (MINOR). The fallback is a smudge.** When the cut fails the whole scan is drawn in the figure
box at 408 px: unreadable, unmarked. *Fix:* when `scan.whole` is used, give the figure the old
white card at full column width with the zoom cursor, and a one-line caption ("Enunciat original").

**Y7 (MINOR). Timing is a non-issue on the laptop and worth one measurement on a phone.** 3 to 7
ms to cut, 5 to 7 ms to tint, once per problem and once per theme change; the scans are 1653 px
wide and under 250 px tall. A phone is slower but not two orders of magnitude; the page waits for
`/api/image` anyway.

**Y8 (MINOR). The note says the figure goes under the text on a phone; it goes above it.** At
390x844 the figure sits at 123 px and the text at 363 px. Either is fine; the doc should match.

**Y9 (MINOR). "mostra-ho tot" is 32 px tall** (pre-existing). `.hint .more { min-height: 44px }`.

## Checks

| Check | Result |
| --- | --- |
| crops right and complete | 5 of 6 demo problems; `lvl-3_2021_20` includes option fragments |
| option rows match letters in order | yes on 5; garbled OCR text on `lvl-3_2021_20` |
| text-only problems | no figure, no strip, no whole scan |
| cut / tint time (laptop) | 3-7 ms / 5-7 ms per problem |
| dark legibility of thin lines | good (scissors, arrows, grid, rings) |
| dark meaning of black regions | inverted (Y3) |
| fallback visibility | 408x61 strip, no caption (Y6) |
| sheet vs rows at 1280x800 | row E behind the sheet at load (Y4) |
| sheet vs rows at 390x844 | 2 rows hidden at load, all reachable, no h-scroll |
| menu sidebar | fixed left, page pushed, nothing covered |
| keys | A-E, P, Enter, Escape work; T dead (Y5) |
| controls under 44 px | "mostra-ho tot" 32 px |
| focus ring | 3 px on Tab |
| external loads | none |
| label in `/api/state` | absent before answering |
| tests | 284 OK, 1 skipped |

## In one line

The cut works on the demo's scans and is cheap; fix the OCR gate and the dark inversion before
the demo, give the five options back their single row, and put rung 0 back or delete it.

## Addendum: `ui-fixes-4` on `origin/main` at 832c0af

Checked the same way (sim on port 7013, 1280x800 and 390x844, light and dark), on the six
demo problems again. Tests 284 OK, 1 skipped.

**Closed.**
- **Y5, rung 0.** The T key and the "Llegeix-lo en anglès" button in the Menú sidebar call
  `/api/translate/show|hide`; the English statement and its options appear under the Catalan
  text in grey with the label "En anglès · no compta com a pista"; `hints_left` stays at 4 and
  `rung` at 0 while `rung0.uses` goes to 1; the second press hides it. Regression closed.
- **Y6, the fallback.** "Mostra l'escaneig sencer" (44 px, under the options) shows the full
  scan tinted at the column's width (888 px at 1280: the scan's text is about 16 px, readable)
  and "Amaga l'escaneig" puts it away; when the page fell back to the whole scan on its own the
  link is hidden, as documented. On `lvl-3_2021_20` the link is the way out: the full scan shows
  the real options (A) 3 cm², B) 7/2 cm², C) 11/2 cm², D) 6 cm², E) 4 cm²) where the rows show the
  OCR's text.
- **Restyle minors.** The sheet's top border is `--control` (`rgb(127,133,142)`); the phone
  padding is 190 px (the neutral sheet is 102 px there; the green one measured 210 px on the
  previous build and was not re-measured here); the map is rendered on the start screen too,
  so a reset empties it (code path checked, not exercised with a non-zero map).

**Still open on 832c0af.**
- **Y1 and Y2.** `lvl-3_2021_20` renders exactly as before: option rows "3cm2 / 7 / 2 11 cm2 /
  6cm2 / 4cm²2" (`optionsClean` still true after `tidyOption`) and a 912x232 "figure" that holds
  the square plus three option fragments, now drawn 355 px wide. The link mitigates; the gate
  and the band merge are not fixed.
- **Y3.** In dark the black corner squares are light in the crop and in the full scan alike.
- **Y4.** Rows are still 64 px: row E sits under the sheet at 1280x800 on the demo's first
  problem.
- **New, minor.** The rung-0 button in the sidebar is `.secondary.small`, 40 px tall (the 44 px
  rule); and the link "Mostra l'escaneig sencer" sits between the options and the hints, which
  on the projector reads as a sixth option row until the eye finds it is a link. A chip in the
  figure's corner would be clearer.
