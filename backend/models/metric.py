"""Calculated metrics cache table (算出指標キャッシュ)."""

from datetime import date
from sqlalchemy import String, Integer, Float, Date, ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.database import Base


class CalculatedMetric(Base):
    __tablename__ = "calculated_metrics"
    __table_args__ = (
        UniqueConstraint("code", "date", name="uq_metrics_code_date"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    code: Mapped[str] = mapped_column(String(4), ForeignKey("stocks.code"), nullable=False)
    date: Mapped[date] = mapped_column(Date, nullable=False, comment="計算基準日")
    per: Mapped[float | None] = mapped_column(Float, comment="PER（株価÷EPS）")
    pbr: Mapped[float | None] = mapped_column(Float, comment="PBR（株価÷BPS）")
    roe: Mapped[float | None] = mapped_column(Float, comment="ROE（純利益÷自己資本）")
    dividend_yield: Mapped[float | None] = mapped_column(Float, comment="配当利回り")
    market_cap: Mapped[float | None] = mapped_column(Float, comment="時価総額")
    turnover_days: Mapped[float | None] = mapped_column(Float, comment="回転日数")
    avg_volume_20d: Mapped[float | None] = mapped_column(Float, comment="20日平均出来高")
    avg_volume_60d: Mapped[float | None] = mapped_column(Float, comment="60日平均出来高")
    volatility_20d: Mapped[float | None] = mapped_column(Float, comment="20日ヒストリカルVol")
    operating_margin: Mapped[float | None] = mapped_column(Float, comment="営業利益率")
    ordinary_margin: Mapped[float | None] = mapped_column(Float, comment="経常利益率")
    ytd_return: Mapped[float | None] = mapped_column(Float, comment="年初来騰落率")

    stock = relationship("Stock", back_populates="metrics")
