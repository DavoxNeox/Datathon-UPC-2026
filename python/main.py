"""Math copilot, App Lab entry point. Thin on purpose: the logic lives in copilot/webapp.py.

    RUNTIME=sim  python3 python/main.py          # laptop: http://127.0.0.1:7001
    RUNTIME=board                                # the board: App Lab runs this file, page on port 7000

The repository root IS the App Lab app (app.yaml, python/, assets/, sketch/ at the root):
App Lab mounts only the app folder inside its container, so everything the app needs,
the copilot package, config.env, data/ and data_curated/, must live below it. The copilot
package is one folder up from here. App.run() is called inside hal.web.serve on the board.
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)  # python/ sits at the repository root, which App Lab mounts as /app
sys.path.insert(0, ROOT)

from copilot import webapp  # noqa: E402
from copilot.hal import web  # noqa: E402

ASSETS = os.path.join(ROOT, "assets")

webapp.start()
web.serve(webapp.routes(), ASSETS)
