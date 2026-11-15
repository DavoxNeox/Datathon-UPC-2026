# Runbook: the morning of the pitch

**Shortcuts.** `dev/demo_preflight.sh` runs steps 1 to 6 below in one command from the laptop
(USB, the three services, the app, both pages, the LED, the two chains, the rehearsal aliases;
`--clean` first wipes `data/students.db` on the board, `--no-chains` skips the chain rehearsal);
every line prints `ok`, `FAIL` or `note`, and a `FAIL` names the row of `contingency.md` to read.
`docs/demo/GUIA-DEMO.md` is the one-person guide in Spanish (the 3-minute order, the clicks one
by one on the current interface, the numbers, the Reasoning half, plan B in short). This runbook
is the long form: what each step checks and why.

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
- [ ] `docs/demo/demo-problems.md` and `docs/demo/GUIA-DEMO.md` printed for the team, `one-pager.md`
      printed for the jury.

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

(`dev/demo_preflight.sh` does steps 1 to 6 at once; read on for the hand version.)

```bash
adb forward tcp:7002 tcp:7000
```

Open <http://127.0.0.1:7002> in the browser. Expected: the start screen "Hola! Com et dius?";
the physical matrix breathes (new student). Port 7002, not 7000: on macOS port 7000
is taken by AirPlay.

```bash
curl -s http://127.0.0.1:7002/api/state | head -c 200
```

Expected: JSON starting with `{"student": ..., "started": false`.

## 5. Clean state: forget every rehearsal alias (t = 5 min)

Every pseudonym played in a rehearsal is still in the board's `data/students.db`, and the
teacher view lists them all. Two ways to clean, pick one:

- **From the page**, one alias at a time: if a problem is shown, open the menu (three-bar icon, top left) and press **Canvia d'alumne**
  twice (the first press asks in line, the second confirms; no pop-up): the current student is forgotten and the start screen comes back; for every
  other alias that was used (`Mariona1`, `Guillem`, `Pau`, `prova`, any name typed in
  rehearsals) type it in the start screen, press `Comença`, then menu → `Canvia d'alumne` twice. From the terminal the same is `curl -s http://127.0.0.1:7002/api/start/<alias>/1`
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

(`dev/demo_preflight.sh` runs both chains and forgets the aliases; by hand:)

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
3. The LED matrix physically shows, in order: the breathing diamond on the start screen, four
   blocks on the two bottom rows when the problem loads (one goes dim per hint), the chosen
   letter for 0.8 s, the tick, and 3 s later the mastery map with the boards row growing; then
   the same with the cross. Watch the board, not the page.

The script ends with a reset (`/api/reset`, the page's **Canvia d'alumne**), so the board is clean again. Then do the same clicks **by
hand in the browser once**, with the projector connected, so V3 knows where every button is
at 150% zoom: the answer buttons under the problem (they show the option's value, no letter; the keys A to E also answer), **Pista** and **Solució** in the action sheet at the
bottom, **Continua** after the verdict (Enter also works), the manipulative opening under the hints.

## 7. The student and the state before the jury arrives (t = 15 min)

1. **Warm-up click.** The first `Pista` of a session loads the retrieval index from
   `data/index.db` (0.2 s on the laptop, longer on the board's SD card); do it now, not on
   stage: type any alias (for example `escalfament`), `Comença`, `Pista` once, wait for the
   card, then menu → `Canvia d'alumne` twice. The index stays in memory while the app runs.
   From the terminal: `curl -s http://127.0.0.1:7002/api/start/escalfament/1`, then
   `curl -s http://127.0.0.1:7002/api/hint`, wait 2 s, then `curl -s http://127.0.0.1:7002/api/reset`.
2. Pseudonym **`Mariona1`**, course **6è de primària (nivell 1)**, typed in the start screen
   but **not** started: the first click of the demo is `Comença`. (The pseudonym gives the
   chain in `demo-problems.md`; `Comença` resets it, so earlier rehearsals do not matter.)
3. Language buttons: **CA** selected; the side menu closed (move the cursor away or press Escape), nothing expanded on the page.
4. The LED matrix **breathes** (a central diamond fading in and out every 2.4 s): that is the
   start screen with a new student, and it is what the jury sees first. A dark matrix means the
   app is not running or the sketch did not flash (`contingency.md` row 5). V1 holds the board
   with the matrix towards the jury and the USB cable with slack.

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

V3 follows the click column of `pitch.md`; V1 shows the matrix at every answer click; V4
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

## 11. The exam (the Reasoning half of the grade)

What the organisers published on 15 Nov 2026 with their practice set (`Qualcomm_practica.zip`,
50 new Kangaroo-style problems written for the datathon, not M3Kang, each in English and
Catalan, levels 0 to 7, 40 text-only and 10 with a figure, every letter correct 10 times):

- the final test is **20 different problems, one language each, levels 0 to 7, 4 with a
  figure**, in the same parquet format as M3Kang (`id`, `level`, `language`, `text_only`,
  `image`, `text`, `label`);
- **they run it with our `predict.py` on the board after the 12:00 last call**: at most 60 s
  per problem, no network, nobody from the team at the keyboard;
- the file is prepared with our own script on a laptop, the command they give is ours.

### The policy that runs (team decision, 15 Nov)

On the practice set the M3Kang priors are worth nothing: 84 of the 86 numeric option sets are
printed in order, so the middle value is almost always C, and with balanced letters any fixed
letter scores 20/100 (shipped policy 16/100, ordered-values abstention 20, learned prior 18,
no family solver fires). The only policy above a fixed letter is the brief reasoning of the
0.8B itself: **25/100** on the laptop (the stage decides on 57 rows and gets 15; the rest fall
through to the middle value), about **35 s per problem on the board, worst seen 45 s**, so 20
problems take about 12 minutes. `config.env` on `main` therefore ships `THINK_LEVELS=all`,
`THINK_TEXT_ONLY=0`, `THINK_STYLE=short`, `THINK_BUDGET_SECONDS=45`. `predict.py` resumes
(rows keyed by id and language), so a reboot in the middle costs one problem, not the file.
The figures of the M3Kang validation are in `docs/results-A.md` ("Data v2"); the practice-set
figures and the tuning runs in `docs/reason-experiments.md`.

To run the shipped M3Kang policy instead (0.2 s per problem, 20/100 on the practice set):
`THINK_LEVELS= python3 predict.py ...` (the variable empty). Never mix policies inside one
CSV: if the policy changes, start again with `--fresh`.

### Procedure, end to end (rehearsed on the practice set)

1. On a laptop with the preparation environment (`laptop/requirements.txt`: pyarrow,
   RapidOCR; on the team's Mac the working one is Python 3.12 in
   `.claude/worktrees/data-4d5bfe/.venv`; `python3 -m venv .venv && pip install -r
   laptop/requirements.txt` builds a fresh one, RapidOCR downloads its models on first use, so
   build it before the last call), from the repository root, with their parquet:

```bash
python3 laptop/prepare_m3kang.py --parquet /path/to/final.parquet --languages eng,cat --val-fraction 0 --out data/final --save-images
```

   About 1 s per row (OCR of the options; the 100 practice rows took 54 s). Expected at the
   end: `versions with 5 options 20/20 (100%)`. Fewer means an option set the OCR missed: the
   row still gets a letter (the policy falls through), nothing breaks.

2. Copy the file and the images to the board:

```bash
adb push data/final/train.jsonl /home/arduino/Datathon-UPC-2026/data/final/train.jsonl
```

```bash
adb push data/final/images /home/arduino/Datathon-UPC-2026/data/final/
```

3. Nothing else may use the model servers: the demo page idle on the start screen, no
   `eval.py`, no rehearsal tab. The stage needs the whole LLM for itself.

4. Run it on the board from the repository root and watch the progress lines:

```bash
adb shell 'cd ~/Datathon-UPC-2026 && python3 predict.py --input data/final/train.jsonl --output results/final-predictions.csv 2>&1 | tee results/final-run.log'
```

   Each line prints `[n/N] id -> letter in X s, board est. Y s (status)`; the CSV is flushed
   after every problem. 20 problems: about 12 minutes. If `adb` drops, the process dies with
   it: rerun the same command, it resumes.

5. Check one row per (id, language), every answer a letter, no row over 60 s:

```bash
adb shell 'cd ~/Datathon-UPC-2026 && python3 -c "
import csv,json
keys=[(json.loads(l)[\"id\"],json.loads(l).get(\"language\",\"\")) for l in open(\"data/final/train.jsonl\") if l.strip()]
rows=list(csv.DictReader(open(\"results/final-predictions.csv\")))
print(len(keys),\"problems\",len(rows),\"rows\")
got={(r[\"id\"],r[\"language\"]) for r in rows}; print(\"missing:\",[k for k in keys if k not in got][:10])
print(\"not a letter:\",[r[\"id\"] for r in rows if r[\"answer\"] not in list(\"ABCDE\")][:10])
print(\"over 60 s:\",[(r[\"id\"],r[\"seconds\"]) for r in rows if float(r[\"seconds\"])>60])
print(\"slowest:\",sorted(((float(r[\"seconds\"]),r[\"id\"]) for r in rows))[-3:])
print(\"status:\",{s:sum(1 for r in rows if r[\"status\"]==s) for s in {r[\"status\"] for r in rows}})"'
```

6. Pull the CSV to the laptop and keep two copies:

```bash
adb pull /home/arduino/Datathon-UPC-2026/results/final-predictions.csv ./final-predictions.csv
```

### If a problem approaches 60 s

The stage budgets itself (`THINK_BUDGET_SECONDS=45` minus what the problem already cost, HTTP
timeout 57 s) and `predict.py` enforces `TIME_LIMIT_SECONDS=60`: a problem that runs out
answers with the fallback policy and a status other than plain `ok`, so the row is never
missing. Worst seen on the board with the stage on: 45 s. If one problem passes 50 s, do not
stop the run; if several do in a row, something else is using the LLM (`adb shell
'journalctl -u math-llm -n 20'`).

### If the board restarts or a row is missing: rerun the same command

`predict.py` **resumes**: when `--output` already exists it keeps the rows it holds and answers
only the (id, language) pairs that are missing, in input order. After a crash or a reboot, run
step 4 again, unchanged. `--fresh` throws the CSV away and starts over: only to change policy.

### Rehearsal with the practice set

The whole procedure above was run on 15 Nov with `data/demo/train.jsonl` (the 100 practice
rows, prepared and pushed exactly as in steps 1 and 2): `predict.py` with the shipped policy
took 0.5 s for the 100 rows; the brief-reasoning run on the board is in
`results/ablations.csv` (`practica-board-think-short-all`). To repeat it:

```bash
adb shell 'cd ~/Datathon-UPC-2026 && python3 predict.py --input data/demo/train.jsonl --output results/practica-predictions.csv --fresh 2>&1 | tail -3'
```
