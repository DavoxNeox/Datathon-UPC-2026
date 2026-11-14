# Review of the Duolingo-like restyle (`ui-lesson`, on `origin/main` at 7340c8d)

Scope: `assets/index.html`, `app.js`, `style.css`, `theme.css`, the restyle notes in
`docs/ui/redesign.md` and `research.md`. No new capture was committed (the notes describe the
screens), so there is nothing to check for M3Kang content. Nothing changed by me.

**Executed**: the suite (284 OK, 1 skipped); the sim server on port 7011 and the built-in browser
at 1280x800 and 390x844, light and dark: contrast of every token pair computed in the page, the
size of every visible control, the geometry of the fixed action sheet against the option cards
and the last content at maximum scroll, keys C, Enter and Tab, the picture zoom in place, the
inline two-step "Canvia d'alumne" (one click, four-second timeout, two clicks), the course
dropdown with mouse and keyboard, the resource list for external loads, `/api/state` for the
label before answering. **Only read**: the pressed-state transform, the manipulative box.

## Executive summary

1. **Everything the controller listed holds.** Text contrast is AA in both themes (lowest 4.68:1,
   `--ok` on `--ok-bg`, used for the verdict and inverted on the green CONTINUA); control borders
   `--control` are 3.39:1 on the page in light and 4.16:1 in dark (the page and the cards now share
   one background, so card and page ratios coincide). Every visible control is at least 44 px
   (option cards 84 px, 68 on the phone; sheet buttons 50 and 44; dropdown rows 46). Focus is a
   3 px accent outline on `:focus-visible`. Keys A-E, P, T, N and now Enter work. No external
   resource (163 loaded, all same-origin). The label never appears in `/api/state` before the
   answer.
2. **The sheet never covers the answers.** At 1280x800 the option cards end at 429 px and the
   sheet starts at 714 px (695 px once it turns green, 106 px tall); at 390x844 the cards end at
   467 px, the sheet starts at 635 px (210 px tall after the verdict), no horizontal scroll, the
   last content at maximum scroll clears the sheet. The main column reserves 140 px (170 on the
   phone) under the content.
3. **Zoom in place works**: the figure gains `zoomed`, scrolls sideways inside its own box (1124 px
   of content in 884 px on the laptop, 354 on the phone), grows 26 px in height, never widens the
   page; a second click shrinks it.
4. **"Canvia d'alumne" cannot fire on one click**: the first press turns it red with "Segur? Esborra
   el progrés" and the session stays started; after 4.6 s it reverts; two presses erase and return
   to the start screen.
5. **The course dropdown opens in the flow** (static list, 9 rows of 46 px, pushes "Comença" from
   437 px to 875 px), ArrowDown opens and moves, Enter chooses, Escape closes and returns focus,
   `role="listbox"` and `aria-selected` are set; the hidden `<select>` keeps the value.
6. The current topic's progress is now a 16 px bar in the top bar, always visible: the two
   "V3 clicks Més" instructions in `pitch.md` (40 s and 60 s) are no longer needed.

## Findings

**R1 (MINOR, computed, not reproduced with tall content). On a phone the sheet after the verdict
is taller than the reserved padding.** `style.css`: `main { padding-bottom: 170px }` under 640 px,
measured sheet height 210 px in the `ok` state (verdict on its own line, CONTINUA full width,
status line). With a long page (hints open, text shown) the last 40 px of the last hint card sit
behind the sheet at maximum scroll. *Fix:* `padding-bottom: 220px` on the phone, or hide the status
line once the verdict is in.

**R2 (MINOR). The sheet's boundary is nearly invisible.** `.sheet { background: var(--card);
border-top: 2px solid var(--line) }` with `--card == --bg`: the line is 1.1:1 in light and 1.3:1 in
dark, so before the verdict the bar is the page with two buttons at the bottom. The buttons
themselves carry the 3:1 border, so nothing fails WCAG, but the "lesson bar" the restyle wants is
not perceived until it turns green or red. *Fix:* `--control` for the top border, or `--card-2` as
the sheet's background.

**R3 (MINOR). After "Canvia d'alumne" the drawer keeps the erased student's map.** `render()` returns
before `renderMastery` when `started` is false, so "El teu progrés" still shows the previous bars
on the start screen while the drawer is open (seen after the two-click reset: Taulers with two
segments). *Fix:* clear `#mastery` and the LED on reset, or render the map whenever the drawer is
open.

**R4 (MINOR). The pitch's click column is one screen behind.** `docs/demo/pitch.md` rows 40 and 60
ask V3 to open Més to show the progress; the bar at the top now shows it. Remove the two clicks
(they cost 4 s of the demo block).

**R5 (MINOR). Open dropdown pushes "Comença" below the fold at 800 px.** 875 px top on an 800 px
viewport; harmless because choosing closes the list, and the start screen is prepared before the
pitch, but a scroll appears while the list is open.

## Checks

| Check | Result |
| --- | --- |
| text contrast light / dark (min pair) | 4.68 / 5.44 (AA) |
| control border on page, light / dark | 3.39 / 4.16 |
| controls under 44 px | none (1280 and 390) |
| sheet vs option cards, 1280x800 | cards end 429, sheet 714 (695 green) |
| sheet vs content, 390x844 | cards end 467, sheet 635, nothing covered; padding 170 < sheet 210 (R1) |
| horizontal scroll, 390 | none, also with the picture zoomed |
| picture zoom in place | sideways scroll inside the figure, +26 px height, page width unchanged |
| reset one click / timeout / two clicks | armed, reverted at 4.6 s, erased |
| dropdown mouse / keyboard / aria | in flow, Arrow + Enter + Escape, listbox + aria-selected |
| focus ring | 3 px accent on Tab |
| keys | A-E, P, Enter (continue) verified; T, N unchanged |
| external resources | 0 of 163 |
| `label` before answering | absent |
| new captures | none committed |
| tests | 284 OK, 1 skipped |

## In one line

The restyle passes every accessibility and safety check it was asked for; the remaining items are
40 px of phone padding, a sheet boundary that cannot be seen, a stale drawer after reset, and two
clicks the pitch no longer needs.
