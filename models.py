from datetime import date
from sqlalchemy import String, Integer, Float, Date
from sqlalchemy.orm import Mapped, mapped_column
from database import Base

class Sale(Base):
    __tablename__ = "sales"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    transaction_id: Mapped[str] = mapped_column(String, unique=True)
    sale_date: Mapped[date] = mapped_column(Date)
    city: Mapped[str] = mapped_column(String)
    branch: Mapped[str] = mapped_column(String)
    category: Mapped[str] = mapped_column(String)
    product: Mapped[str] = mapped_column(String)
    quantity: Mapped[int] = mapped_column(Integer)
    unit_price_ksh: Mapped[float] = mapped_column(Float)
    payment_method: Mapped[str] = mapped_column(String)