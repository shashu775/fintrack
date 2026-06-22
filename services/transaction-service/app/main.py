import uuid
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session

from . import models, schemas
from .database import engine, get_db
from .kafka_producer import publish_transaction_created, stop_producer

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

models.Base.metadata.create_all(bind=engine)


@asynccontextmanager
async def lifespan(app: FastAPI):
    yield
    await stop_producer()


app = FastAPI(title="Transaction Service", lifespan=lifespan)


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/transactions", response_model=schemas.TransactionOut, status_code=201)
async def create_transaction(payload: schemas.TransactionCreate, db: Session = Depends(get_db)):
    txn = models.Transaction(
        id=uuid.uuid4(),
        account_id=payload.account_id,
        amount=payload.amount,
        currency=payload.currency,
        status="pending",
    )
    db.add(txn)
    db.commit()
    db.refresh(txn)

    await publish_transaction_created({
        "id": str(txn.id),
        "account_id": str(txn.account_id),
        "amount": str(txn.amount),
        "currency": txn.currency,
        "status": txn.status,
    })

    return txn


@app.get("/transactions/{transaction_id}", response_model=schemas.TransactionOut)
def get_transaction(transaction_id: uuid.UUID, db: Session = Depends(get_db)):
    txn = db.query(models.Transaction).filter(models.Transaction.id == transaction_id).first()
    if not txn:
        raise HTTPException(status_code=404, detail="Transaction not found")
    return txn
