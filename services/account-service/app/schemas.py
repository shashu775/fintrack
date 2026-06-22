import uuid
from decimal import Decimal
from pydantic import BaseModel, EmailStr


class AccountCreate(BaseModel):
    owner_email: EmailStr


class AccountOut(BaseModel):
    id: uuid.UUID
    owner_email: str
    balance: Decimal

    class Config:
        from_attributes = True
