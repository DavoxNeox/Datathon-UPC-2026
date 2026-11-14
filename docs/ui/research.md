# Student page redesign: references

Research for the minimal student page (assets/), done on Mobbin on 14 November 2026 with the
Mobbin connector (`search_screens`). Each entry says what we take from it and what we leave.
Links go to the Mobbin screen; the previews were read, not copied.

Constraints that shaped the choice: offline board (no fonts, no CDNs), one student at a time,
a 3-minute demo on a 1280x800 laptop and on a phone, M3Kang images that already carry the
statement and the options, and a page that must motivate a 10-to-18-year-old without stressing.

## References

1. **Brilliant, web lesson with a chart question** ([screen](https://mobbin.com/screens/1b1f55e7-1791-448f-ace3-82b727c63586))
   Take: one task per screen, centred column of about 560 px, nothing else on the page but a thin
   progress bar at the top and a single action bar at the bottom. The verdict is a full-width
   pale green band under the content that never covers the question. Leave: XP counters.

2. **Brilliant, "Finding half" interactive** ([screen](https://mobbin.com/screens/757189ac-bfec-4194-92b9-887619becaf4))
   Take: the figure is the content, drawn big with a thin border on a white surface; the
   primary button is disabled until there is something to check. Leave: the dark "Check"
   button (our primary is the accent colour, to stand out on a warm background).

3. **Brilliant, "Here's the answer" state** ([screen](https://mobbin.com/screens/30213eac-1f38-4efe-809f-9eb2d7d33008))
   Take: a wrong answer is shown in neutral grey, not red, with a "Why?" secondary action.
   Our rungs (hint, solution) play that role. Leave: the modal explanation; ours stays inline.

4. **Duolingo, iOS "Fill in the blank" with correct feedback** ([screen](https://mobbin.com/screens/57d38f9d-5bee-42f9-96f8-85b05f3bf835))
   Take: options as full-width pills with a 3D-free 2 px border, the chosen one tinted; the
   feedback band slides under the options in soft green and holds the "Continue" button, so
   the options stay visible. Leave: mascots, combos, streak counters.

5. **Duolingo, web wrong answer** ([screen](https://mobbin.com/screens/46846d71-0727-4d42-8d3d-73e2336bb3d0))
   Take: the error band is a pale red surface with dark red text, never a bright red block;
   the correct answer is named in the band. Leave: the red "Continue" button, we keep one
   accent for the primary action in every state.

6. **Khan Academy, iOS "Which box has 8 chicks?"** ([screen](https://mobbin.com/screens/37743b4a-6a0f-4d75-840f-279bafd1a89f))
   Take: lettered circles A, B, C in front of picture options; when the options are pictures
   the letters are the whole button. This is our "options already in the image" case: big
   letter-only buttons in the image's order. Leave: the dark blue header.

7. **Khan Academy, "Nice work" bubble and dot progress** ([screen](https://mobbin.com/screens/16b5952e-678b-4adf-90ef-a76c7dc7ddec))
   Take: progress as a row of small dots that fill up, one per problem, next to the next
   button; the correct option gets a green check and a tiny "correct" label. Leave: the
   pop-up bubble (it covers content).

8. **Khan Academy, "Stuck? Use a hint"** ([screen](https://mobbin.com/screens/390161fb-2136-4825-9945-7e23dade4bc6))
   Take: the hint is a quiet text link with a bulb icon under the problem, not a big button;
   the student notices it only when stuck. Our hint ladder keeps its dots.

9. **Headspace, "Start your day" list** ([screen](https://mobbin.com/screens/c7fcbf0d-0846-43a4-a0b5-89e681b6f4ce))
   Take: warm off-white background (#f7f3ee family), cards with 16 px radius and no border,
   generous 24 px paddings, and one orange accent used once per screen. The mood is calm, which
   is what we want for a student who is stuck. Leave: the illustrations.

10. **Linear, Preferences with "Interface theme: System preference / Light / Dark"** ([screen](https://mobbin.com/screens/aa0b9e71-c5a0-4245-b30a-ee5059de6235))
    Take: a three-state theme setting (system, light, dark) in a secondary place, not in the
    main flow. Ours is a small control in the collapsible bar, saved in localStorage.

11. **Linear, dark theme preferences** ([screen](https://mobbin.com/screens/c968b3b2-82a5-4044-8e4a-0bec5683dec5))
    Take: dark mode is a graphite surface (#1c1d21 family) with slightly lighter cards and
    soft off-white text, never pure black or pure white. Borders are one step lighter than
    the surface rather than a separate colour.

12. **Notion, page with toggle blocks** ([screen](https://mobbin.com/screens/67a8339c-58b2-43e4-8ded-6c003882cdd9))
    Take: secondary content lives behind a plain disclosure triangle ("This is a toggle
    block"), the open state is just more text below. Our "Mostra el text", the domain map, the
    LED and the timing live behind `<details>`.

13. **Uxcel, quiz with figure on the left and options on the right** ([screen](https://mobbin.com/screens/57f30d08-7ba2-45d9-a676-eb59df77c3dd))
    Take: the figure in a bordered white card and the keyboard shortcut (1, 2, 3, 4) printed
    small inside each option; a timer exists but is tiny and in the corner. Ours goes further:
    no timer on the student page.

14. **Turo, "Test your knowledge" with the correct answer band** ([screen](https://mobbin.com/screens/1055c068-8deb-4bc9-accc-33fae4e7aa32))
    Take: on a correct answer the explanation appears as a green-bordered box above the
    options, the options stay where they were, the chosen one gets a green check. Leave:
    the sidebar and the purple progress bar.

## What the references agree on

- One column, 560 to 720 px wide, centred; nothing competes with the task.
- Surfaces: a warm or neutral off-white page, white cards, 1 px borders or none, 12 to 16 px radius.
- One accent colour for the primary action, used once per screen. Success and error are pale
  tints with dark text, shown as a band that never covers the options.
- Progress is small and grows (dots, a thin bar); no scores, no timers in front of the learner.
- Help is quiet until needed (a link, a small button), then expands inline.
- Dark mode: graphite surfaces, soft text, the same accent lightened one step.

## Decisions taken from this research

See `docs/ui/redesign.md` for the before/after and the measurements.
