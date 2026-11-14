# Student page redesign: before, after, decisions

Branch `team/ui-redesign-48906b`, 14 November 2026.

**About the captures.** M3Kang is licensed for research only, so no capture that shows a
problem (its text or its scan) is committed: those files stay on the laptop that made them
(`docs/ui/*problem*`, `*answer*`, `*rung0*`, `*hints*`, `*no-picture*`, `*panel*` are
git-ignored) and are described below. The committed ones show no problem: the start screens,
the teacher view and a manipulative. Regenerate the rest in sim mode with the data linked. Everything in `assets/`; the Python server
(`copilot/webapp.py`, `copilot/hal/web.py`) is untouched and every route and behaviour of
`app.js` is kept: polling of `/api/state`, the hint ladder, rung 0 (translation), reset, the
keys A to E, P/H, T and N, Enter on the start screen.

References and what was taken from each: `docs/ui/research.md`.

## Before

- `before-start-1280.png`: a white header with the title, the LED matrix (234 px wide) and
  the teacher link; the start card under it; the action timeline and the load time in the footer.
- `before-problem-1280.png`: two columns. Left, the picture at 300 px tall (the Kangaroo scans
  are 1650 px wide, so the text inside was 7 px tall), then the same statement again as text,
  then the A to E buttons with the OCR text under each letter (often wrong: "ALL", "A△△O"),
  then the message. Right, the "Ajuda" card with Pista and Solució, the mastery bars 0 to 5.
  Under both, the timeline with laptop and board seconds, visible to the student.
- `before-problem-390.png`: on a phone the header wrapped to three rows (title, reset, CA/EN,
  LED, teacher link) and the problem started below the fold.

## After

Student page (`index.html`, `style.css`, `app.js`, new `theme.css` and `theme.js`):

- `after-problem-1280-light.png`: one column of 920 px. A quiet bar (app name, student chip,
  CA/EN, the theme button, "Més"). A one-line meta ("Nivell 2 · 1r d'ESO · Angles"). The
  picture in a white card at full width (the text inside is now 15 px tall on the laptop).
  Two chips: "Mostra el text" and "Llegeix-lo en anglès" (rung 0). Five letter buttons, 68 px
  tall, equal width, in the picture's order. A reserved line for the message. Pista with its
  three rung dots and Solució as a text link.
- `after-problem-1280-dark.png`: the same in dark (`?theme=dark` or the system preference):
  graphite background, lighter cards, soft text, the accent one step lighter; the picture stays
  on a white card dimmed to 86 % so it does not glare.
- `after-answer-1280-light.png`: after a wrong answer, A in soft red, the correct E in soft
  green, and the verdict as a pale red band under the options holding "Següent problema". The
  options never move and nothing covers them. Pista is disabled, Solució stays.
- `after-rung0-1280-light.png`: rung 0 open: the English statement in a card with an accent
  edge under the picture, labelled "no compta com a pista"; the chip reads "Amaga l'anglès".
- `after-hints-1280-dark.png`: two hints (neighbour problem and strategy card) under the help
  row, in cards with an accent edge; the neighbour text clamps to three lines with "mostra'l
  sencer".
- `after-no-picture-1280-light.png`: the variant without a picture (rendered from the same
  code with `has_image` false): the text is the statement and the options go on full-width
  rows with a letter badge.
- `after-panel-1280-light.png` and `after-panel-390-light.png`: the "Més" drawer. "El teu
  progrés" as five segments per topic that light up (never a number), the LED matrix, the
  timings behind a `<details>` for the teacher (problem id, last actions, laptop and board
  seconds, page load), the teacher link and the reset button. Escape closes it.
- `after-problem-390-light.png` and `after-problem-390-dark.png`: phone, 390x844. The bar in
  one row (the app name drops out: the tab has it). On a phone the text opens by default,
  because the scan is too wide to read at that size; tapping the picture opens it bigger in a
  dialog that scrolls sideways. The five letters still fit in one row (65 px each).
- `after-problem-390-light-closed-text.png`: the phone with the text closed by the student.
- `after-start-1280-light.png` and `after-start-1280-dark.png`: the start card alone.
- `after-teacher-1280-light.png` and `after-teacher-1280-dark.png`: the teacher view with the
  same bar, the same tokens for the mastery cells (0 muted, 1 red tint, 2 amber tint, 3 accent
  tint, 4 and 5 green tint) and the theme button. Not redesigned beyond that.
- `after-manip-rotate-light.png` and `after-manip-rotate-dark.png`: a manipulative with the
  tokens; the canvas reads the tokens from CSS, so the shapes follow the theme. The dialog
  passes `&theme=` to the iframe.

## Decisions

1. **The picture is the statement.** Every M3Kang scan carries the statement and the
   options. When `has_image` is true, the text is behind "Mostra el text" (open by default
   under 640 px) and the buttons show the letter only. The OCR options are listed under the
   text when open, as a reading aid, never on the buttons: 40 % of val problems have no OCR
   options and many of the rest are wrong. Without a picture the text is the statement and
   the options go on the buttons (rows).
2. **One accent.** `--accent` #2f5fd6 (5.9:1 on white) for the primary action and the chosen
   states; light #8aa6ff on dark cards. Success and error are pale tints with dark text:
   `--ok` #1a7a47 on #e2f4e8 (5.1:1), `--bad` #b4231f on #fdeae8 (5.7:1); the dark pairs are
   #8fd9ad on #1b3326 and #f3a59d on #44211e (both above 7:1). Text `--ink` #1f2430 on white
   is 14.6:1, `--muted` #5f6673 is 5.6:1. Warm page #f7f4ee, white cards, 1 px borders,
   14 px radius. System font stack, nothing fetched.
3. **Dark mode.** Tokens in `:root`, redefined under `@media (prefers-color-scheme: dark)`
   for `:root:not([data-theme="light"])` and again for `:root[data-theme="dark"]`. The button
   in the bar cycles auto, light, dark (◐ ☀ ☾) and stores the choice in `localStorage`
   (`copilot-theme`); `theme.js` applies it before the first paint and also reads `?theme=`,
   which the dialog passes to the manipulatives. The problem PNGs keep a white card: a soft
   inversion was rejected because grey and black cells carry meaning in many figures
   (boards, shading); the card is dimmed to 86 % in dark instead.
4. **Calm states.** The verdict is a band under the options, with the space reserved so the
   page never jumps; the only transitions are 150 ms colour changes on the buttons, disabled
   under `prefers-reduced-motion`. No timer in front of the student: the timeline and the load
   time live in the panel behind "Temps (per al professor)". Progress is segments that fill.
5. **Accessibility.** `:focus-visible` ring in the accent, every control at least 44 px tall
   (letters 68 px, 60 px on a phone), `aria-expanded` on the two toggles, `aria-label` on the
   letter buttons with the option text when it is shown, the theme button announces its state.
   Keys unchanged. All student text through the existing `cat`/`eng` tables; new keys:
   `show_text`, `hide_text`, `more_panel`, `board_led`, `timing`, `problem`, `theme`.
6. **Hint limit (merged from main, `HINT_MAX_USES=3`).** The three dots on "Pista" are the
   hints left on this problem (`hints_left` of `hints_max` from `/api/state`): they go out one
   by one; at zero the button is disabled with a tooltip and the server's bilingual message
   fills the reserved line, while "Solució" and rung 0 stay available (they do not count).
7. **Catalan strings.** The corrections of `docs/content-review.md` that touch `assets/` are
   applied (Nom o àlies, Canvia d'alumne, Que ho endevini el copilot, Un moment…, the hint
   kinds without "Pista 1", mostra-ho tot, progrés, placa (estimat), temps de càrrega, the
   one-word topic labels Nombres / Comptar / Espai, "una reflexió (un mirall)" in the rotate
   manipulative, "a vegades" in the teacher legend). The ones in `copilot/` are for the controller.
8. **Nothing flashes.** No animation repeats; the LED canvas is redrawn on each poll with the
   same frame, as before.

## Measurements (laptop, sim mode, port 7007, no network)

| What | Value |
|---|---|
| Page load reported by the page (`#load`, first `/api/state` rendered) | 8 ms |
| `performance` navigation: DOMContentLoaded / load | 12 ms / 13 ms |
| Requests on first paint | 5 files (html, 2 css, 2 js), then `/api/state` and `/api/image` |
| `assets/` total (7 files + 3 manipulatives) | 66.5 KB (84 KB on disk) |
| `index.html` / `style.css` / `theme.css` / `theme.js` / `app.js` | 4.1 / 11.7 / 2.3 / 1.4 / 16.6 KB |
| Before: `index.html` + `style.css` + `app.js` | 24.4 KB |
| Each asset over HTTP from the sim server | under 1 ms |
| Tests (`python3 -m unittest discover tests`), after merging main `1c5534b` | 181 OK, 1 skipped |

The phone captures were taken with the app's browser pane at 390x844 (headless Chrome does
not go under about 500 px wide, so its phone captures were discarded); the laptop captures
with headless Chrome at 1280x800, forcing the theme with `?theme=`.

## Not done, and what the API would need

- The page assumes every picture carries the options (true for the M3Kang scans). If a
  future source has pictures without the options, `/api/state` would need a flag such as
  `options_in_image` so the buttons can show the text again; nothing else changes.
- The server clears `message` after a hint, so the reserved line under the options is empty
  then. Fine as it is; a short neutral message from the server would fill it.
- The problem id is no longer on the student's screen; it is in the panel under the timings.

## The fourth use: a lesson (branch `ui-lesson`)

With `HINT_MAX_USES=4` the fourth press of "Pista" is not a hint but a short lesson on the
topic; the server (D) will send it inside `hints` with `kind: "lesson"` and `title_ca/en`,
`text_ca/en`. The page is ready for it:

- The last of the dots on "Pista" is a small open book (inline SVG, nothing fetched) with the
  tooltip "Lliçó" / "Lesson"; the dots now go out from the left as hints are used, so the book
  is the one still lit before the last press. `lesson-dots-4-left.png` (all four lit) and
  `lesson-dots-1-left.png` (three hints used, only the book lit).
- A `kind: "lesson"` entry is drawn as its own card under the hints: a `LLIÇÓ` kicker with the
  book, a 20 px title, the text at 18 px with line height 1.6 and a 68-character measure, on
  the quieter `--card-2` surface with no accent edge and no laptop/board time. It sits under
  the help row like the hints, so it never covers the options. `lesson-card-1280-light.png`,
  `lesson-card-1280-dark.png`, `lesson-card-390-light.png` (the card is 358 px wide on the
  phone, no horizontal scroll). Keys and the 44 px targets are unchanged; the button is 48 px.
- Until the server serves it, `dev/fixtures/lesson_hint.json` (own text, 99 words in Catalan
  and 105 in English, on counting in a grid) with the console recipe in `dev/fixtures/README.md`
  shows the card; the captures above were made that way on the sim with `HINT_MAX_USES=4`.
