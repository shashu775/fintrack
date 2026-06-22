import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI

from . import models
from .database import engine
from .kafka_consumer import start_consumer_task

logging.basicConfig(level=logging.INFO)

models.Base.metadata.create_all(bind=engine)

consumer_task = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    global consumer_task
    consumer_task = start_consumer_task()
    yield
    if consumer_task:
        consumer_task.cancel()


app = FastAPI(title="Ledger Service", lifespan=lifespan)


@app.get("/health")
def health():
    return {"status": "ok"}
