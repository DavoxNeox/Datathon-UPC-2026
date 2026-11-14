# Runbook: the morning of the pitch

From a powered-off board to the last click. Laptop commands run in a terminal on the
MacBook; nothing has to be typed on the board (the app, the two model servers and the relay
start at boot: `docs/deploy-board.md` §5). Allow **30 minutes** before the slot; the board
needs 2 of them, the rest is checking and one rehearsal.

## 0. The night before

- [ ] Board, its USB-C cable (data, not charge-only), laptop charger, HDMI/USB-C adapter for
      the projector, a phone with the backup video (`contingency.md`) and a power bank that
      can feed the board (5 V, 3 A).
- [ ] Laptop: `adb` installed (`brew install --cask android-platform-tools`), automatic sleep
      and notifications off, browser zoom at 150% remembered for `127.0.0.1:7002`.
- [ ] `git log -1` on the board equals `origin/main` (the controller says which commit is the
      demo commit; do not pull on the morning).
- [ ] `docs/demo/demo-problems.md` printed, and `one-pager.md` printed for the jury.

## 1. Power on (t = 0)

Plug the board into the laptop's USB-C port (that powers it and gives `adb`). Wait about
2 minutes: the Linux side is up when `adb` sees it.

```bash
adb devices
```

Expected: one line `<serial>  device`. `unauthorized` or nothing: see `contingency.md` §2.

## 2. Check the three services (t = 2 min)

```bash
adb shell systemctl is-active math-llm math-embed math-relay
```

Expected: three lines `active`. Anything else: `contingency.md` §1.

```bash
adb shell 'curl -s http://127.0.0.1:8081/health; echo; curl -s http://127.0.0.1:8082/health; echo'
```

Expected: `{"status":"ok"}` twice (the embedding server answers before the LLM finishes
loading its 835 MB; give it another 30 s if the first line is empty).

## 3. Check the app (t = 3 min)

```bash
adb shell 'TMPDIR=/tmp arduino-app-cli app ps'
```

Expected: `user:math-copilot` running. If it is not listed as running:

```bash
adb shell 'TMPDIR=/tmp arduino-app-cli app start user:math-copilot'
```

(`app start` refuses when the app is already running; then use `stop` and `start`, each
with `TMPDIR=/tmp`.) The page answers about 20 s after the app starts (the sketch compiles
on the first start after a change, about a minute).

## 4. Forward the page to the laptop (t = 4 min)

```bash
adb forward tcp:7002 tcp:7000
```

Open <http://127.0.0.1:7002> in the browser. Expected: the start screen "Hola! Com et dius?"
with the LED matrix drawing (dark) at the top right. Port 7002, not 7000: on macOS port 7000
is taken by AirPlay.

```bash
curl -s http://127.0.0.1:7002/api/state | head -c 200
```

Expected: JSON starting with `{"student": ..., "started": false`.

## 5. Clean state: forget every rehearsal alias (t = 5 min)

Every pseudonym played in a rehearsal is still in the board's `data/students.db`, and the
teacher view lists them all. Two ways to clean, pick one:

- **From the page**, one alias at a time: if a problem is shown, press **Canvia d'alumne**
  and confirm (the current student is forgotten and the start screen comes back); for every
  other alias that was used (`Mariona1`, `Guillem`, `Pau`, `prova`, any name typed in
  rehearsals) type it in the start screen, press `Comença`, then `Canvia d'alumne` and
  confirm. From the terminal the same is `curl -s http://127.0.0.1:7002/api/start/<alias>/1`
  followed by `curl -s http://127.0.0.1:7002/api/reset`.
- **All at once**, with the app stopped (the file is recreated empty on the next start):

```bash
adb shell 'TMPDIR=/tmp arduino-app-cli app stop user:math-copilot'
```

```bash
adb shell rm -f /home/arduino/Datathon-UPC-2026/data/students.db
```

```bash
adb shell 'TMPDIR=/tmp arduino-app-cli app start user:math-copilot'
```

Then wait about 20 s for the page and check the teacher view is empty:
<http://127.0.0.1:7002/teacher> shows no student row.

## 6. One full rehearsal on the board (t = 6 to 12 min)

Run the click script from the laptop against the board, exactly as the pitch will do it:

```bash
python3 dev/demo_rehearse.py --base http://127.0.0.1:7002 Mariona1 1 C A --hints 2 --hints2 2
```

Check three things in its output:

1. Problem 1 is `lvl-1_2024_2` and problem 2 is `lvl-3_2019_18`; the neighbours are
   `lvl-0_2024_3` and `lvl-2_2019_9` with `image=yes`. If the ids differ, the board's data or
   `SEED` differ from the laptop's: switch to whatever chain the board gives
   (`dev/demo_pick.py --chain Mariona1 1` on the laptop will not help; read the ids from the
   output and tell V2), or use chain A (`Guillem 2`) and check it the same way.
2. Every step well under 10 s real ("board est" is 0.0 for these steps).
3. The LED matrix physically shows the tick, then the mastery bars, then the cross. Watch the
   board, not the page.

The script ends with a reset (`/api/reset`, the page's **Canvia d'alumne**), so the board is clean again. Then do the same clicks **by
hand in the browser once**, with the projector connected, so V3 knows where every button is
at 150% zoom.

## 7. The student and the state before the jury arrives (t = 15 min)

1. **Warm-up click.** The first `Pista` of a session loads the retrieval index from
   `data/index.db` (0.2 s on the laptop, longer on the board's SD card); do it now, not on
   stage: type any alias (for example `escalfament`), `Comença`, `Pista` once, wait for the
   card, then `Canvia d'alumne` and confirm. The index stays in memory while the app runs.
   From the terminal: `curl -s http://127.0.0.1:7002/api/start/escalfament/1`, then
   `curl -s http://127.0.0.1:7002/api/hint`, wait 2 s, then `curl -s http://127.0.0.1:7002/api/reset`.
2. Pseudonym **`Mariona1`**, course **6è de primària (nivell 1)**, typed in the start screen
   but **not** started: the first click of the demo is `Comença`. (The pseudonym gives the
   chain in `demo-problems.md`; `Comença` resets it, so earlier rehearsals do not matter.)
3. Language buttons: **CA** selected.
4. The LED matrix is dark except the resting frame; V1 holds the board with the matrix
   towards the jury and the USB cable with slack.

## 8. Tabs, in this order, nothing else open

| tab | URL | purpose |
| --- | --- | --- |
| 1 | `http://127.0.0.1:7002/` | the student page, start screen ready (the demo runs here) |
| 2 | `http://127.0.0.1:7002/teacher` | the teacher view, opened at 81 s of the demo; reload it then (`Cmd+R`) so it shows Mariona1 |
| 3 | the backup video file, paused at 0:00 | `contingency.md` §9 |
| 4 | `docs/demo/one-pager.md` rendered (or the printed sheet) | only if the jury asks for the architecture |

Browser in full screen (`Ctrl+Cmd+F`), bookmarks bar hidden, 150% zoom on tabs 1 and 2.
The terminal stays open behind the browser with the `adb forward` already done, in case
`contingency.md` is needed.

## 9. During the pitch

V3 follows the click column of `pitch.md`; V1 shows the matrix at every letter click; V4
signals time. Nobody touches the board's cable.

## 10. After the pitch

```bash
curl -s http://127.0.0.1:7002/api/reset > /dev/null
```

Leave the board on for the jury's questions (afterwards, clean the aliases again as in step 5 if there is a second slot) (they may ask to type a problem's answer
themselves: any pseudonym and course works). Shut down only at the end of the day:

```bash
adb shell sudo poweroff
```
