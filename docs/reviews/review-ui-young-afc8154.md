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

## Addendum 2: `ui-polish` on `origin/main` at aef2a17

Scope asked: Y4 and the five-card row. Checked on the six demo problems in sim (port 7014),
1280x800 and 390x844, light; 284 tests OK, 1 skipped.

**Y4 closed.** On all six problems the five options are one row of cards (`letters short`),
in the order A B C D E, 168x76 px at 1280 (65x64 on the phone, 65x72 on `lvl-3_2021_20`), and
the fifth card's bottom edge sits far above the sheet at load: 321 to 334 px against a sheet top
of 701 px at 1280; 344 to 592 px against 727 px on the phone, even under the tallest figure (the
hand, 232 px on the phone). No horizontal scroll at either size. The letter badge is 12 px
`--muted` on the card, 5.26:1; the value is `--ink`, 14.1:1. The sheet has two columns (message
and Solució on the left; Continua over Pista on the right, 50 px each); after the verdict it is
134 px at 1280 and 126 px on the phone, under the 160 / 200 px reserved, so the last content
clears it at maximum scroll. The figure stays within 30% of the column (15% grid, 29% folded
sheet and square) and the zoom shows the whole figure at up to 760 px wide without widening the
page.

**New, minor (P1).** The figure is also capped at the height of the question's text, so a tall,
narrow figure under a short question becomes a thumbnail: the hand with the three rings
(`lvl-5_2022_30`, reserve chain) is 67 px wide at 1280, 7% of the column; the rings are not
distinguishable on a projector without the zoom (which then makes it 1145 px tall). The two
visual problems of the main chain are wide figures and are fine. *Fix:* cap by the text's height
only when the figure is wider than tall; otherwise allow up to 34vh as before, or drop the figure
under the text when its aspect ratio is above 1.2.

Still open, as assigned to ui-fixes-5: Y1, Y2, Y3 and the two minors of the previous addendum.

## Addendum 3: `ui-fixes-5` on `origin/main` at d2b3107

Checked on the six demo problems in sim (port 7015), 1280x800 and 390x844, light and dark;
284 tests OK, 1 skipped.

**Closed.**
- **Y1 and Y2.** `lvl-3_2021_20`: `optionsClean` now rejects "3cm2", "2 11 cm2" and "4cm²2"
  (`NOISY`), the option band absorbs the numerators and superscripts, and the page shows five
  pieces cut from the scan with the fractions intact (3 cm², 7/2 cm², 11/2 cm², 6 cm², 4 cm²; 66 px
  tall, 168x84 cards, order A-E) and a figure crop of 232x232 that is the square alone. Same on
  the phone (65x84 cards, fifth card at 583 px against a sheet at 727).
- **Y3.** In dark the square with its black corners is drawn as it is on a white card (`figure
  card`, image background white), and so are the five pieces; the grid of `lvl-1_2024_2` (line
  art) keeps the tint. In light everything is tinted, black stays black.
- **Y4** holds on d2b3107 (fifth card 325 to 345 px, sheet 701).
- **The minors**: "veure l'escaneig original" is a small underlined caption, no longer a sixth row;
  the solution scrolls to its card and leaves only "Continua" in the sheet; the menu is a 48 px
  icon fixed at the left edge.

**Letterless buttons.** The letters are present and clipped (`position: absolute; clip: rect(0 0
0 0)`), so the keys A-E and the reading order still work; the `aria-label` is "A: 10" … when the
options are text and only "A" … "E" when the options are scan pieces (the piece images carry no
alt text): a screen reader hears a letter and no value on `lvl-3_2021_20`. For the pitch, the
click column says "clic C": V3 must read it as "the third card, 15"; the audience sees the
chosen value, not a letter, which is fine. *Minor:* give the pieces `alt` from the OCR text when
one exists, or "opció C" otherwise.

**F1 (IMPORTANT). The sidebar closes under a keyboard user.** `app.js` `setPanel(true)` arms
`armClose(1500)` whenever `(hover: hover)` matches; only `mouseenter` cancels it. Measured:
opened with Enter on the menu button and no mouse movement, the panel is hidden after 2.2 s;
opened and then focused inside with Tab, it is hidden after 2.2 s while `document.activeElement`
is still inside it. The sidebar holds CA/EN, the theme, "Llegeix-lo en anglès", the map, the LED,
the teacher link and "Canvia d'alumne", so a keyboard-only student loses them. The same 1.5 s
timer bites a mouse user who opens the menu (button at the top-left corner) and reads without
moving the cursor into the panel, which sits 300 px below. *Fix:* cancel the timer on `focusin`
of the panel or the button and re-arm on `focusout` to outside; do not arm on open when the
opener was a keyboard event (`event.detail === 0`); raise the "never entered" delay to about 4 s
or drop it and rely on leave, Escape and tap-outside.

**P1 still open.** The hand of `lvl-5_2022_30` is 67x101 px at 1280 (7% of the column) because
the figure is capped at the question's text height; the rings cannot be told apart without the
zoom. On the phone it is 358 px wide and fine.

**Touch behaviour not verified here**: the phone emulation still reports `(hover: hover)`, so
the auto-close ran on it too; a tap outside did close the panel. Check once on a real phone.

## Addendum 4: ninth round, no white card (`origin/main` at ff45825)

Checked on the six demo problems in sim (port 7017) at 1280x800, light and dark, by reading the
pixels of each tinted figure back from the page and timing `tinted()` on the raw crops; 285 tests
OK, 1 skipped. `c849c56` (options from the other language) is not exercised by the six demo
problems (all have Catalan OCR options).

**What holds.**
- **Black is never shown as white.** `lvl-3_2021_20` in dark: of 11,024 black pixels in the crop,
  9,136 stay black (the insides of the four corner squares) and 1,888 become the light rim at
  their edges; no pixel of any of the six figures is white (over 245) in dark. In light every
  opaque pixel is ink.
- **Filled shapes read on the dark page**: the black squares sit inside a light rim; the hand's
  ring bands stay black (8% of its opaque pixels).
- **Thin lines stay legible**: the grid of `lvl-1_2024_2` is 98% light strokes in dark, the folded
  sheet 99%; both zoom crisp.
- **Cost**: `tinted()` takes 2 to 10 ms per figure at 1280 (232x232 square 9.5 ms in dark, 2.2 ms
  in light; 328x216 grid 4.2 ms; the five 70x66 pieces 2 to 6 ms each), once per problem and per
  theme change. Nothing a phone or the board's browser would notice.

**G1 (IMPORTANT). Grey does not stay grey, in either theme, and the demo's sixth problem asks
about the grey part.** `lvl-3_2021_20`'s crop has 4,168 neutral grey pixels (levels 60 to 200,
mostly 80 to 120: the eight grey triangles and the anti-aliased edges). In dark 3,320 of them
become the light ink, 820 transparent and 28 stay grey; in light 3,348 become black and 820
transparent. The interior test (`mn < 110` and dark neighbours 3 px away in four directions)
rarely holds inside thin triangles of mid grey, so they are treated as strokes. The student
reads "Quina és l'àrea de la part grisa?" and sees, in dark, whitish triangles between black
squares, and in light, black triangles next to black squares. The round's note says the opposite
("grey stays grey", checked on this id). *Fix:* treat a neutral pixel with `mn` between 60 and
200 as a fill whenever it has at least two neutral neighbours of similar level at 2 px (not four
dark ones at 3 px), and keep its own level in both themes (lightened by a fixed amount in dark
so it reads against the page); or fall back to the white card for crops whose grey share passes
a few percent. Re-measure with this script on `lvl-3_2021_20` after the change.

**G2 (MINOR). Light greys vanish.** The hand of `lvl-5_2022_30` is filled light grey (217) in the
scan; `darkness < 60` makes it transparent in both themes, so the hand is an outline on the page.
Harmless here, but any figure whose light grey carries meaning (a shaded region in a counting
problem) loses it. Lower the noise floor to 40 for neutral pixels inside a closed outline, or
keep 60 and say so in the note.

**Still open**: P1 (the hand is 181x272 px at 1280 now, so the tall-figure cap was relaxed:
closed), the pieces' `alt` text, the two controls under 44 px in the settings popup.

## Addendum 5: thirteenth round, grey patches (`ui-fixes-8`, `origin/main` at 5dbcef0)

Re-measured with the method of addendum 4 on the six demo problems in sim (port 7018) at
1280x800, light and dark: every neutral pixel of the raw crop classed by its level (black under
40, mid grey 40 to 200, light grey 200 to 235) and followed into the tinted image (black under
60, grey 60 to 200, lifted grey 200 to 216, ink 216 to 240, white over 245, transparent); zooms of
the triangles and the hand; `tinted()` timed per crop; crop sizes compared with addendum 3.
304 tests OK, 1 skipped.

**G1 closed.** `lvl-3_2021_20`, dark: of the 4,168 mid-grey pixels (the triangles' anti-aliased
edges and grain), 2,742 come out as lifted grey (the cap of 210), 286 as grey under 200 and 1,140
as the ink rim: 3,028 grey against 28 before. Of the 10,018 light-grey pixels (the triangles'
body, 200 to 235 in the scan), 9,668 come out grey at 210, 144 darker grey, 206 transparent, none
as ink. Light theme: 2,800 + 206 of the mid greys and 7,720 + 2,068 of the light greys stay grey,
1,162 go to the black rim. The zooms show the triangles as a smooth grey surface in both themes,
not a speckle; the UI's own counts (3,060 / 2,944 of 4,104) agree with mine within the class
boundaries.

**Black never white, still.** The square's 11,024 black pixels: 9,136 black and 1,888 ink rim in
dark, all black in light; no white pixel in any figure in either theme.

**G2 closed.** The hand (`lvl-5_2022_30`, fill at 217): in dark 16,952 of its 17,341 light-grey
pixels come out at 210 and the hand reads as a grey surface with a light outline; in light they
stay at 217 on the 244 page, a faint but visible fill (14,553 in the 216-240 band). The ring
bands stay black (129 of 432 black pixels; the rest is rim).

**Thin lines.** The grid's 6,732 black and 7,395 anti-aliased pixels: light ink in dark (98%),
black in light; the zooms are crisp. The folded sheet likewise.

**Cuts unchanged.** 232x232 and five pieces of 72/76/92/70/72 by 66 (square), 328x216 (grid),
460x140 (sheet), 154x232 (hand), nothing for the two text-only problems: identical to addendum 3,
so the statement-continuation and two-row-option changes did not move the demo's crops.

**Cost.** 1 to 11 ms per crop (the 5x5 window pass: grid 11 ms in light, 3.5 ms in dark; square 3
to 5 ms; pieces 1 to 2 ms). Once per problem and theme change; nothing a phone would notice.

**Two remarks.**
- **H1 (MINOR).** In dark the grey patch is capped at 210 and the ink is 231: a gap of 21 lum
  levels between a shaded area and its rim. It reads, but on a projector with a washed-out
  dark theme it will be subtle. Capping at 195 keeps the patch clearly below the ink and still
  above the page (lum 23).
- **H2 (MINOR).** The automatic whole-scan fallback is now drawn untinted (`fig.toDataURL` when
  `scan.figure` is null): the only place a white paper background can still appear, under the
  "Escaneig original" caption. None of the six demo problems triggers it; worth a sentence in the
  round's notes since the brief was "no white background anywhere".
