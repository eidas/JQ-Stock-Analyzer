"""Screening presets table (スクリーニング条件保存)."""

from datetime import datetime
from sqlalchemy import String, Integer, Text, DateTime
from sqlalchemy.orm import Mapped, mapped_column

from backend.database import Base


class ScreeningPreset(Base):
    __tablename__ = "screening_presets"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String, nullable=False, comment="プリセット名")
    conditions_json: Mapped[str | None] = mapped_column(Text, comment="条件JSON")
    created_at: Mapped[datetime | None] = mapped_column(DateTime, default=datetime.utcnow)
