# AUTOFLOW AI

AUTOFLOW AI is a powerful code analysis and debugging tool. It features a modern web interface that analyzes code, provides multi-language smart debugging, and generates elegant flowcharts natively using Graphviz.

## Features
- Smart Code Debugging
- Native Auto-Flowchart Generation
- Web Interface
- Multi-Language Support

## How to Run
Run the web application using:
```bash
pip install -r requirements.txt
python app.py
```
Then navigate to the URL provided in the terminal (usually `http://127.0.0.1:5002`).

## Desktop App
The desktop UI in `main.py` uses `customtkinter`. Install the desktop dependency set when needed:
```bash
pip install -r requirements-desktop.txt
```

## Vercel Deployment
- The repository exposes the Flask `app` from `app.py`, which Vercel supports directly.
- Static frontend files are served from `public/assets`.
- Runtime-generated diagrams are served from `/generated/...`.
- `.python-version` pins Python `3.12` for predictable builds.
- `vercel.json` sets a longer function duration for code analysis and diagram generation.
