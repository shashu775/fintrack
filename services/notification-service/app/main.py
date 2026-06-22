import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI

from .kafka_consumer import start_consumer_task

logging.basicConfig(level=logging.INFO)

consumer_task = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    global consumer_task
    consumer_task = start_consumer_task()
    yield
    if consumer_task:
        consumer_task.cancel()


app = FastAPI(title="Notification Service", lifespan=lifespan)


@app.get("/health")
def health():
    return {"status": "ok"}
