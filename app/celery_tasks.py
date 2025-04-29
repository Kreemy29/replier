import asyncio
from celery_app import celery_app
from app.services.reply import make_reply

@celery_app.task(name="generate_reply")
def generate_reply_task(payload: dict) -> str:
    """
    Celery wrapper around the async make_reply.
    Runs in a separate worker process.
    """
    return asyncio.run(make_reply(payload)) 