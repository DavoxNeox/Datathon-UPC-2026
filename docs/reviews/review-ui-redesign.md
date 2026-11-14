# Review of the student-page redesign (`team/ui-redesign-48906b`, on `origin/main` at 7a67b77)

Scope: `assets/` (index.html, app.js, style.css, new theme.css and theme.js, teacher.html, the three
manipulatives), `docs/ui/redesign.md`, `docs/ui/research.md`, the seven PNG captures, the
`HINT_MAX_USES` cap and the Catalan corrections in `copilot/webapp.py`, `hints.py`,
`solvers/average.py`. Reviewed with the demo in front: the Mariona1 chain on the new page.

**Executed**: the suite on `origin/main` (181 OK); the sim server on port 7008 driven with `curl`
(start, four hint clicks, solution) and with the built-in browser (keys C, Tab, N, P, A, Escape;
the "Més" panel; the theme button three times; the mobile preset 375x812); WCAG contrast ratios of
every token pair computed in the page for light and dark; sizes of every visible control; the
network log (82 requests) and the console; the seven captures opened one by one. **Only read**:
`research.md` (Mobbin links not followed), the phone captures the author describes but did not
commit.

## Executive summary

1. **License: clean.** The seven committed PNGs show the start screens (light and dark), the
   teacher view (test pseudonyms only) and the rotate manipulative with a hand-drawn shape. No
   M3Kang statement, scan or option appears; `.gitignore` now excludes every capture pattern that
   would. Nothing critical.
2. **Offline, label-free, tested.** Only `theme.css`, `style.css`, `theme.js`, `app.js` and `/api/*`
   load, all from the board; no font, CDN or `url()`. `/api/state` carries no `label` for the problem,
   the neighbour or the translation (the letter appears only after an answer or on `Solució`, as
   before). The hint cap works: the three dots count down, the fourth click is refused with the
   bilingual message and the button is disabled at zero while `Solució` and rung 0 stay.
3. **Accessibility: text passes, boundaries do not.** Every visible control is at least 44 px
   (letters 68 px, 60 px on a phone), the focus ring is a 3 px accent outline on `:focus-visible`,
   the keys A-E, P/H, N, T and Escape work, no horizontal scroll at 375 px. Text contrast is AA in
   both themes (lowest: `--ok` on `--ok-bg` 4.68:1 in light, `--accent` on `--accent-soft` 4.80:1;
   dark is above 5.4:1 everywhere). But the answer buttons' boundary is `--line` on `--card` at
   1.34:1 (dark 1.31:1) and the card on the page is 1.06:1: WCAG 1.4.11 asks 3:1 for a control's
   boundary. On a projector the five letters are five faint rectangles.
4. **Dark mode and the picture.** The scan keeps its white card dimmed to 86%; readable in the
   browser and in my dark screenshot. The theme button cycles auto/light/dark, persists in
   `localStorage`, and announces its state.
5. **The demo documents are now out of date in three places.** "Reinicia l'alumne" is "Canvia
   d'alumne" behind "Més" (runbook §5, contingency row 3); the LED drawn on the page and the
   progress bars are behind "Més" too, so contingency row 5 ("V3 points at the matrix drawn on the
   page") and the two script moments about mastery (48 s "el domini de taulers puja", 70 s "el
   domini d'espacial queda a u") have nothing visible on the projector unless V3 opens the panel.
6. The redesign kept the two behaviours the main review called critical: one wrong click shows the
   correct letter in green with "La resposta correcta era la E", and `Solució` is one click, now a
   quiet text link.

## Findings

**U1 (IMPORTANT). Answer buttons fail non-text contrast.** `assets/style.css` `.letters button`
(2 px `--line` on `--card`), tokens in `theme.css`. Measured 1.34:1 light, 1.31:1 dark; card against
page 1.06:1 light. *Fix:* border `--muted` (5.8:1) or a dedicated `--control-line` around 3:1
(`#8a8f99` on white is 3.3:1), or fill the buttons with `--card-2`; keep the hover accent.

**U2 (IMPORTANT). The demo script and runbook name controls that moved.** `docs/demo/runbook.md`
§5 and §10, `contingency.md` rows 3 and 5, `pitch.md` rows 48 and 70. In the new page the reset is
"Canvia d'alumne" inside "Més"; the LED canvas and "El teu progrés" are inside "Més". The panel is a
fixed overlay on the right that covers the E button and part of the figure at 1280 px, so it cannot
simply stay open. *Fix:* in `pitch.md` give V3 a click on "Més" at 46 s and 69 s (two seconds each)
or move the progress segments back under the letters; update the two documents' button names.

**U3 (IMPORTANT). The reveal after a wrong answer is kept, and styled.** `app.js:renderAnswer`
marks `a.label` green; `webapp.py` sends "No és aquesta. La resposta correcta era la X". Same as
review-main C3; the redesign was the moment to add the second attempt the Bastani reference calls
for. `Solució` as a `.link` is quieter than before, which is good, but still unconfirmed (C2).

**U4 (MINOR). The contrast figures in `docs/ui/redesign.md` are not the measured ones.** Doc: ink
14.6, muted 5.6, accent 5.9, ok 5.1, bad 5.7. Measured on the page: 15.5, 5.78, 5.63, **4.68**,
5.66. All pass, but `--ok` is 0.4 below what the doc claims and 0.2 above the AA line; `#16703f`
gives about 5.2:1. Correct the numbers or the token.

**U5 (MINOR). The statement text opens by default according to the window width at load only.**
`app.js` `let textOpen = matchMedia("(max-width: 640px)").matches` runs once. In my session the
pane was narrow when the page loaded and the text stayed open at 1024 px, so the scan and the same
sentence appear twice. On stage: open the page after the projector is connected and the window is
full screen (add to runbook §8), or re-evaluate on `resize`.

**U6 (MINOR). No live region for the verdict.** The theme button has `aria-live`, the band that
says "Molt bé, correcte!" / "No és aquesta…" does not; a screen reader hears nothing after an
answer. `aria-live="polite"` on `#verdict` is one attribute. `.letters button.chosen` in
`style.css` is never applied (dead rule).

**U7 (MINOR). Pseudonym label.** "Nom o àlies" invites real names on a page whose teacher view
is open to anyone on the LAN; the design is pseudonymous. "Àlies (no cal el nom)" keeps the hint
and the privacy.

**U8 (MINOR). "Més" panel.** Escape closes it, `aria-expanded` and `aria-controls` are set; it has
no focus trap and the teacher link opens in the same tab (the demo uses a second tab, fine). The
problem id moved to "Temps (per al professor)", which the runbook's id check does not need.

## Checks

| Check | Result |
| --- | --- |
| captures in `docs/ui/*.png` free of M3Kang content | 7/7 clean |
| external loads | none: 2 css, 2 js, `/api/*`, all 127.0.0.1; no `url()`, `@import`, font |
| `label` in `/api/state` before answering | absent (problem, neighbour, translation) |
| controls ≥ 44 px | all (44, 48, 68; 60 on phone) |
| focus visible | 3 px solid accent on Tab |
| keys A-E, P, N, T, Escape | work; Enter on the start field unchanged |
| text contrast light / dark | min 4.68 / 5.44 (AA) |
| control boundary contrast | 1.34 / 1.31 (fails 3:1) |
| picture in dark | white card at 86%, legible |
| phone 375 px | no horizontal scroll, letters 62x60, text open by default |
| hint cap | 3 accepted, 4th refused, dots count down, button disabled |
| theme cycle | auto → light → dark → auto, stored, `aria-label` updated |
| demo click script | Comença, Pista, A-E, Següent problema, Gira i volteja, Tanca still present; reset and LED moved |
| tests | 181 OK, 1 skipped |

## In one line

A calmer, faster page that respects the license and the board; fix the button boundaries, sync the
demo documents with the moved controls, and use the chance to stop revealing the letter after one
wrong click.
