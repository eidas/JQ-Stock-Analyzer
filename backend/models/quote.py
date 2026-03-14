"""Daily quotes table (日次株価・出来高)."""

from datetime import date
from sqlalchemy import String, Integer, Float, Date, ForeignKey, UniqueConstraint, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.database import Base


class DailyQuote(Base):
    __tablename__ = "daily_quotes"
    __table_args__ = (
        UniqueConstraint("code", "date", name="uq_quotes_code_date"),
        Index("idx_quotes_code_date", "code", "date"),
        Index("idx_quotes_date", "date"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    code: Mapped[str] = mapped_column(String(4), ForeignKey("stocks.code"), nullable=False)
    date: Mapped[date] = mapped_column(Date, nullable=False, comment="取引日")
    open: Mapped[float | None] = mapped_column(Float, comment="始値（調整後）")
    high: Mapped[float | None] = mapped_column(Float, comment="高値（調整後）")
    low: Mapped[float | None] = mapped_column(Float, comment="安値（調整後）")
    close: Mapped[float | None] = mapped_column(Float, comment="終値（調整後）")
    volume: Mapped[int | None] = mapped_column(Integer, comment="出来高（調整後）")
    turnover_value: Mapped[float | None] = mapped_column(Float, comment="売買代金")
    adjustment_factor: Mapped[float | None] = mapped_column(Float, comment="調整係数")

    stock = relationship("Stock", back_populates="quotes")
