"""
The door between the browser and the rest of the backend.

app.py                   - the FastAPI app: gets each request from the
                           browser (e.g. "Send was pressed") and runs
                           the right function for it
request_bodies.py        - the shape of the JSON each POST sends
answers_to_browser.py    - shapes the data sent back for the screen:
                           project, map tree, chat
files_to_browser.py      - finds the app's own files (HTML, JavaScript,
                           CSS) for app.py to send — not data

No product rules live here; those are in backend/project/.
"""
