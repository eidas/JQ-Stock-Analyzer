"""Portfolio tables (ポートフォリオ + 構成銘柄)."""

from datetime import date, datetime
from sqlalchemy import String, Integer, Float, Date, DateTime, Text, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.database import Base


class Portfolio(Base):
    __tablename__ = "portfolios"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String, nullable=False, comment="ポートフォリオ名")
    description: Mapped[str | None] = mapped_column(Text, comment="メモ")
    created_at: Mapped[datetime | None] = mapped_column(DateTime, default=datetime.utcnow)

    items = relationship("PortfolioItem", back_populates="portfolio", cascade="all, delete-orphan")


class PortfolioItem(Base):
    __tablename__ = "portfolio_items"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    portfolio_id: Mapped[int] = mapped_column(Integer, ForeignKey("portfolios.id"), nullable=False)
    code: Mapped[str] = mapped_column(String(4), ForeignKey("stocks.code"), nullable=False)
    shares: Mapped[int | None] = mapped_column(Integer, comment="保有株数")
    avg_cost: Mapped[float | None] = mapped_column(Float, comment="平均取得単価")
    acquired_date: Mapped[date | None] = mapped_column(Date, comment="取得日")
    memo: Mapped[str | None] = mapped_column(Text, comment="メモ")

    portfolio = relationship("Portfolio", back_populates="items")
    stock = relationship("Stock")
