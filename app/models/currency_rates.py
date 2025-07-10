from sqlalchemy import Column, Integer, String, Numeric, Date, DateTime, func
from app.db.database import Base

class CurrencyRates(Base):
    __tablename__ = "currency_rates"

    id = Column(Integer, primary_key=True, autoincrement=True)
    base_currency = Column(String(3), nullable=False)
    target_currency = Column(String(3), nullable=False)
    rate = Column(Numeric(15), nullable=False)
    rate_date = Column(Date, nullable=False)
    created_at = Column(DateTime, server_default=func.now(), nullable=True) 