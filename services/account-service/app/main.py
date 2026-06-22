import uuid
import logging
from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session

from . import models, schemas
from .database import engine, get_db

logging.basicConfig(level=logging.INFO)

models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="Account Service")


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/accounts", response_model=schemas.AccountOut, status_code=201)
def create_account(payload: schemas.AccountCreate, db: Session = Depends(get_db)):
    account = models.Account(id=uuid.uuid4(), owner_email=payload.owner_email)
    db.add(account)
    db.commit()
    db.refresh(account)
    return account


@app.get("/accounts/{account_id}", response_model=schemas.AccountOut)
def get_account(account_id: uuid.UUID, db: Session = Depends(get_db)):
    account = db.query(models.Account).filter(models.Account.id == account_id).first()
    if not account:
        raise HTTPException(status_code=404, detail="Account not found")
    return account
