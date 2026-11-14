# Deploy on the Arduino UNO Q

From a board set up with steps 0 to 7 of the datathon README (Debian updated by App Lab,
build tools, llama.cpp at `2cbe0ec`, both models, both systemd services) to our copilot.
Commands run **on the board** unless marked "laptop". Connect with `ssh arduino@<ip>` or,
over USB, `adb shell` (`brew install --cask android-platform-tools` on macOS).

Measured on our board (14 Nov 2026): the board's own `apt-get install arduino-unoq` runs
after the first App Lab setup and holds the dpkg lock for about 10 minutes; wait for it
(`pgrep -a apt-get`) before step 2. Downloading the two models took about 5 minutes over Wi-Fi.
Building llama.cpp takes about 30 minutes.

## 1. Our code

```bash
cd ~ && git clone -b main https://github.com/DavoxNeox/Datathon-UPC-2026.git
cd ~/Datathon-UPC-2026 && chmod +x board/*.sh && ./board/00_check_board.sh
```

Steps 2 to 7 of the README are the scripts `board/01_install_packages.sh` (needs the sudo
password), `02_build_llama_cpp.sh`, `03_download_models.sh`, `04_install_services.sh` (sudo),
`05_smoke_test.sh`. `config.env` has `RUNTIME=auto`: the code detects the board from
`/proc/device-tree/model`, nothing to edit.

## 2. The data (laptop)

M3Kang is research-only: it travels over the cable, never through git. From the laptop that
ran `laptop/prepare_m3kang.py --out ~/m3kang-data`:

```bash
adb push ~/m3kang-data/train.jsonl ~/m3kang-data/val.jsonl ~/m3kang-data/index.db /home/arduino/Datathon-UPC-2026/data/
```

```bash
adb push ~/m3kang-data/images /home/arduino/Datathon-UPC-2026/data/images
```

(144 MB; needed for rung 1 of the hint ladder on visual topics and for the explorer.) Over
Wi-Fi, `scp` to `arduino@<ip>:~/Datathon-UPC-2026/data/` does the same. `index.db` was built
on the laptop from the English and Catalan training problems with the same bge-small model;
rebuilding it on the board (`python3 build_index.py --input data/train.jsonl --db data/index.db`)
takes about 15 minutes and gives the same vectors.

## 3. Check and measure

```bash
cd ~/Datathon-UPC-2026 && python3 -m unittest discover tests
```

```bash
python3 predict.py --input data/sample_problems.jsonl --output results/smoke.csv && cat results/smoke.csv
```

```bash
python3 board/calibrate_speed.py
```

`calibrate_speed.py` prints the board's real reading, writing and embedding speeds next to
the `BOARD_*` constants in `config.env`; run it with `--write` to update them, and commit the
change with the date. Then the baseline and the official run, on the board:

```bash
python3 eval.py --limit 50 --languages eng --name A-board-baseline
```

```bash
python3 predict.py --input data/val.jsonl --output results/predictions.csv
```

`eval.py` prints the real seconds (the limit is checked against them in `RUNTIME=board`)
and the estimate from the token counts side by side: after calibration they should agree.

## 4. The App Lab app (student page, teacher view, LED matrix)

App Lab apps live in `/home/arduino/ArduinoApps/<name>/`, and App Lab mounts **only that
folder** inside the app's Python container (as `/app`, on its own Docker network). That is why
the repository root is the app: `app.yaml`, `python/`, `assets/` and `sketch/` sit next to
`copilot/`, `config.env`, `data/` and `data_curated/`. Link the repository in, then start it:

```bash
ln -s ~/Datathon-UPC-2026 ~/ArduinoApps/math-copilot
```

```bash
TMPDIR=/tmp arduino-app-cli app start user:math-copilot
```

Verified on our board: App Lab lists the symlinked folder as `user:math-copilot`. The
`TMPDIR=/tmp` matters when you run this over `adb shell`, whose environment sets
`TMPDIR=/data/local/tmp` (an Android path that does not exist on the board); without it
the sketch build stops at "Generating function prototypes" with `stat /data/local/tmp: no
such file or directory`. Over SSH the default is fine.

```bash
arduino-app-cli app logs /home/arduino/ArduinoApps/math-copilot --all
```

The `web_ui` brick serves the page on port 7000. From the laptop over USB:
`adb forward tcp:7000 tcp:7000`, then <http://127.0.0.1:7000> (teacher view at `/teacher`).
Only one App Lab app runs at a time, and the sketch compiles on first start (about a minute).
**Still to verify on the board:** the RAM with everything running: `free -m` should keep a few
hundred MB available next to the two servers (1059 MB + 75 MB measured) and the App Lab
containers.

## 5. Demo mode

Wi-Fi off, services started at boot, the laptop only shows the page over USB:

```bash
adb forward tcp:7000 tcp:7000
```

Rehearse the chosen problems the same day on the board. `python3 eval.py --simulate-latency`
on a laptop rehearses the timing when the board is not at hand. Shut down with `sudo poweroff`.
