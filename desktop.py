"""Entry point for the desktop application (pywebview native window)."""

import os
import sys
import threading
import time
import urllib.error
import urllib.request
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


def _get_db_path() -> Path:
    return DATA_DIR / "data" / "db" / "rental.db"


def _get_icon_path() -> Path | None:
    ico = BASE_DIR / "build" / "icon.ico"
    return ico if ico.exists() else None


def _fatal(message: str) -> None:
    print(f"[fatal] {message}", file=sys.stderr)
    if sys.platform == "win32":
        try:
            import ctypes

            ctypes.windll.user32.MessageBoxW(None, message, "Rental Management", 0x10)
        except Exception:
            pass
    elif sys.platform != "linux" or not os.environ.get("DISPLAY"):
        pass
    else:
        try:
            import webview

            webview.create_window("Rental Management", html=f"<h2>Error</h2><p>{message}</p>")
            webview.start()
        except Exception:
            pass
    raise SystemExit(1)


def run_migrations() -> None:
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


def backup_if_exists() -> None:
    from app.services.backup_service import BackupService

    db_path = _get_db_path()
    if not db_path.exists():
        return
    stamp = time.strftime("%Y%m%d_%H%M%S")
    backup_path = DATA_DIR / "data" / "backups" / f"pre-upgrade-{stamp}.db"
    BackupService.backup_database(db_path, backup_path)
    print(f"  Pre-upgrade backup: {backup_path.name}")


def seed_demo_if_enabled() -> None:
    if os.getenv("RENTAL_MGMT_DEMO") != "1":
        return

    from sqlmodel import Session, select

    from app.database import engine
    from app.models.owner import Owner
    from app.seeder import seed_database

    with Session(engine) as session:
        if session.exec(select(Owner)).first() is not None:
            return
        print("  Seeding database with demo data...")
        seed_database(session)
        session.commit()
        print("  Seed done.")


def catch_up_jobs() -> None:
    from app.jobs.daily_overdue import detect_overdue_invoices
    from app.jobs.monthly_invoicing import generate_monthly_invoices

    try:
        invoices = generate_monthly_invoices()
        if invoices:
            print(f"  Catch-up: generated {len(invoices)} invoices")
    except Exception as e:
        print(f"[catch-up] Invoice generation failed: {e}", file=sys.stderr)

    try:
        overdue = detect_overdue_invoices()
        if overdue:
            print(f"  Catch-up: {len(overdue)} overdue invoices detected")
    except Exception as e:
        print(f"[catch-up] Overdue detection failed: {e}", file=sys.stderr)


def _wait_for_server(server: Server, host: str, port: int, timeout: float = 15.0) -> bool:
    deadline = time.monotonic() + timeout
    health_url = f"http://{host}:{port}/health"
    while time.monotonic() < deadline:
        if getattr(server, "started", False):
            try:
                with urllib.request.urlopen(health_url, timeout=1) as response:
                    if response.status == 200:
                        return True
            except (urllib.error.URLError, OSError):
                pass
        time.sleep(0.25)
    return False


def main():
    (DATA_DIR / "data" / "db").mkdir(parents=True, exist_ok=True)
    (DATA_DIR / "data" / "backups").mkdir(parents=True, exist_ok=True)
    (DATA_DIR / "data" / "invoices").mkdir(parents=True, exist_ok=True)

    port = int(os.getenv("RENTAL_PORT", "8000"))
    host = "127.0.0.1"
    server = _ThreadServer(
        Config(
            "app.main:app",
            host=host,
            port=port,
            log_level="error",
            access_log=False,
        )
    )

    try:
        backup_if_exists()
        print("  Running database migrations...")
        run_migrations()
    except Exception as e:
        _fatal(f"Database migration failed:\n{e}")

    seed_demo_if_enabled()
    catch_up_jobs()

    print("  Starting server...")
    server_thread = threading.Thread(target=server.run, daemon=True)
    server_thread.start()

    url = f"http://{host}:{port}"

    if not _wait_for_server(server, host, port):
        _fatal(f"The server did not start on {url}. Is port {port} already in use?")

    try:
        import webview

        print(f"  Opening native window at {url}")
        webview.create_window(
            "Rental Management",
            url,
            width=1280,
            height=800,
            icon=_get_icon_path(),
        )
        webview.start()
    except Exception:
        import webbrowser

        print(f"  Native window not available, opening browser at {url}")
        print("  Close the browser window and press Enter to stop the server...")
        webbrowser.open(url)
        try:
            input()
        except EOFError:
            while server_thread.is_alive():
                time.sleep(1)

    print("  Shutting down server...")
    server.should_exit = True
    server_thread.join(timeout=10)
    print("  Done.")


if __name__ == "__main__":
    main()
