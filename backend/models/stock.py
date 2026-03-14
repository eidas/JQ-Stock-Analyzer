"""Stock master table (銘柄マスタ)."""

from datetime import datetime
from sqlalchemy import String, Boolean, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.database import Base


class Stock(Base):
    __tablename__ = "stocks"

    code: Mapped[str] = mapped_column(String(4), primary_key=True, comment="銘柄コード（4桁）")
    name: Mapped[str] = mapped_column(String, nullable=False, comment="銘柄名")
    sector_17: Mapped[str | None] = mapped_column(String, comment="17業種区分")
    sector_33: Mapped[str | None] = mapped_column(String, comment="33業種区分")
    market_segment: Mapped[str | None] = mapped_column(String, comment="市場区分（プライム等）")
    is_active: Mapped[bool | None] = mapped_column(Boolean, default=True, comment="上場中フラグ")
    updated_at: Mapped[datetime | None] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    quotes = relationship("DailyQuote", back_populates="stock", lazy="dynamic")
    financials = relationship("FinancialStatement", back_populates="stock", lazy="dynamic")
    metrics = relationship("CalculatedMetric", back_populates="stock", lazy="dynamic")
