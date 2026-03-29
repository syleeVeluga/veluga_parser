from sqlalchemy import create_engine, event, text
from sqlalchemy.orm import sessionmaker, DeclarativeBase
from src.backend.config import DATABASE_URL


engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False},
)


@event.listens_for(engine, "connect")
def set_wal_mode(dbapi_connection, connection_record):
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA journal_mode=WAL")
    cursor.close()


SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    pass


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def create_tables():
    from src.backend.models import job, result  # noqa: F401 — register models
    Base.metadata.create_all(bind=engine)
    # Migrate: add deleted_at column if not present (idempotent)
    with engine.connect() as conn:
        try:
            conn.execute(text("ALTER TABLE jobs ADD COLUMN deleted_at DATETIME"))
            conn.commit()
        except Exception:
            pass  # Column already exists
