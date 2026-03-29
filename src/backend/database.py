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


_JOB_MIGRATIONS = [
    "ALTER TABLE jobs ADD COLUMN deleted_at DATETIME",
    "ALTER TABLE jobs ADD COLUMN doc_title TEXT",
    "ALTER TABLE jobs ADD COLUMN element_count INTEGER",
    "ALTER TABLE jobs ADD COLUMN chunk_count INTEGER",
    "ALTER TABLE jobs ADD COLUMN has_equations BOOLEAN DEFAULT 0",
    "ALTER TABLE jobs ADD COLUMN has_code BOOLEAN DEFAULT 0",
    "ALTER TABLE jobs ADD COLUMN has_structure BOOLEAN DEFAULT 0",
    "ALTER TABLE jobs ADD COLUMN engine VARCHAR(20) DEFAULT 'docling'",
    "ALTER TABLE jobs ADD COLUMN parse_duration_seconds REAL",
]

_RESULT_MIGRATIONS = [
    "ALTER TABLE parsed_results ADD COLUMN schema_version TEXT DEFAULT '1.0'",
    "ALTER TABLE parsed_results ADD COLUMN chunks_json TEXT",
    "ALTER TABLE parsed_results ADD COLUMN toc_json TEXT",
    "ALTER TABLE parsed_results ADD COLUMN element_count INTEGER",
    "ALTER TABLE parsed_results ADD COLUMN chunks_path TEXT",
    "ALTER TABLE parsed_results ADD COLUMN structure_json TEXT",
    "ALTER TABLE parsed_results ADD COLUMN markdown_pages_dir TEXT",
]


def create_tables():
    from src.backend.models import job, result  # noqa: F401 — register models
    Base.metadata.create_all(bind=engine)
    # Idempotent migrations for all new columns
    with engine.connect() as conn:
        for stmt in _JOB_MIGRATIONS + _RESULT_MIGRATIONS:
            try:
                conn.execute(text(stmt))
                conn.commit()
            except Exception:
                pass  # Column already exists
