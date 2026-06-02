"""Entry point for the desktop application (pywebview native window)."""

import os
import sys
import threading
import time
from pathlib import Path

from uvicorn import Config
from uvicorn.server import Server


class _ThreadServer(Server):
    """Uvicorn Server subclass that skips signal handler installation
    (signals only work from the main thread)."""

    def install_signal_handlers(self):
        pass


def _get_root() -> Path:
    if getattr(sys, "frozen", False):
        return Path(sys._MEIPASS)
    return Path(__file__).resolve().parent


def _get_data_dir() -> Path:
    if getattr(sys, "frozen", False):
        return Path(sys.executable).parent
    return Path(__file__).resolve().parent


BASE_DIR = _get_root()
DATA_DIR = _get_data_dir()
sys.path.insert(0, str(BASE_DIR))

os.environ["RENTAL_MGMT_DESKTOP"] = "1"


def _get_db_path() -> Path:
    return DATA_DIR / "data" / "db" / "rental.db"


def run_migrations():
    try:
        db_path = _get_db_path()
        db_path.parent.mkdir(parents=True, exist_ok=True)
        print(f"  Database: {db_path}")

        from alembic.config import Config

        from alembic import command

        alembic_ini = BASE_DIR / "alembic.ini"
        alembic_cfg = Config(str(alembic_ini))
        alembic_cfg.set_main_option("script_location", str(BASE_DIR / "alembic"))
        alembic_cfg.set_main_option("sqlalchemy.url", f"sqlite:///{db_path}")
        command.upgrade(alembic_cfg, "head")
        return True
    except Exception as e:
        print(f"[migrations] Error: {e}", file=sys.stderr)
        return False


def main():
    (DATA_DIR / "data" / "db").mkdir(parents=True, exist_ok=True)
    (DATA_DIR / "data" / "backups").mkdir(parents=True, exist_ok=True)

    port = int(os.getenv("RENTAL_PORT", "8000"))
    server = _ThreadServer(
        Config("app.main:app", host="127.0.0.1", port=port, log_level="info")
    )

    print("  Running database migrations...")
    run_migrations()

    print("  Starting server...")
    server_thread = threading.Thread(target=server.run)
    server_thread.start()
    time.sleep(2)

    url = f"http://127.0.0.1:{port}"

    try:
        import webview

        print(f"  Opening native window at {url}")
        webview.create_window("Rental Management", url, width=1280, height=800)
        webview.start()
    except Exception:
        import webbrowser

        print(f"  Native window not available, opening browser at {url}")
        print("  Close the browser window and press Enter to stop the server...")
        webbrowser.open(url)
        input()

    print("  Shutting down server...")
    server.should_exit = True
    server_thread.join(timeout=10)
    print("  Done.")


if __name__ == "__main__":
    main()
