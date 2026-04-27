from __future__ import annotations

import os
import socket
import sys
import threading
import time
import urllib.error
import urllib.request
import webbrowser
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path


APP_NAME = "AI Debate Trainer"
BACKEND_HOST = "127.0.0.1"
BACKEND_PORT = 8000


def app_root() -> Path:
    bundled_root = getattr(sys, "_MEIPASS", None)
    if bundled_root:
        return Path(bundled_root)
    return Path(__file__).resolve().parent


ROOT = app_root()
BACKEND_DIR = ROOT / "backend"
FRONTEND_DIR = ROOT / "frontend"


def configure_runtime() -> None:
    sys.path.insert(0, str(BACKEND_DIR))

    app_data = Path(os.getenv("LOCALAPPDATA") or Path.home() / "AppData" / "Local")
    data_dir = app_data / APP_NAME
    data_dir.mkdir(parents=True, exist_ok=True)
    os.environ.setdefault("DATABASE_PATH", str(data_dir / "ai_debate_trainer.db"))


def is_port_open(host: str, port: int) -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.settimeout(0.3)
        return sock.connect_ex((host, port)) == 0


def backend_is_healthy() -> bool:
    try:
        with urllib.request.urlopen(f"http://{BACKEND_HOST}:{BACKEND_PORT}/health", timeout=1.5) as response:
            return response.status == 200
    except (urllib.error.URLError, TimeoutError, OSError):
        return False


def run_backend() -> None:
    import uvicorn
    from app.main import app as fastapi_app

    config = uvicorn.Config(
        fastapi_app,
        host=BACKEND_HOST,
        port=BACKEND_PORT,
        log_level="warning",
        access_log=False,
    )
    server = uvicorn.Server(config)
    server.run()


def ensure_backend() -> None:
    if backend_is_healthy():
        return

    if is_port_open(BACKEND_HOST, BACKEND_PORT):
        raise RuntimeError(
            f"Port {BACKEND_PORT} is already in use, but it is not serving {APP_NAME}."
        )

    thread = threading.Thread(target=run_backend, name="ai-debate-backend", daemon=True)
    thread.start()

    deadline = time.time() + 25
    while time.time() < deadline:
        if backend_is_healthy():
            return
        time.sleep(0.25)

    raise RuntimeError("Backend did not become healthy in time.")


def start_frontend_server() -> tuple[ThreadingHTTPServer, str]:
    if not (FRONTEND_DIR / "web.html").exists():
        raise FileNotFoundError(f"Cannot find frontend at {FRONTEND_DIR / 'web.html'}")

    class FrontendHandler(SimpleHTTPRequestHandler):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, directory=str(FRONTEND_DIR), **kwargs)

        def log_message(self, format: str, *args) -> None:
            return

    server = ThreadingHTTPServer(("127.0.0.1", 0), FrontendHandler)
    thread = threading.Thread(target=server.serve_forever, name="ai-debate-frontend", daemon=True)
    thread.start()
    return server, f"http://127.0.0.1:{server.server_port}/web.html"


def open_window(url: str) -> None:
    try:
        import webview
    except ImportError:
        webbrowser.open(url)
        print("pywebview is not installed. Opened the app in your default browser.")
        print("Install desktop dependencies with: pip install -r requirements-desktop.txt")
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            return

    webview.create_window(
        APP_NAME,
        url,
        width=1280,
        height=820,
        min_size=(1024, 680),
        text_select=True,
    )
    webview.start(debug=os.getenv("AI_DEBATE_DEBUG", "").lower() == "true")


def main() -> None:
    configure_runtime()
    ensure_backend()
    frontend_server, frontend_url = start_frontend_server()
    try:
        open_window(frontend_url)
    finally:
        frontend_server.shutdown()


if __name__ == "__main__":
    main()
