from sqlalchemy import Engine, event
from sqlmodel import Session, create_engine

from app.config import DATABASE_URL


def _apply_sqlite_pragmas(engine: Engine) -> None:
    @event.listens_for(engine, "connect")
    def _set_sqlite_pragma(dbapi_connection, _connection_record):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.execute("PRAGMA journal_mode=WAL")
        cursor.execute("PRAGMA busy_timeout=5000")
        cursor.close()


def create_db_engine(url: str, *, echo: bool = False) -> Engine:
    engine = create_engine(url, echo=echo, connect_args={"check_same_thread": False})
    _apply_sqlite_pragmas(engine)
    return engine


engine = create_db_engine(DATABASE_URL)


def get_session():
    with Session(engine) as session:
        yield session
