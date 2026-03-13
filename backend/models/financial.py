"""Financial statements table (財務サマリー)."""

from datetime import date
from sqlalchemy import String, Integer, Float, Date, ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.database import Base


class FinancialStatement(Base):
    __tablename__ = "financial_statements"
    __table_args__ = (
        UniqueConstraint("code", "fiscal_year", "type_of_document", name="uq_fin_code_fy_doc"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    code: Mapped[str] = mapped_column(String(4), ForeignKey("stocks.code"), nullable=False)
    disclosed_date: Mapped[date | None] = mapped_column(Date, comment="開示日")
    fiscal_year: Mapped[str | None] = mapped_column(String, comment="決算期（YYYY-MM形式）")
    type_of_document: Mapped[str | None] = mapped_column(String, comment="書類種別")
    net_sales: Mapped[float | None] = mapped_column(Float, comment="売上高")
    operating_profit: Mapped[float | None] = mapped_column(Float, comment="営業利益")
    ordinary_profit: Mapped[float | None] = mapped_column(Float, comment="経常利益")
    net_income: Mapped[float | None] = mapped_column(Float, comment="純利益")
    eps: Mapped[float | None] = mapped_column(Float, comment="EPS")
    bps: Mapped[float | None] = mapped_column(Float, comment="BPS")
    total_assets: Mapped[float | None] = mapped_column(Float, comment="総資産")
    equity: Mapped[float | None] = mapped_column(Float, comment="自己資本")
    equity_ratio: Mapped[float | None] = mapped_column(Float, comment="自己資本比率")
    shares_outstanding: Mapped[int | None] = mapped_column(
        Integer, comment="発行済株式数（自己株式控除前）"
    )
    dividend_forecast: Mapped[float | None] = mapped_column(Float, comment="配当予想（年間）")
    forecast_net_sales: Mapped[float | None] = mapped_column(Float, comment="売上高予想（通期）")
    forecast_operating_profit: Mapped[float | None] = mapped_column(Float, comment="営業利益予想（通期）")
    forecast_ordinary_profit: Mapped[float | None] = mapped_column(Float, comment="経常利益予想（通期）")
    forecast_net_income: Mapped[float | None] = mapped_column(Float, comment="純利益予想（通期）")
    forecast_eps: Mapped[float | None] = mapped_column(Float, comment="EPS予想")
    forecast_dividend: Mapped[float | None] = mapped_column(Float, comment="配当予想（会社予想、年間）")

    stock = relationship("Stock", back_populates="financials")
