"""
HTTP process entry for app/ — starts the server that serves ui/ and
the API.

What each request does lives in backend/api/ (app.py for the routes,
answers_to_browser.py for what they send back). This file only starts
uvicorn with that app.

Run from app/ (this directory), with app/'s own venv:
    .venv/bin/python -m server
Then open http://localhost:8000/ in a browser; every route is listed at
http://localhost:8000/docs.

HOST is localhost unless set: only this machine can connect. A host
running the public demo sets HOST=0.0.0.0 behind its HTTPS proxy, and
PORT (docs/demo.md).
"""

import os

import uvicorn

from backend.api.app import app

HOST = os.environ.get("HOST", "localhost")
PORT = int(os.environ.get("PORT", "8000"))


if __name__ == "__main__":
    print(f"web prototype - http://{HOST}:{PORT}/")
    # No access log: the terminal is for debug lines, as before.
    uvicorn.run(app, host=HOST, port=PORT, access_log=False)
