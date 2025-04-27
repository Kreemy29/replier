import logging
import json
from fastapi import APIRouter, HTTPException
from app.services.reply import make_reply, sanitize_log_message
from pydantic import BaseModel

# Get a logger for this module
logger = logging.getLogger(__name__)

router = APIRouter()

class ReplyRequest(BaseModel):
    original: dict
    target: dict
    history: list = []

@router.post("/generate-reply")
async def generate_reply(request: ReplyRequest):
    logger.info("Received generate-reply request")
    try:
        # Log the entire request for debugging, but sanitize it first
        safe_request = sanitize_log_message(request.dict())
        logger.debug(f"Request data (sanitized): {json.dumps(safe_request, indent=2)}")
        
        # Check if text fields exist and have content
        orig_text = request.original.get('text', '')
        target_text = request.target.get('text', '')
        
        logger.debug(f"Original text length: {len(orig_text)}")
        logger.debug(f"Target text length: {len(target_text)}")
        
        if not orig_text:
            logger.warning("Original text is empty!")
        if not target_text:
            logger.warning("Target text is empty!")
        
        reply = await make_reply({
            "original": request.original,
            "target": request.target,
            "history": request.history,
            "postId": "system-generated"
        })
        
        # Log a truncated version of the reply
        if reply:
            logger.info(f"Generated reply (truncated): '{reply[:15]}...'")
        else:
            logger.warning("Empty reply generated")
            
        return {"reply": reply}
    except Exception as e:
        logger.error(f"Error generating reply: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
