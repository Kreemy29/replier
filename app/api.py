import logging
import json

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from celery.result import AsyncResult

from celery_app import celery_app
from app.celery_tasks import generate_reply_task
from app.services.reply import sanitize_log_message

logger = logging.getLogger(__name__)
router = APIRouter()

class ReplyRequest(BaseModel):
    original: dict
    target:   dict
    history:  list = []

@router.post("/generate-reply")
async def enqueue_reply(request: ReplyRequest):
    """
    Enqueue a reply job and return a task_id immediately.
    """
    logger.info("Enqueuing generate-reply task")
    safe = sanitize_log_message(request.dict())
    logger.debug("Sanitized request:\n%s", json.dumps(safe, indent=2))

    payload = {
        "original": request.original,
        "target":   request.target,
        "history":  request.history,
        "postId":   "system-generated"
    }

    task = generate_reply_task.delay(payload)
    return {"task_id": task.id}

@router.get("/generate-reply/{task_id}")
async def get_reply(task_id: str):
    """
    Poll for the status and result of a previously enqueued task.
    """
    res = AsyncResult(task_id, app=celery_app)
    state = res.state

    if state == "PENDING":
        return {"status": "pending"}
    if state == "SUCCESS":
        return {"status": "done", "reply": res.result}
    if state == "FAILURE":
        return {"status": "failure", "error": str(res.result)}

    # Covers states like RETRY
    return {"status": state}
