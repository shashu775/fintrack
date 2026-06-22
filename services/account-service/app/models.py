import uuid
from sqlalchemy import Column, String, Numeric
from sqlalchemy.dialects.postgresql import UUID
from .database import Base


class Account(Base):
    __tablename__ = "accounts"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    owner_email = Column(String(255), nullable=False, unique=True, index=True)
    balance = Column(Numeric(12, 2), nullable=False, default=0)
