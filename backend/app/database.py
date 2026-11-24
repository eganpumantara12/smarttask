from datetime import datetime, timezone

from sqlalchemy import DateTime, create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker
from sqlalchemy.types import TypeDecorator

from .config import settings

_is_sqlite = settings.database_url.startswith("sqlite")
engine = create_engine(
    settings.database_url,
    pool_pre_ping=True,
    connect_args={"check_same_thread": False} if _is_sqlite else {},
)
SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)


class Base(DeclarativeBase):
    pass


class UTCDateTime(TypeDecorator):
    """Selalu simpan UTC dan selalu kembalikan datetime ber-timezone UTC (mitigasi risiko zona waktu)."""

    impl = DateTime(timezone=True)
    cache_ok = True

    def process_bind_param(self, value, dialect):
        if value is None:
            return None
        if value.tzinfo is None:
            value = value.replace(tzinfo=timezone.utc)
        return value.astimezone(timezone.utc)

    def process_result_value(self, value, dialect):
        if value is None:
            return None
        if value.tzinfo is None:
            return value.replace(tzinfo=timezone.utc)
        return value.astimezone(timezone.utc)


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def ensure_columns() -> None:
    """Migrasi ringan: tambahkan kolom baru pada tabel lama (create_all tidak mengubah tabel yang sudah ada)."""
    from sqlalchemy import inspect, text

    insp = inspect(engine)
    if "users" not in insp.get_table_names():
        return
    have = {c["name"] for c in insp.get_columns("users")}
    pg = engine.dialect.name == "postgresql"
    ts = "TIMESTAMP WITH TIME ZONE" if pg else "DATETIME"
    true, one = ("TRUE", "TRUE") if pg else ("1", "1")
    wanted = {
        "last_login_at": f"{ts}",
        "reminder_enabled": f"BOOLEAN NOT NULL DEFAULT {true}",
        "reminder_time": "VARCHAR(5) NOT NULL DEFAULT '08:00'",
        "reminder_sound": f"BOOLEAN NOT NULL DEFAULT {one}",
        "deadline_alert_hours": "INTEGER NOT NULL DEFAULT 3",
    }
    with engine.begin() as conn:
        for name, ddl in wanted.items():
            if name not in have:
                conn.execute(text(f"ALTER TABLE users ADD COLUMN {name} {ddl}"))
