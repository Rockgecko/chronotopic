# Chronotopic

A personal project to develop a timeline for visualizing how events and lifetimes in history overlapped.

Starting simple, but things may evolve...!

Running locally (this is not packaged for distribution at this point):

1. Requires [uv](https://docs.astral.sh/uv/) to be installed
2. From `backend` folder, run: `uv run uvicorn main:app --reload`
3. From `frontend` folder, run: `python -m http.server 8001`
4. Navigate to `http://127.0.0.1:8001` in the browser.
