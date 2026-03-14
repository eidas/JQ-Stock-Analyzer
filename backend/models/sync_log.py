"""Data sync log table (同期ログ)."""

from datetime import date, datetime
from sqlalchemy import String, Integer, Float, Date, DateTime, Text
from sqlalchemy.orm import Mapped, mapped_column

from backend.database import Base


class DataSyncLog(Base):
    __tablename__ = "data_sync_log"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    sync_type: Mapped[str | None] = mapped_column(String, comment="同期種別")
    target_date: Mapped[date | None] = mapped_column(Date, comment="対象日")
    records_count: Mapped[int | None] = mapped_column(Integer, comment="取得件数")
    status: Mapped[str | None] = mapped_column(String, comment="success / error / running")
    error_message: Mapped[str | None] = mapped_column(Text, comment="エラー詳細")
    progress_pct: Mapped[float | None] = mapped_column(Float, default=0.0, comment="進捗率（0.0〜100.0）")
    current_step: Mapped[str | None] = mapped_column(String, comment="現在の処理ステップ説明")
    started_at: Mapped[datetime | None] = mapped_column(DateTime, default=datetime.utcnow)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime)
