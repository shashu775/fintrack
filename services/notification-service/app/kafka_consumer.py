import os
import json
import logging
import asyncio
from aiokafka import AIOKafkaConsumer

logger = logging.getLogger(__name__)

KAFKA_BOOTSTRAP_SERVERS = os.getenv(
    "KAFKA_BOOTSTRAP_SERVERS", "fintrack-kafka-bootstrap:9092"
)
TOPIC_TRANSACTION_CREATED = "transaction.created"
GROUP_ID = "notification-service"


async def consume_transactions():
    consumer = AIOKafkaConsumer(
        TOPIC_TRANSACTION_CREATED,
        bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
        group_id=GROUP_ID,
        value_deserializer=lambda v: json.loads(v.decode("utf-8")),
    )
    await consumer.start()
    logger.info("Notification consumer started")
    try:
        async for msg in consumer:
            await _send_notification(msg.value)
    finally:
        await consumer.stop()


async def _send_notification(event: dict):
    # Replace with a real email/SMS/push integration.
    # Kept as a log line here since this is a portfolio scaffold.
    logger.info(
        "Notify account=%s: transaction %s for %s %s",
        event["account_id"], event["id"], event["amount"], event["currency"],
    )


def start_consumer_task() -> asyncio.Task:
    return asyncio.create_task(consume_transactions())
