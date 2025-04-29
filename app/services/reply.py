import random
import asyncio
import json
import logging
import re
from typing import Dict, List, Optional

import aiohttp
from tenacity import retry, stop_after_attempt, wait_exponential

from app.config import (
    DEEPSEEK_API_KEY,
    DEEPSEEK_CHAT_URL,
    CHAT_MODEL,
    FALLBACK_COMMENTS,
    POSTED_COMMENTS,
)

# Get a logger for this module
logger = logging.getLogger(__name__)

def redact_api_key(text: str) -> str:
    """Redact API key from log messages."""
    if not DEEPSEEK_API_KEY or not text:
        return text
    return text.replace(DEEPSEEK_API_KEY, "SK-***REDACTED***")

def sanitize_log_message(obj):
    """Sanitize and redact sensitive information from log messages."""
    if isinstance(obj, str):
        return redact_api_key(obj)
    if isinstance(obj, dict):
        sanitized = {}
        for k, v in obj.items():
            if k.lower() == "authorization":
                sanitized[k] = "Bearer SK-***REDACTED***"
            else:
                sanitized[k] = sanitize_log_message(v)
        return sanitized
    if isinstance(obj, list):
        return [sanitize_log_message(item) for item in obj]
    return obj

def clean_reply(text: str) -> Optional[str]:
    """
    Clean the reply text to remove any references to DeepSeek, AI assistants,
    or other unwanted patterns.
    """
    if not text:
        return None

    patterns = [
        (r'(?i)deepseek', ''), (r'(?i)deep\s*seek', ''), (r'(?i)deep-seek', ''),
        (r'(?i)as\s*an?\s*ai', ''), (r'(?i)i\'m\s*an?\s*ai', ''), (r'(?i)ai\s*assistant', ''),
        (r'(?i)ai\s*model', ''), (r'(?i)language\s*model', ''), (r'(?i)llm', ''),
        (r'(?i)gpt', ''), (r'(?i)artificial\s*intelligence', ''),
        (r'(?i)i\s*don\'?t\s*have\s*personal', ''), (r'(?i)i\s*cannot', ''),
        (r'(?i)i\'m\s*not\s*able\s*to', ''), (r'(?i)i\s*don\'?t\s*have\s*access\s*to', ''),
        (r'(?i)i\s*don\'?t\s*have\s*the\s*ability', ''), (r'(?i)as\s*a[n]?\s*language\s*model', ''),
        (r'(?i)assistant[:\s]', ''), (r'(?i)system[:\s]', ''), (r'(?i)ai[:\s]', ''),
        (r'^[\'"]', ''), (r'[\'"]$', ''), (r'(?i)the\s*ai', 'it'),
        (r'(?i)\bai\b', ''), (r'(?i)powered\s*by', 'made with'),
        (r'(?i)technology', 'tech'), (r'(?i)trained\s*on', 'based on'),
        (r'(?i)generate\s*responses', 'create replies'), (r'(?i)chatbot', 'app'),
    ]

    cleaned = text
    for pattern, repl in patterns:
        cleaned = re.sub(pattern, repl, cleaned)

    cleaned = re.sub(r'\s+', ' ', cleaned).strip()
    if re.match(r'^I\s+(?!\')', cleaned, re.IGNORECASE):
        cleaned = re.sub(r'^I\s+', '', cleaned, flags=re.IGNORECASE)

    # Final guard: if it dropped to too few chars, fallback
    if len(cleaned) < 5:
        return None
    return cleaned

@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
async def make_reply(p: Dict) -> str:
    """
    Generate a reply using DeepSeek-Chat API or fallback to predefined comments.
    Expects keys: original, target, history, postId.
    """
    logger.debug(f"Starting make_reply (postId={p.get('postId')})")

    try:
        orig = p.get("original", {}).get("text", "")
        targ = p.get("target", {}).get("text", "")
        if not orig or not targ:
            logger.warning("Missing original or target text → falling back")
            return random.choice(FALLBACK_COMMENTS)

        # Build the prompt
        prompt = (
            f'THREAD by @{p["original"].get("username","unknown")} (ID {p.get("postId","0")}):\n'
            f'  Text: "{orig}"\n\n'
            f'TARGET by @{p["target"]["username"]}: "{targ}"\n\n'
        )
        hist = p.get("history", [])[:3]
        if hist:
            prompt += "OTHER REPLIES:\n"
            for h in hist:
                prompt += f'  @{h["username"]}: "{h["text"]}"\n'
            prompt += "\n"
        prompt += (
            "INSTRUCTIONS:\n"
            "Write ONE casual reply (≤12 words) that addresses "
            f"@{p['target']['username']}, adds a fresh perspective, "
            "and includes exactly ONE emoji.\n"
            "IMPORTANT: Output ONLY the reply text. "
            "DO NOT mention being an AI or any model names."
        )

        sys_prompt = (
            "You are Ava, a witty 20-something woman replying on Threads. "
            "Never reveal you are an AI or mention AI capabilities."
        )

        if not DEEPSEEK_API_KEY:
            logger.error("No DEEPSEEK_API_KEY → falling back")
            return random.choice(FALLBACK_COMMENTS)

        async with aiohttp.ClientSession() as session:
            resp = await session.post(
                DEEPSEEK_CHAT_URL,
                headers={
                    "Authorization": f"Bearer {DEEPSEEK_API_KEY}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": CHAT_MODEL,
                    "messages": [
                        {"role": "system",  "content": sys_prompt},
                        {"role": "user",    "content": prompt},
                    ],
                    "max_tokens": 100,
                    "temperature": 0.7,
                    "top_p": 0.9,
                    "frequency_penalty": 0.5,
                    "presence_penalty": 0.5,
                },
                timeout=60,
            )
            
            if resp.status != 200:
                logger.error(f"DeepSeek API error: {resp.status} {await resp.text()}")
                return random.choice(FALLBACK_COMMENTS)
                
            js = await resp.json()
            
        # Parse & clean
        choices = js.get("choices", [])
        if not choices:
            logger.warning("Empty choices → falling back")
            return random.choice(FALLBACK_COMMENTS)

        raw = choices[0].get("message", {}).get("content", "").strip().strip('"\'')
        cleaned = clean_reply(raw) or random.choice(FALLBACK_COMMENTS)

        # Ensure one emoji
        if not any(ord(c) > 127 for c in cleaned):
            cleaned += " " + random.choice(["✨", "🔥", "🙌", "👍", "😊", "💯", "🌟", "❤️"])

        # De-dup
        if cleaned in POSTED_COMMENTS.values():
            cleaned += random.choice([" ✨", " 🔥", " 🙌"])
        POSTED_COMMENTS[p["postId"]] = cleaned

        return cleaned[:80]
        
    except asyncio.TimeoutError:
        logger.error("DeepSeek API timeout → falling back")
        return random.choice(FALLBACK_COMMENTS)
    except Exception as e:
        logger.error(f"Unexpected error in make_reply: {str(e)}")
        return random.choice(FALLBACK_COMMENTS)

# Note: The Celery task registration is moved to a separate file to avoid circular imports
