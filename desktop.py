"""Entry point for the desktop application (pywebview native window)."""

import os
import sys
import threading
from pathlib import Path


def _get_root() -> Path:
    """Get the root directory containing bundled data files."""
    if getattr(sys, "frozen", False):
        return Path(sys._MEIPASS)
    return Path(__file__).resolve().parent


def _get_data_dir() -> Path:
    """Get the directory for persistent data (database, backups)."""
    if getattr(sys, "frozen", False):
        return Path(sys.executable).parent
    return Path(__file__).resolve().parent


BASE_DIR = _get_root()
DATA_DIR = _get_data_dir()
sys.path.insert(0, str(BASE_DIR))

os.environ["RENTAL_MGMT_DESKTOP"] = "1"


def run_migrations():
    """Run Alembic migrations at startup."""
    try:
        from alembic.config import Config
        from alembic import command

        alembic_ini = BASE_DIR / "alembic.ini"
        alembic_cfg = Config(str(alembic_ini))
        alembic_cfg.set_main_option("script_location", str(BASE_DIR / "alembic"))
        command.upgrade(alembic_cfg, "head")
        return True
    except Exception as e:
        print(f"[migrations] Error: {e}", file=sys.stderr)
        return False


def start_server():
    """Start the FastAPI server with uvicorn."""
    import uvicorn

    port = int(os.getenv("RENTAL_PORT", "8000"))
    uvicorn.run(
        "app.main:app",
        host="127.0.0.1",
        port=port,
        log_level="info",
    )


def main():
    (DATA_DIR / "data" / "db").mkdir(parents=True, exist_ok=True)
    (DATA_DIR / "data" / "backups").mkdir(parents=True, exist_ok=True)

    print("  Running database migrations...")
    run_migrations()

    print("  Starting server...")
    server_thread = threading.Thread(target=start_server, daemon=True)
    server_thread.start()

    import time
    time.sleep(2)

    port = int(os.getenv("RENTAL_PORT", "8000"))
    url = f"http://127.0.0.1:{port}"

    try:
        import webview
        print(f"  Opening native window at {url}")
        webview.create_window("Rental Management", url, width=1280, height=800)
        webview.start()
    except Exception:
        import webbrowser
        print(f"  Native window not available, opening browser at {url}")
        print("  Press Ctrl+C to stop")
        webbrowser.open(url)
        try:
            while True:
                time.sleep(3600)
        except KeyboardInterrupt:
            print("Shutting down...")


if __name__ == "__main__":
    main()
