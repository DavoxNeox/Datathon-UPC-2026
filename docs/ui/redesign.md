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
2. **One accent, measured.** `--accent` #2f5fd6 for the primary action and the chosen
   states; #8aa6ff on dark. Success and error are pale tints with dark text. Contrast ratios
   (WCAG relative luminance, computed from the tokens):

   | pair | light | dark |
   |---|---|---|
   | text `--ink` on `--card` / on `--bg` | 15.5 / 14.1 | 13.0 / 14.5 |
   | secondary text `--muted` on `--card` / on `--bg` / on `--card-2` | 5.8 / 5.3 / 4.95 | 6.6 / 7.3 / 5.8 |
   | `--accent` on `--card` / on `--bg` | 5.6 / 5.1 | 6.9 / 7.7 |
   | button text `--accent-ink` on `--accent` | 5.6 | 7.8 |
   | `--accent` on `--accent-soft` (chosen chip) | 4.8 | 5.4 |
   | `--ok` on `--ok-bg` | 4.68 | 8.2 |
   | `--bad` on `--bad-bg` | 5.7 | 7.2 |
   | `--warn` on `--warn-bg` | 5.4 | 7.6 |
   | control border `--control` on `--card` / on `--bg` | 3.7 / 3.4 | 3.7 / 4.2 |
   | card border `--line` on `--card` (decorative) | 1.3 | 1.3 |

   Every text pair is above 4.5:1 (the lowest is 4.68:1, the success text in light). Controls
   (the A to E buttons, chips, Pista, CA/EN, the theme and Més buttons, the start fields, the
   manipulatives' buttons) use `--control` (#7f858e light, #737a88 dark), which is at least
   3:1 against both the control's fill and the page, as WCAG 1.4.11 asks; cards keep the soft
   `--line`, which is decorative. Warm page #f7f4ee, white cards, 14 px radius, system fonts.
3. **Dark mode.** Tokens in `:root`, redefined under `@media (prefers-color-scheme: dark)`
   for `:root:not([data-theme="light"])` and again for `:root[data-theme="dark"]`. The button
   in the bar cycles auto, light, dark (◐ ☀ ☾) and stores the choice in `localStorage`
   (`copilot-theme`); `theme.js` applies it before the first paint and also reads `?theme=`,
   which the dialog passes to the manipulatives. The problem PNGs keep a white card: a soft
   inversion was rejected because grey and black cells carry meaning in many figures
   (boards, shading); the card is dimmed to 86 % in dark instead.
4. **Calm states.** The verdict is a band under the options (`aria-live="polite"`, so a
   screen reader hears it), with the space reserved so the page never jumps; the only transitions are 150 ms colour changes on the buttons, disabled
   under `prefers-reduced-motion`. No timer in front of the student: the timeline and the load
   time live in the panel behind "Temps (per al professor)". Progress is segments that fill: the
   current topic's five segments with its name sit under the letters, always visible (the pitch
   points at them at 48 s and 70 s), and the whole map is in the Més drawer. On a screen 1000 px
   or wider the drawer pushes the page left (the content is 836 px wide at 1280) so it never
   covers an answer button; on a narrower screen it closes by itself when the student answers.
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
   applied (Canvia d'alumne, Que ho endevini el copilot, Un moment…, the hint
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
  `lesson-card-1280-dark.png`; on the phone (390x844, checked in the browser pane) the card
  is 358 px wide with no horizontal scroll (that capture shows a neighbour problem, so it is not committed). Keys and the 44 px targets are unchanged; the button is 48 px.
- Until the server serves it, `dev/fixtures/lesson_hint.json` (own text, 99 words in Catalan
  and 105 in English, on counting in a grid) with the console recipe in `dev/fixtures/README.md`
  shows the card; the captures above were made that way on the sim with `HINT_MAX_USES=4`.

## After the review (`docs/reviews/review-ui-redesign.md`)

Applied on `ui-lesson`: the `--control` border token at 3:1 or more on every control in both
themes (measured above); the current topic's progress under the letters, always visible, and
the Més drawer that pushes the page on wide screens and closes on answer on narrow ones;
`aria-live="polite"` on the verdict band; "Àlies" / "Nickname" again; the contrast table
replaced by measured values; the text fold re-evaluated on resize until the student chooses.
`review-letters-progress-verdict.png`: the letters with the new border, "Taulers i patrons"
with two segments lit after a correct answer, and the green band with "Molt bé, correcte!".

## Duolingo-like restyle (branch `ui-lesson`, 14 November, evening)

Requested by the user: the same page in Duolingo's lesson language, with few colours and no
drawings. Same structure, same routes and keys; `style.css` rewritten, `index.html` rearranged.

- **Top bar as a lesson header**: "MÉS" on the left (where Duolingo has the X), the student
  in small grey, the current topic's mastery as a 16 px rounded bar with its name in small
  caps above it (fills in fifths; this is what the pitch points at), CA/EN and the theme
  button on the right. The map of all topics stays in the drawer.
- **Pressable buttons**: every button and option card has a 4 px darker bottom edge drawn as
  a shadow (`--accent-deep`, `--ok-deep`, `--bad-deep`, `--control`), which disappears while
  pressed as the button moves down 4 px. Labels are uppercase, 800 weight, letter-spaced.
  The font stack starts with `ui-rounded` (SF Rounded on Apple devices) and falls back to the
  system font elsewhere; nothing is fetched.
- **Option cards**: 84 px tall, 16 px radius, 2 px `--control` border; the chosen one turns
  accent-tinted, the right one green, the wrong one red; the others fade to 60 %.
- **Action sheet**: fixed at the bottom of the viewport like a lesson's bar, 84 px tall,
  with PISTA (and its dots and the book), SOLUCIÓ and the manipulative on the left, the
  message in the middle and CONTINUA on the right once answered. Neutral before the answer,
  pale green or pale red after it, with the button filled in the same colour. The main
  column has 140 px of bottom padding (170 on a phone) so the sheet never covers an answer
  or a hint; `aria-live="polite"` stays on it. Enter also continues, as in a lesson.
- **Colours**: still the three (accent blue, success green, error red) plus neutrals; no
  icons besides the book and the theme glyphs; no illustrations.
- The topic segments under the letters were replaced by the top bar, which is bigger and
  always visible; the review's intent (progress visible outside the drawer) holds.

### Same background, no modals (same evening)

The user asked for no modals and one background everywhere, with a dropdown of our own:

- `--card` now equals `--bg` in both themes (#f7f4ee light, #15171c dark): the start form,
  the hints, the drawer and the action sheet sit on the page and 2 px borders do the
  separating; the problem picture keeps its white card because the PNGs are white. The start
  screen lost its card: title, two fields and the button on the page.
- **Course dropdown**: a button styled like the inputs (2 px `--control` border, 14 px radius,
  a CSS chevron that turns when open) and a list that opens *in the flow* under it, pushing
  the help text and the button down, never over anything; options are 46 px rows, the chosen
  one accent-tinted with a check mark. Keyboard: Down/Up open and move, Enter or Space choose,
  Escape closes and returns focus, Tab closes; a click outside closes. `role="listbox"` and
  `role="option"` with `aria-selected`; the native `<select id="level">` stays hidden as the
  value holder, so nothing else in `app.js` changed.
- **No `<dialog>` and no `confirm()`**: the manipulative opens in a bordered box under the
  hints (with its own "Tanca"), the picture zooms in place (click: the figure scrolls
  sideways at 1100 px; click again to shrink), and "Canvia d'alumne" asks inline: the first
  press turns the button red with "Segur? Esborra el progrés" for four seconds, the second
  press erases. The `Escape` and letter keys no longer need a dialog guard.

## For young readers: text, figure, options, and nothing twice (branch `ui-young`, 15 November)

The user asked for a page a ten-year-old reads at a glance: short texts as bullets, one menu
button instead of five controls, a much bigger progress bar, the statement never shown twice,
and a hint button without icons.

- **The problem in three parts.** The statement is the dataset's text (the scan's line breaks
  and the problem number removed, 24 px bold). The figure is cut out of the scan in the browser
  (`scanComponents`, `classifyParts`, `cropPart` in `app.js`): the PNG is read on a canvas at
  2 px cells, blanks inside a line are bridged, 4-connected components are found, the text line
  height is the median of the wide low components, option rows are bands of three or more
  pieces spread across the page, the statement is the left-margin text lines plus the pieces
  that share their row left of the first big thing on the right, and the figure is everything
  else; the statement's rectangle is painted white inside the crop. When the OCR options are
  readable text they go on the option rows and the scan's option row is dropped; when they are
  pictures or symbols the option strip of the scan is kept, glued to the figure when it sits
  under it (keys, cubes, balances) or shown as its own strip otherwise. Nothing fetched, no
  server change: `/api/image` is read once per problem and cut once. Prototyped in Python
  against 32 scans of train and val (all topics, text-only and figure problems, figure on the
  right and below, options as pictures): every crop was right by eye; if anything fails at
  run time the whole scan is shown as before. Small crops are drawn at 1.6 times.
- **Menu and progress.** One "Menú" button on the left; the current topic's mastery as a 26 px
  bar across the rest of the header (20 px on a phone). The sidebar holds the student and the
  course, CA/EN, the theme, the map of topics, the LED, the timings and the teacher link; it is
  in the flow on a phone and a fixed left column that pushes the page on a wide screen.
- **No chips.** "Mostra el text" and "Llegeix-lo en anglès" are gone: the text is always shown
  and the language changes in the menu. Rung 0 is therefore not reachable from the student
  page any more (the route stays; the teacher view keeps its section).
- **Plain hint button.** "PISTA · 3" says how many hints are left; the last use, when the
  server allows four, reads "LLIÇÓ"; no dots, no book.
- **Bullets.** Strategy, step and lesson texts are split into sentences and shown as a list
  when there is more than one sentence; the statement and the neighbour problem stay as prose.
- **Compact sheet.** 76 px tall on a laptop; on a phone the message sits on its own line and
  the buttons share one row, nothing wraps.

### Second round for young readers (same day)

- **Answers on the buttons.** When the OCR could not read the options, each option is cut out
  of the scan and drawn inside its button, without its letter: text options ("A) 15") lose the
  label by column profile (the letter and its parenthesis are one run, the value starts after
  the first real gap); options drawn as pictures (keys, cubes, tiles, unfoldings, puzzle
  pieces) are found as five letters each next to its own picture, or bridged into it (the
  leading columns of the picture with ink only in the bottom band are the letter, masked
  white). Five found, five buttons; anything else keeps the previous behaviour. Checked on 34
  scans: the five picture-option scans split into five pieces, none of the 29 others did.
- **Figures without background.** Every crop becomes an alpha mask: a pixel's alpha is its
  darkness, grey pixels take the theme's ink colour, saturated colours keep their hue and are
  lightened by 40 % in the dark theme. The figure sits on the page itself, no card; the
  neighbour problem's picture gets the same treatment; everything is re-tinted when the theme
  changes and the tinted crops are cached per theme.
- **Figure on the right, text around it.** The figure floats right at up to 46 % of the
  column and the statement wraps on its left and below it; on a phone it goes above the text.
- **Bugs.** The hints were rebuilt on every poll (twice a second), which closed "mostra-ho
  tot" at once: they are now rebuilt only when their content changes and the expanded state is
  kept per problem and hint. Pista and Solució now disable themselves and show "Un moment…"
  the instant they are pressed, until the next poll brings the result.

### Third round (same evening)

- Options are text whenever the OCR read them as text, maths included (roots, ×, π, powers,
  braces, ≤, ∞); only drawn shapes (△ ○ □) keep the scan's crop. Two OCR habits are tidied: a
  "V" before a digit is a root sign, a stray capital at the end of a value is dropped.
- Figures a step smaller (40 % of the column at most, 34 vh tall, small crops at 1.25 times up
  to 400 px) and crisper: the mask drops the scan's grey noise under a darkness of 60 and ramps
  lines to full ink by 170, so there is no halo around the lines on either background.
- The review's three fixes (sheet edge in `--control`, phone padding under the sheet, mastery
  map drawn on the start screen so a reset empties it) are on this branch as well as on
  `ui-fixes-3`.

### Rung 0 back, and the whole scan one click away (branch `ui-fixes-4`)

- **Rung 0** is reachable again: "Llegeix-lo en anglès" / "Read it in Catalan" is a button in
  the Menú sidebar, under CA/EN (which still switches the page's language, apart). It calls
  `/api/translate/show|hide` as before, so it counts as rung 0 and spends no hint use. The
  translation appears under the statement as quiet grey text with an accent edge and the
  label "En anglès · no compta com a pista"; the key T toggles it.
- **The whole scan, one click away**: a small "Mostra l'escaneig sencer" link under the
  options shows the full scan (tinted like the crops) below them, for the case a cut goes
  wrong on the projector; "Amaga l'escaneig" puts it away. The link is not shown when the
  page already fell back to the whole scan.
- **When the page falls back to the whole scan by itself**: (1) the cutting code throws (an
  image that is not a PNG the canvas can read, a zero-sized component list); (2) nothing was
  found to show, that is no figure, no option strip and no option pieces, while the OCR options
  are not readable text (a scan made only of pictures the rules did not recognise). In both
  cases the full scan is shown where the figure goes and the buttons carry the letters only.
  When the OCR options are readable text and no figure is found, nothing is shown besides the
  text and the option rows (a text-only problem). A wrong cut that does not throw (a figure
  trimmed too tight, a label left in) is not detected: that is what the link is for.

### Fourth round (branch `ui-polish`)

- Short options (every value up to 10 characters: "42 cm", "3√2 cm") go in one row of five
  cards with the value as the main text; longer ones keep one per row.
- The figure takes at most 30 % of the column and, when it is wider than tall, is never taller
  than the question: its height is set from the text's height (measured twice, since the text wraps around it), capped
  at a third of the window and at 1.25 times its own size; a tall figure (height over 1.2 times
  its width) may use the third of the window, and no figure goes under a fifth of the column
  unless its crop is smaller. On a phone it sits above the text
  at its natural size, then the text, then the answers in a row.
- Zoom shows the whole figure: the figure leaves the float and takes the column (up to 760 px),
  the image scales to fit; a second click puts it back.
- The action sheet has two columns: the message with all the width and "Solució" under it on
  the left; "Continua" on top of "Pista" on the right. 160 px of room under it on a laptop,
  200 px on a phone (the sheet with a verdict measures 134 and 186 px).

### Fifth round (branch `ui-fixes-5`, before the demo)

Reviewer's three important points and the user's next requests, in one branch:

- **The five options fit at 1280x800.** Short options share one row (branch `ui-polish`,
  merged here); long ones are 56 px rows. Checked on the six demo problems (`lvl-1_2024_2`,
  `lvl-3_2019_18`, `lvl-2_2020_4`, `lvl-4_2010_12`, `lvl-3_2021_20`, `lvl-5_2022_30`): the
  last option ends between 323 and 348 px from the top, the sheet starts at 701.
- **Dark theme never turns black into white.** A crop whose interior has filled areas (dark
  pixels with dark neighbours 3 px away in every direction, over 0.4 % of the crop), or a
  statement that names a colour (negre, blanc, gris, fosc, clar, ombrejat, pintat and the
  English words), is drawn as it is on a white card with 6 px of padding; line drawings keep
  the tint. The light theme always tints (black stays black). The neighbour's picture follows
  the same rule.
- **`lvl-3_2021_20`.** Option rows absorb the pieces the band missed (numerators,
  superscripts, units), so the figure crop no longer swallows half the option row; and the OCR
  filter rejects values with two numbers split by a space or a unit glued to a trailing digit
  ("2 11 cm2", "3cm2", "4cm²2"), so the five options come from the scan, fractions intact.
- **Menu and sidebar.** The menu is an icon (three bars) fixed at the page's left edge; the
  progress bar takes the whole width of the 920 px container, which keeps its size whatever
  the sidebar does. The sidebar floats over everything on the left, vertically centred, and
  hides when the cursor leaves it, on Escape, or on a tap outside; on a phone it drops from
  the top. The "Llegeix-lo en anglès" button is 44 px tall.
- **Solution flow.** When the solution arrives the page scrolls to its card and the sheet
  keeps only "Continua": the hint button, the solution link and the status line go.
- **Buttons show the answers only**, centred; the letters A to E stay for the keyboard and
  the screen reader but are not drawn.
- **Fallback and captions.** When the whole scan stands in for a figure it carries the
  caption "Escaneig original" and zooms like any figure; the "veure l'escaneig original" link
  is a small underlined caption under the options, not a sixth row. "mostra-ho tot" is 44 px.

### Sixth round (branch `ui-fixes-6`)

- **The sidebar under a keyboard user.** Opened from the keyboard (a click with `detail`
  0) it never closes by itself; focus inside the panel or on the menu button cancels any
  pending close and focus leaving them re-arms it; the "opened with the mouse and never
  visited" close waits 4 s and only exists for a fine pointer (`hover: hover` and
  `pointer: fine`), so a phone's emulation does not trigger it. Escape and a tap outside
  still close it.
- **After an answer the right button offers a hint**, right or wrong, while hints are left;
  the solution only when none are left. The server still refuses hints after an answer
  (`already answered`): until it allows them, the page falls back to the solution on that
  error, so the button is never dead. The server change is requested.
- **Pieces have names**: when the OCR read an option well its text is the piece's `alt` and
  the button's `aria-label` ("C: 15") even when the picture is shown; otherwise "opció C".

### Seventh round: the settings as a popup

The sidebar became a centred popup over the page: a translucent card (`--glass`, 84 % of the
page colour with an 18 px blur behind it) on a scrim that blurs the page by 6 px. One row
holds CA/EN, the theme and "Llegeix-lo en anglès"; the eight topics sit in two columns; the
LED matrix and the teacher's timings share a row; the teacher link and "Canvia d'alumne"
close the card. It opens from the menu icon, and closes with its X, Escape or a click on the
scrim; focus moves to the X on open and back to the icon on close, so it behaves the same
from the keyboard. There is no close-by-itself any more (a centred card would lose the
cursor all the time), which also settles the keyboard problem of the previous round.

### Eighth round

- The five letter buttons never wrap: one row that shrinks (65 px each on a phone), so no
  lone giant button.
- After an answer, right or wrong, the right button is the hint while hints are left; the
  solution only when none are left. The server now allows hints after the answer (one guard
  removed in `copilot/webapp.py`, with a test): a student who got it wrong may retry by
  themselves with a hint before reading the solution. Mastery is unchanged (recorded at the
  answer). The verdict stays on the sheet when a later hint clears the server's message.

### Ninth round: no white card anywhere

The user does not want a white background on any picture. Every crop is transparent in both
themes. In the dark theme strokes and the edges of shapes take the light ink, while the inside
of a filled shape (dark pixels with dark neighbours 3 px away in every direction) keeps its own
colour: "the black square" stays black, inside a light rim that shows where it is; grey stays
grey. This replaces the white card of the fifth round and keeps the reviewer's point (black is
never shown as white). Checked on `lvl-3_2021_20` (black corner squares, grey triangles) and
`lvl-5_2022_30` (the hand) in both themes. The one exception is the original scan, which the
user asked to keep as paper (eleventh round).

### Tenth round: options from the other language's OCR

When this language's OCR options are missing or noisy, the page takes the other language's
options if they are clean and have no words (numbers, fractions, units: "110", "115,5",
"3√2 cm"). Over the whole bank, 1688 problem versions lack clean options and 110 of them are
rescued this way; the rest keep their options cut from the scan, because there is no text to
show. `lvl-7_2008_3` in Catalan now shows 110 / 121 / 115,5 / 119 / 242 as text.

### Eleventh round: the original scan keeps its paper

The original scan (the "veure l'escaneig original" link, and the fallback when nothing could
be cut) is shown as it is, white paper included, on a white card with soft corners; only the
cuts (figure, option strip, pieces) are tinted and transparent.

This is deliberate and it is the only place where white paper can appear on the page. The
user asked for no white backgrounds on the cuts (ninth round) and, separately, for the
original scan to keep its background ("L'escaneig original no hauria de tindre el fons
borrat"): a scan shown as a scan, not as a drawing. The automatic fallback to the whole scan,
when nothing could be cut, is the same picture through the same path, so it is shown untinted
on purpose. The caption under it says it is the original scan.

Problems the page can serve today (the trainer's bank, `data/train.jsonl` and `data/val.jsonl`):
1747 problems, each in Catalan and English (3494 versions): 1466 from train and 281 from val;
by level 0 to 7: 142, 106, 146, 123, 339, 296, 305, 290.
### Twelfth round (branch `ui-fixes-7`)

- The verdict is captured when the answer arrives (both languages) and stays on the sheet
  while the problem is open, whatever the server's message does afterwards: a hint in
  progress, a hand-written step, the lesson, a refusal or the solution. Other messages go to
  the status line. Checked on `lvl-3_2021_20`: wrong answer, three hints, lesson, solution.
- The settings popup has `role="dialog"`, `aria-modal="true"` and `aria-labelledby` pointing at
  the student's name; the teacher link and "Canvia d'alumne" are 44 px tall.
- The hand-written steps (`demo_steps`) have a label of their own in both languages.

### Thirteenth round (branch `ui-fixes-8`): grey stays grey, and two cutting fixes

- **Grey fills** (G1). A neutral pixel whose 3x3 core holds no solid ink (nothing under 25) and
  whose 5x5 window has a grey mean (55 to 228) with at most three fifths of white specks is a
  grey patch: it takes the window's mean (smoothing the scan's grain), lifted by 35 and capped
  at 210 in the dark theme so it never reaches the ink's lightness. Pixels right next to a line
  stay edges, in ink: the rim of the shape. Measured by reading pixels, counting the neutral
  pixels of level 60 to 200 in the figure crop and what they became:

  | crop | grey pixels | still grey, dark | still grey, light | to ink (the rim) | transparent |
  |---|---|---|---|---|---|
  | `lvl-3_2021_20` (triangles), before | 4104 | 28 | 0 | 3320 / 3348 | 820 |
  | `lvl-3_2021_20`, after | 4104 | 3060 | 2944 | 1032 / 1148 | 12 |
  | `lvl-5_2022_30` (hand, grey 217), after | 3049 | 2954 | 2953 | 27 / 28 | 68 |

  Tinting the hand's crop takes 3 ms. The light grey of the hand (G2) is covered by the same
  rule, since the window's mean (up to 228) tells it from paper (the scan's paper is 250 and
  above); a shaded region lighter than about 230 would still be lost, which is the limit.
- **Indented statement lines.** Wrapped lines of a statement sit after the problem's number;
  the margin test now allows two line heights, so they are statement, not figure.
- **Two-row options.** A row with only two options ("D) ... E) ...") right under an option row
  and aligned with it is an option row too; option rows are looked for only under the
  statement's long lines (a justified line of text is never an option row) and never include
  the figure's labels. `lvl-1_2021_24` (three rectangles) now gives the figure alone and five
  option pieces without their letters.

### Fourteenth round (branch `ui-light-only`): one theme

- **Dark mode removed.** The team chose one palette. `theme.css` keeps the light tokens only;
  the `prefers-color-scheme` and `[data-theme]` blocks, `theme.js` (the stored choice and the
  `?theme=` parameter), the ◐ ☀ ☾ button in the settings popup and in the teacher view, and
  the `theme` i18n keys are gone. The manipulatives keep reading the tokens from `theme.css`.
- **Tinting, one way.** `tintedCanvas` no longer asks which theme is on: strokes, edges and
  black fills take the page's ink, grey patches keep their smoothed mean with no lift, colours
  keep their hue with no lightening. The cuts are tinted once per scan (no retint on a theme
  change). The measurements of the thirteenth round's light column stand.

### Fifteenth round (branch `ui-teacher`): the teacher's view diagnoses a student

The teacher page (`assets/teacher.html`) was a mastery table and a rung-0 table. It is now two
blocks, the class and one student, with inline SVG charts drawn on the page (no library, nothing
fetched) and a table of advanced statistics with a "how" column. References 18 to 21 in
`research.md`.

- **Data.** `trainer.answer_log()` (new, read-only) returns every answer in order with its
  topic, level, letter, label, correctness, hint rung, review flag and time, plus each student's
  row and topic states; `/api/teacher` carries it as `log` next to the report. The page computes
  everything in the browser. Nothing else of the trainer changed; the predictor and the hints see
  the same data as before.
- **The class.** Tiles (students and active today, answers, accuracy with its Wilson interval,
  accuracy without hints, share of problems with a hint); the mastery heatmap with attempts and
  accuracy per student (a click on a row picks the student); accuracy by level and by topic.
- **The student.** A picker (the page's own dropdown), tiles (answers, accuracy with the 95 %
  interval, accuracy without hints, hint share, median time per problem, current streak, working
  level and base level), the diagnosis in sentences, and the charts: mastery pips and accuracy per
  topic; the rolling accuracy of the last five answers with a dot per answer and the problem's
  level as steps behind; hint use as one stacked bar and the accuracy per rung; letters chosen
  against the 20 % of chance; accuracy per level; answers per day over the last 14 days.
- **Advanced statistics** (each row says how it is computed): Wilson 95 % interval; accuracy
  without hints; hint dependence (accuracy after a hint over accuracy without); trend (last 10
  against the previous 10, with a two-proportion z test); learning slope (least squares of
  correctness on answer order, shown from 10 answers); guessing index (chi-square of the letters
  chosen with 4 degrees of freedom, and accuracy against 20 % chance); median time per problem
  (gaps over 10 minutes dropped); longest streaks; working level (highest level with at least
  half correct over 3 answers or more); weakest and strongest topic with 3 answers or more;
  share of answers given after the solution; rung-0 uses and accuracy after it.
- **The diagnosis in words** is a list of rules over those numbers, in Catalan and English:
  little data (under 5), too hard / right zone / masters it (under 45 %, 45 to 75 %, over 75 %),
  possible guessing (from 8 answers: accuracy not above chance, or one letter dominant with
  accuracy under 40 %), hint dependence, improving or worsening (15 points between the last 10
  and the previous 10), answering under 20 s or over 4 minutes, working level and challenge, a
  topic to reinforce (under 40 %) or mastered (80 % or more), looking at the solution on 30 % or
  more, rung-0 use. Checked on the local database: a student with 6 answers gets "too hard
  (33 %)", "answers very fast (5 s)", "uses rung 0"; a student with one answer gets only
  "little data".
- Layout: cards of at least 440 px so the 520 px charts draw close to 1:1; one column on a phone,
  the tables scroll sideways; the bar keeps the student page and the decision dashboard links.
