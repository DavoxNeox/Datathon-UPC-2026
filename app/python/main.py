"""Math copilot, App Lab entry point. Thin on purpose: the logic lives in copilot/webapp.py.

    RUNTIME=sim  python3 app/python/main.py      # laptop: http://127.0.0.1:7001
    RUNTIME=board                                # the board: App Lab runs this file, page on port 7000

The repository is checked out on the board, and this app folder lives inside it, so the
copilot package is three folders up. App.run() is called inside hal.web.serve on the board.
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, ROOT)

from copilot import webapp  # noqa: E402
from copilot.hal import web  # noqa: E402

ASSETS = os.path.join(os.path.dirname(HERE), "assets")

webapp.start()
web.serve(webapp.routes(), ASSETS)
