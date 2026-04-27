# Windows desktop app

This project can run as a local Windows desktop app. The app shell starts the
FastAPI backend on `127.0.0.1:8000`, serves `frontend/web.html` from a local
static server, and opens it in a native WebView window.

## Requirements

- Windows 10 or newer
- Python 3.11+
- Ollama running locally if `DEMO_MODE=false`
- The configured Ollama model, for example `qwen3:latest`

## Run in development

From the repository root:

```powershell
powershell -ExecutionPolicy Bypass -File scripts\run_windows_app.ps1
```

The script creates `.venv`, installs backend and desktop dependencies, starts
the local backend, and opens the app window.

## Build an `.exe`

From the repository root:

```powershell
powershell -ExecutionPolicy Bypass -File scripts\build_windows_app.ps1
```

The output is:

```text
dist\AI Debate Trainer\AI Debate Trainer.exe
```

Keep the whole `dist\AI Debate Trainer` folder together when sharing the app.

## Local data

The desktop launcher stores the SQLite database under:

```text
%LOCALAPPDATA%\AI Debate Trainer\ai_debate_trainer.db
```

This keeps user data outside the installed app folder.
