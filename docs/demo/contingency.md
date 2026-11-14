# Contingency plan

Rule: whatever breaks, the narration never stops. V2 keeps the script, V3 fixes or switches
within 15 seconds, V4 decides at 15 s whether to go to the video. Every row below is "what to
do" and "what to say" for one failure; the backup video is §9.

| # | failure | what V3 does (under 15 s) | what V2 says |
| --- | --- | --- | --- |
| 1 | **The board does not boot** (no `adb` after 3 min, or a service is not `active`) | Before the slot: unplug, wait 10 s, plug again, 2 more minutes. During the slot: go to the video (§9). If only one service is down: `adb shell sudo systemctl restart math-llm math-embed math-relay`, then `TMPDIR=/tmp arduino-app-cli app stop` and `start user:math-copilot`; this takes about 1 min, too long for the slot. | «La placa va arrencar fa deu minuts; ara mateix no respon. Us ensenyo la gravació d'avui al matí, feta amb aquesta mateixa placa.» |
| 2 | **`adb` does not see the board** (`adb devices` empty or `unauthorized`) | Swap the USB cable for the spare (a charge-only cable is the usual cause); try the other USB-C port of the laptop; `adb kill-server && adb devices`. If `unauthorized`: the board's SSH over Wi-Fi is off on stage, so go to the video. | «El cable. Un segon.» If it takes longer: row 1's sentence. |
| 3 | **The web page does not load** (`127.0.0.1:7002` spins, or `curl /api/state` fails) | `adb forward tcp:7002 tcp:7000` again (the forward dies when `adb` reconnects). Then `adb shell 'TMPDIR=/tmp arduino-app-cli app ps'`; if the app is not running, `app start user:math-copilot` and talk for 20 s. If the page loads but shows a problem from before, press `Canvia d'alumne` twice (it confirms in line). | «La pàgina la serveix la placa pel cable; la torno a enllaçar.» Then continue at the same point of the script. |
| 4 | **A hint takes more than 10 s** ("Pensant una pista…" stays) | Nothing in Catalan uses the model, so this means the app is stuck. While a hint is pending the app answers `busy` to every other button (letters, `Continua`, `Canvia d'alumne`): reloading the tab does not help. Count to 15; if the card has not appeared, go to the video (§9). After the pitch: `TMPDIR=/tmp arduino-app-cli app stop` and `start user:math-copilot`. | «Mentre la placa busca el veí, compara embeddings de tots els problemes del mateix tema, dins de la placa.» Then, at 15 s: row 9's sentence. |
| 5 | **The LED matrix does not change** after a letter | Nothing to fix on stage (the frame goes over the Bridge to the microcontroller; the page shows the same frame in its corner). V1 keeps the board up anyway; V3 points at the action sheet at the bottom, which turns green or red with the verdict, and at the topic progress bar at the top of the page. After the pitch: `TMPDIR=/tmp arduino-app-cli app stop` and `start` recompiles the sketch. | «La matriu de la pàgina és el mateix quadre que envia a la placa: tick, creu i mapa de domini.» |
| 6 | **The projector does not show the laptop** | V3: `Cmd+F1` (mirror displays), then the display menu in the macOS menu bar; try the other adapter. If 15 s pass, V1 walks the board to the jury's table and V3 turns the laptop screen to them; the demo goes on at the laptop. | «Veniu una mica més a prop, ho veureu millor a la placa i al portàtil.» |
| 7 | **Power cut** (room goes dark, projector off) | The board is powered by the laptop, the laptop by its battery: nothing stops. V3 raises the laptop brightness to maximum, V1 brings the board to the jury (the LED matrix is bright in the dark). The phone video is the second fallback. | «La placa va amb la bateria del portàtil: la demo continua.» |
| 8 | **The wrong problem appears** (not `lvl-1_2024_2` after `Comença`) | Do not restart. V2 adapts: ask for `Pista` anyway (rung 1 always returns a neighbour of the same topic, easier or "del mateix nivell"), then `Pista` again, then answer any letter. The story (hint, strategy, tick or cross, mastery) is the same. | V2 reads the topic shown under the problem and says it instead of "taulers i patrons"; nothing else changes. |
| 9 | **Any failure past 15 s** | Tab 3: play the backup video (90 s), full screen. V2 narrates over it with the demo script, same timings. | «Us ensenyo la gravació d'aquest matí amb aquesta placa; el guió és el mateix.» |

Decision rules: the phone video exists for rows 1, 2 and 9 only; everything else is solved
live. If the demo block ends early because a step was skipped, V3 uses the spare seconds on
the teacher view; the numbers block starts at 110 s of the pitch regardless.

## 9. The backup video: storyboard (90 s, one take, phone in landscape)

Record it the morning of the pitch on the real board after the rehearsal of `runbook.md`
§6, with the same pseudonym (the chain is deterministic, so the video shows exactly what
the live demo would). One person films, one clicks, one holds the board; no audio needed
(V2 narrates live over it), but keep the room quiet in case it is played with sound. Phone
settings: 1080p, 30 fps, exposure locked on the laptop screen (tap and hold), torch off.

| s | shot | what is on screen | note |
| --- | --- | --- | --- |
| 0-8 | wide: the board in a hand, the USB cable to the laptop, no other cable | the start screen on the laptop in the background with `Mariona1` and `6è de primària` typed | establishes "board, one cable, offline" |
| 8-14 | close-up of the laptop screen | the click on `Comença`, problem 1 appears with its picture and the five options | zoom to 150% beforehand |
| 14-26 | same framing | click `Pista`: the "Un problema semblant" card with the neighbour's picture | hold 6 s so the viewer can see both grids |
| 26-38 | same framing | click `Pista`: the strategy card; then click `C`; the action sheet turns green with "Correcte!" | |
| 38-46 | **pan to the board**, close-up of the LED matrix | the tick, then (after 3 s) the mastery map with the boards row lit | the only shot where the LED matters: do not rush it |
| 46-52 | back to the laptop | the action sheet green; the progress of Taulers raised; click `Continua` | |
| 52-66 | laptop | problem 2 (folded sheet) with its picture; `Pista` (neighbour with picture), `Pista` (strategy with "Gira i volteja"); click the manipulative, which opens under the hints, rotate the figure once | |
| 66-74 | laptop, then **pan to the board** | click `A`; "No és això. La resposta era E."; the cross on the LED matrix | second LED shot |
| 74-84 | laptop | the action sheet red; the progress bars (spatial at 1, boards at 2); switch to the teacher tab, reload: Mariona1's row and hits by level | |
| 84-90 | wide again: board, cable, laptop | the timeline at the bottom of the page: every step in milliseconds, "placa (est.)" at 0.0 | end on the board |

Export without edits; put the file on the laptop (tab 3 of `runbook.md` §8, paused at 0:00)
and keep a copy on the phone. Check once that it plays full screen in the browser
(`file:///…/demo-backup.mp4`) and that the laptop's volume is muted if it has sound. Do not
commit the video: it shows M3Kang statements.

## Who does what when something breaks

- **V3** (laptop): fixes rows 2, 3, 4, 6, 8; starts the video.
- **V1** (board): rows 5 and 7, walks the board to the jury when the screen is lost.
- **V4** (time): counts 15 s aloud to themself, says "vídeo" to V3 at 15 s.
- **V2** (voice): never stops, never apologises more than one sentence.
