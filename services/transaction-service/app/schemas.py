import uuid
from decimal import Decimal
from pydantic import BaseModel


class TransactionCreate(BaseModel):
    account_id: uuid.UUID
    amount: Decimal
    currency: str = "USD"


class TransactionOut(BaseModel):
    id: uuid.UUID
    account_id: uuid.UUID
    amount: Decimal
    currency: str
    status: str

    class Config:
        from_attributes = True
