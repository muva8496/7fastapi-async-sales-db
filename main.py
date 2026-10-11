from datetime import date
from enum import Enum
from fastapi import FastAPI, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError, OperationalError

from database import engine, Base, get_session
from models import Sale

app = FastAPI(title="Vellamo Sales DB API")

class PaymentMethod(str, Enum):
    mpesa = "M-Pesa"
    cash = "Cash"
    card = "Card"

class SaleIn(BaseModel):
    transaction_id: str
    sale_date: date
    city: str
    branch: str
    category: str
    product: str
    quantity: int = Field(gt=0)
    unit_price_ksh: float = Field(gt=0)
    payment_method: PaymentMethod

@app.on_event("startup")
async def on_startup():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

@app.get("/health")
async def health():
    return {"status": "ok"}

@app.post("/sales", status_code=201)
async def create_sale(sale: SaleIn, session: AsyncSession = Depends(get_session)):
    new_sale = Sale(**sale.model_dump())
    session.add(new_sale)
    try:
        await session.commit()
    except IntegrityError:
        await session.rollback()
        raise HTTPException(
            status_code=409,
            detail=f"Sale with transaction_id '{sale.transaction_id}' already exists",
        )
    except OperationalError:
        await session.rollback()
        raise HTTPException(
            status_code=503,
            detail="Database temporarily error. Please try again later.",
        )

    await session.refresh(new_sale)
    return {"status": "saved", "id": new_sale.id, "transaction_id": new_sale.transaction_id}


@app.get("/sales")
async def list_sales(session: AsyncSession = Depends(get_session)):
    result = await session.execute(select(Sale))
    return result.scalars().all()