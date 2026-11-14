# Math copilot app (App Lab)

The student's web page, the teacher view and the LED matrix around the copilot.
The logic lives in `copilot/webapp.py` and `copilot/hints.py`; `python/main.py` only wires them.

## Run it on the laptop (sim)

```bash
python3 app/python/main.py
```

Open <http://127.0.0.1:7001> (port `SIM_WEB_PORT` in `config.env`). The teacher view is
<http://127.0.0.1:7001/teacher>. The LED matrix is drawn on the page from `hal.led.last_frame()`.
Both llama-servers must be up (`dev/start_servers.sh --status`) for rung 3 of the hint ladder;
everything else works without them.

## Run it on the board

Copy the repository to the board and start this folder as an App Lab app
(`arduino-app-cli app start user:<name>`, see `.skills/unoq-hardware-ui/SKILL.md`). With
`RUNTIME=board` the `web_ui` brick serves the same `assets/` and endpoints on port 7000, and
the sketch draws the frames Python sends over the Bridge.

## Endpoints (all JSON, all GET)

| path | what |
| --- | --- |
| `/api/state` | the whole session: problem (never its label), hints, answer, LED frame, mastery, timings; the page polls it |
| `/api/student/{name}` | choose the student pseudonym and load their next problem |
| `/api/lang/{cat,eng}` | page language |
| `/api/next` | next problem from `trainer.next_problem` (starts `hints.prefetch`) |
| `/api/answer/{A-E}` | `trainer.record_answer`, tick or cross on the LED, mastery map 3 s later |
| `/api/hint` | climb one rung (1, 2, then 3 again and again); runs in a thread |
| `/api/solution` | rung 4, only on request |
| `/api/image` | the problem picture as base64 PNG when `data/images/<id>_<lang>.png` exists |
| `/api/led`, `/api/led/path/{grid}` | the current frame; draw a path-count grid (manipulative b) |
| `/api/teacher` | `trainer.teacher_report()` when it exists, else `mastery_map` per student |

Manipulatives: `assets/manip/rotate.html`, `paths.html`, `dice.html`, opened from a strategy
card that names one. No fonts, scripts or styles are loaded from the network.
