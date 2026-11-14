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

The organisers grade 50% of the project on a **test exam**: a file of problems in the M3Kang
format, answered by `predict.py` and corrected from its CSV. The details of the file and of the
procedure are not known yet; the blanks below are marked `[?]` and the questions to ask the
organisation **today** are at the end of this section.

### Procedure on the board

1. Copy the exam file to the board (laptop; `[?]` = the file name they give us):

```bash
adb push [?]exam.jsonl /home/arduino/Datathon-UPC-2026/data/exam.jsonl
```

   If the exam comes with images, push the folder too; `predict.py` never reads them (the
   pipeline is text-only), so a missing image changes nothing.

2. Check the file: one JSON object per line, the same fields as `data/sample_problems.jsonl`
   (`id`, `language`, `level`, `text`, `options`; `label` may be absent):

```bash
adb shell 'cd ~/Datathon-UPC-2026 && wc -l data/exam.jsonl && head -c 300 data/exam.jsonl && python3 -c "import json,sys; ids=[json.loads(l)[\"id\"] for l in open(\"data/exam.jsonl\") if l.strip()]; print(len(ids), \"rows\", len(set(ids)), \"distinct ids\")"'
```

3. Nothing else may use the model servers (close every rehearsal tab, no `eval.py` running):
   the 54 s and 41 s outliers in `docs/results-A.md` §10 came from foreign requests queued on
   the LLM. The shipped policy (`SOLVERS=1`, `MIDDLE_VALUE=1`, `LETTER_MODEL=0`) calls the
   model only inside a family solver, so the run is mostly milliseconds per problem.

4. Run it from the repository root on the board, in a shell that survives a dropped `adb`
   (`nohup`), and watch the progress lines:

```bash
adb shell 'cd ~/Datathon-UPC-2026 && nohup python3 predict.py --input data/exam.jsonl --output results/exam-predictions.csv > results/exam-run.log 2>&1 &'
```

```bash
adb shell 'tail -f /home/arduino/Datathon-UPC-2026/results/exam-run.log'
```

   Each line prints `[n/N] id -> letter in X s, board est. Y s (status)`. The CSV falls in
   `results/exam-predictions.csv` on the board, columns `id, language, answer, seconds, status`,
   flushed after every problem (a crash keeps the rows done so far).

5. When it ends, check **one row per id**, every answer a letter A to E, no row over 60 s:

```bash
adb shell 'cd ~/Datathon-UPC-2026 && python3 -c "
import csv,json
ids=[json.loads(l)[\"id\"] for l in open(\"data/exam.jsonl\") if l.strip()]
rows=list(csv.DictReader(open(\"results/exam-predictions.csv\")))
print(len(ids),\"problems\",len(rows),\"rows\")
got={r[\"id\"] for r in rows}; print(\"missing:\",[i for i in ids if i not in got][:10])
print(\"not a letter:\",[r[\"id\"] for r in rows if r[\"answer\"] not in list(\"ABCDE\")][:10])
print(\"over 60 s:\",[(r[\"id\"],r[\"seconds\"]) for r in rows if float(r[\"seconds\"])>60])
print(\"slowest:\",sorted(((float(r[\"seconds\"]),r[\"id\"]) for r in rows))[-3:])
print(\"status:\",{s:sum(1 for r in rows if r[\"status\"]==s) for s in {r[\"status\"] for r in rows}})"'
```

6. Pull the CSV to the laptop and keep two copies (laptop and a USB stick):

```bash
adb pull /home/arduino/Datathon-UPC-2026/results/exam-predictions.csv ./exam-predictions.csv
```

### If a problem approaches 60 s

`predict.py` enforces `TIME_LIMIT_SECONDS=60` itself: a problem that runs out answers
`FALLBACK_ANSWER` (D) with a status other than `ok`, so the row is never missing. Worst
measured on the full validation set: 38.7 s (a problem routed to a family whose extraction
then matched no option). If the log shows one problem past 45 s: do not stop the run; note the
id; after the run, check in the CSV that its status says why. If several problems are slow in a
row, something else is using the LLM: `adb shell 'journalctl -u math-llm -n 20'` shows the
foreign requests, and the run is repeated once they stop. Only if the organisers allow a rerun.

### If an id gets no row (a crash)

Rerun on the missing ids only and append (the CSV header must appear once):

```bash
adb shell 'cd ~/Datathon-UPC-2026 && python3 -c "
import csv,json
done={r[\"id\"] for r in csv.DictReader(open(\"results/exam-predictions.csv\"))}
open(\"data/exam-rest.jsonl\",\"w\").writelines(l for l in open(\"data/exam.jsonl\") if l.strip() and json.loads(l)[\"id\"] not in done)" && python3 predict.py --input data/exam-rest.jsonl --output results/exam-rest.csv && tail -n +2 results/exam-rest.csv >> results/exam-predictions.csv'
```

### Questions for the organisation (ask today)

1. **Size:** how many problems, and how many per language and level? (It sets the run time:
   at 0.38 s mean, 500 problems take about 3 minutes; the worst single problem about 40 s.)
2. **Format:** the same JSONL as `data/sample_problems.jsonl` (`id`, `language`, `level`,
   `text`, `options` as a dict A to E)? Are images included, and may a problem need its image?
   Which languages (Catalan, English, both, others)? Is `label` absent?
3. **Time allowed:** per problem (the README says 60 s) and in total for the whole file? Does
   the clock include loading the models, or only `predict.py`'s own run?
4. **Where it runs:** on our board in front of them, or do we deliver the CSV? If on the board,
   do they bring the file on a USB stick or over the network, and may we keep the services
   already running?
5. **Scoring:** does an empty or non-letter answer count as wrong (we always answer a letter),
   is there a penalty for wrong answers (Kangaroo style) or plain accuracy, and are the two
   languages of one problem scored as two items?
6. **Reruns:** if the board crashes or a row is missing, may we rerun on the missing ids?
7. **Policy freeze:** is the `config.env` of the submitted commit what is graded, or may the
   run use a later commit?

