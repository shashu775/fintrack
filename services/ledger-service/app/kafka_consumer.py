import os
import json
import logging
import asyncio
from aiokafka import AIOKafkaConsumer
from sqlalchemy.orm import Session

from . import models
from .database import SessionLocal

logger = logging.getLogger(__name__)

KAFKA_BOOTSTRAP_SERVERS = os.getenv(
    "KAFKA_BOOTSTRAP_SERVERS", "fintrack-kafka-bootstrap:9092"
)
TOPIC_TRANSACTION_CREATED = "transaction.created"
GROUP_ID = "ledger-service"


async def consume_transactions():
    consumer = AIOKafkaConsumer(
        TOPIC_TRANSACTION_CREATED,
        bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
        group_id=GROUP_ID,
        value_deserializer=lambda v: json.loads(v.decode("utf-8")),
        enable_auto_commit=False,
    )
    await consumer.start()
    logger.info("Ledger consumer started, topic=%s", TOPIC_TRANSACTION_CREATED)
    try:
        async for msg in consumer:
            await _handle_message(msg.value)
            await consumer.commit()
    finally:
        await consumer.stop()


async def _handle_message(event: dict):
    # NOTE: idempotency check below guards against duplicate delivery,
    # which is a real possibility since enable_auto_commit is False
    # and we only commit *after* a successful write.
    db: Session = SessionLocal()
    try:
        existing = db.query(models.LedgerEntry).filter(
            models.LedgerEntry.transaction_id == event["id"]
        ).first()
        if existing:
            logger.info("Ledger entry already exists for txn=%s, skipping", event["id"])
            return

        entry = models.LedgerEntry(
            transaction_id=event["id"],
            account_id=event["account_id"],
            amount=event["amount"],
            currency=event["currency"],
        )
        db.add(entry)
        db.commit()
        logger.info("Posted ledger entry for txn=%s", event["id"])
    finally:
        db.close()


def start_consumer_task() -> asyncio.Task:
    return asyncio.create_task(consume_transactions())
