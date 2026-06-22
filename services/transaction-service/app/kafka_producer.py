import os
import json
import logging
from typing import Optional
from aiokafka import AIOKafkaProducer

logger = logging.getLogger(__name__)

KAFKA_BOOTSTRAP_SERVERS = os.getenv(
    "KAFKA_BOOTSTRAP_SERVERS", "fintrack-kafka-bootstrap:9092"
)
TOPIC_TRANSACTION_CREATED = "transaction.created"

_producer: Optional[AIOKafkaProducer] = None


async def get_producer() -> AIOKafkaProducer:
    global _producer
    if _producer is None:
        _producer = AIOKafkaProducer(
            bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
            value_serializer=lambda v: json.dumps(v).encode("utf-8"),
        )
        await _producer.start()
        logger.info("Kafka producer started, brokers=%s", KAFKA_BOOTSTRAP_SERVERS)
    return _producer


async def stop_producer():
    global _producer
    if _producer is not None:
        await _producer.stop()
        _producer = None


async def publish_transaction_created(transaction: dict):
    producer = await get_producer()
    await producer.send_and_wait(
        TOPIC_TRANSACTION_CREATED,
        key=str(transaction["account_id"]).encode("utf-8"),
        value=transaction,
    )
    logger.info("Published transaction.created event id=%s", transaction["id"])
