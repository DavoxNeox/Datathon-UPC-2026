#!/usr/bin/env python3
"""Laptop only: does what we run fit in the board's RAM?

    python3 dev/ram_budget.py                      # the two llama-servers
    python3 dev/ram_budget.py --match predict.py   # plus every process whose command contains this
    python3 dev/ram_budget.py --pid 12345          # plus this process

Adds up the resident memory (RSS) of the llama-server processes and of our app, and
compares it with what the board leaves free. The board numbers come from the README
(step 1.1: 3.1 GB available after boot) and from BOARD_* settings in config.env; the
App Lab reserve is NOT measured yet (Phase 10). RSS on a laptop is an approximation of
RSS on the board: same model files, same flags, different kernel and libc.
"""
import argparse
import os
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from copilot.config import CONFIG  # noqa: E402

AVAILABLE_MB = int(CONFIG.get("BOARD_RAM_AVAILABLE_MB", 3100))
APP_LAB_MB = int(CONFIG.get("BOARD_APP_LAB_RESERVE_MB", 500))
SAFETY = 0.10  # keep 10% free for the kernel's page cache and spikes


def processes():
    """(pid, rss_mb, command) for every process; works on macOS and Linux."""
    out = subprocess.check_output(["ps", "-axo", "pid=,rss=,command="], text=True)
    for line in out.splitlines():
        parts = line.split(None, 2)
        if len(parts) == 3 and parts[0].isdigit():
            yield int(parts[0]), int(parts[1]) / 1024, parts[2]


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--match", action="append", default=[], help="count processes whose command contains this")
    p.add_argument("--pid", action="append", type=int, default=[], help="count this process")
    args = p.parse_args()

    rows = []
    for pid, rss, cmd in processes():
        if pid == os.getpid():
            continue
        if "llama-server" in cmd or pid in args.pid or any(m in cmd for m in args.match):
            rows.append((pid, rss, cmd))
    if not rows:
        sys.exit("No llama-server running. Start it: dev/start_servers.sh")

    print(f"{'PID':>7} {'RSS MB':>8}  COMMAND")
    for pid, rss, cmd in rows:
        print(f"{pid:>7} {rss:8.0f}  {cmd[:90]}")
    total = sum(r[1] for r in rows)
    budget = AVAILABLE_MB - APP_LAB_MB
    limit = budget * (1 - SAFETY)
    print()
    print(f"Total measured here:        {total:6.0f} MB")
    print(f"Board available after boot: {AVAILABLE_MB:6d} MB  (README step 1.1)")
    print(f"App Lab reserve:            {APP_LAB_MB:6d} MB  (NOT measured: set BOARD_APP_LAB_RESERVE_MB after Phase 10)")
    print(f"Budget with {int(SAFETY * 100)}% safety:     {limit:6.0f} MB")
    if total > limit:
        print(f"\nWARNING: {total - limit:.0f} MB over the budget. The board would likely OOM-kill a server.")
        sys.exit(1)
    print(f"\nOK: {limit - total:.0f} MB of headroom. The README measured about 1100 MB for the two servers alone.")


if __name__ == "__main__":
    main()
