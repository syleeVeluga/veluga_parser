from datetime import datetime, timezone
from sqlalchemy import String, DateTime, Integer, Text, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column
from src.backend.database import Base


def _utcnow() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


class ParsedResult(Base):
    __tablename__ = "parsed_results"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    job_id: Mapped[str] = mapped_column(String(36), ForeignKey("jobs.id"), nullable=False, unique=True)
    schema_version: Mapped[str | None] = mapped_column(String(10), nullable=True, default="1.0")
    result_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    chunks_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    toc_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    structure_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    element_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    markdown_path: Mapped[str | None] = mapped_column(String(512), nullable=True)
    text_path: Mapped[str | None] = mapped_column(String(512), nullable=True)
    json_path: Mapped[str | None] = mapped_column(String(512), nullable=True)
    chunks_path: Mapped[str | None] = mapped_column(String(512), nullable=True)
    image_dir: Mapped[str | None] = mapped_column(String(512), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow)
