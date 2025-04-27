import random
import asyncio
import json
import logging
import re
from typing import Dict, List
import aiohttp
from tenacity import retry, stop_after_attempt, wait_exponential
from app.config import (
    DEEPSEEK_API_KEY, DEEPSEEK_CHAT_URL,
    CHAT_MODEL, FALLBACK_COMMENTS, POSTED_COMMENTS
)

# Get a logger for this module
logger = logging.getLogger(__name__)

def redact_api_key(text):
    """Redact API key from log messages"""
    if not DEEPSEEK_API_KEY or not text:
        return text
    # Redact the API key if present in the text
    return text.replace(DEEPSEEK_API_KEY, "SK-***REDACTED***")

def sanitize_log_message(obj):
    """Sanitize and redact sensitive information from log messages"""
    if isinstance(obj, str):
        return redact_api_key(obj)
    elif isinstance(obj, dict):
        # For dictionaries, recursively sanitize values
        sanitized = {}
        for k, v in obj.items():
            # Skip logging authorization headers
            if k.lower() == "authorization":
                sanitized[k] = "Bearer SK-***REDACTED***"
            else:
                sanitized[k] = sanitize_log_message(v)
        return sanitized
    elif isinstance(obj, list):
        # For lists, recursively sanitize items
        return [sanitize_log_message(item) for item in obj]
    else:
        # Other types pass through unchanged
        return obj

def clean_reply(text: str) -> str:
    """
    Clean the reply text to remove any references to DeepSeek, AI assistants,
    or other unwanted patterns.
    """
    if not text:
        return text
        
    # List of patterns to remove or replace
    patterns = [
        # Remove DeepSeek mentions (case insensitive)
        (r'(?i)deepseek', ''),
        (r'(?i)deep\s*seek', ''),
        (r'(?i)deep-seek', ''),
        
        # Remove references to being an AI (case insensitive)
        (r'(?i)as\s*an?\s*AI', ''),
        (r'(?i)I\'m\s*an?\s*AI', ''),
        (r'(?i)AI\s*assistant', ''),
        (r'(?i)AI\s*model', ''),
        (r'(?i)language\s*model', ''),
        (r'(?i)LLM', ''),
        (r'(?i)GPT', ''),
        (r'(?i)chat\s*GPT', ''),
        (r'(?i)artificial\s*intelligence', ''),
        
        # Remove common AI-like phrases
        (r'(?i)I\s*don\'?t\s*have\s*personal', ''),
        (r'(?i)I\s*cannot', ''),
        (r'(?i)I\'m\s*not\s*able\s*to', ''),
        (r'(?i)I\s*don\'?t\s*have\s*access\s*to', ''),
        (r'(?i)I\s*don\'?t\s*have\s*the\s*ability', ''),
        (r'(?i)As\s*a[n]?\s*language\s*model', ''),
        (r'(?i)As\s*a[n]?\s*text-based', ''),
        (r'(?i)I\s*don\'?t\s*have\s*physical', ''),
        
        # Remove any role prefixes at start of text
        (r'(?i)^assistant[:\s]', ''),
        (r'(?i)^user[:\s]', ''),
        (r'(?i)^system[:\s]', ''),
        (r'(?i)^AI[:\s]', ''),
        
        # Remove role markers anywhere in text (not just at start)
        (r'(?i)(?<=\s)assistant[:\s]', ' '),
        (r'(?i)(?<=\s)user[:\s]', ' '),
        (r'(?i)(?<=\W)AI[:\s]', ' '),
        
        # Remove quotation marks that might be part of the format
        (r'^[\'"]', ''),
        (r'[\'"]$', ''),
        
        # Replace "the AI" references
        (r'(?i)the\s*AI', 'it'),
        
        # Remove the word AI on its own (with word boundaries)
        (r'(?i)\bAI\b', ''),
        
        # Technology-related terms that might leak AI mentions
        (r'(?i)powered\s*by', 'made with'),
        (r'(?i)technology', 'tech'),
        (r'(?i)trained\s*on', 'based on'),
        (r'(?i)generate\s*responses', 'create replies'),
        (r'(?i)chatbot', 'app'),
        
        # Remove standalone "AI" even when part of other words (careful)
        (r'(?i)(\w*)ai(\w*)', lambda m: m.group(1) + m.group(2) if m.group(0).lower() in ['ai', 'ais'] else m.group(0))
    ]
    
    # Apply each pattern
    cleaned = text
    for pattern, replacement in patterns:
        if callable(replacement):
            cleaned = re.sub(pattern, replacement, cleaned)
        else:
            cleaned = re.sub(pattern, replacement, cleaned)
    
    # Cleanup any artifacts from the replacements
    cleaned = re.sub(r'\s+', ' ', cleaned)  # Replace multiple spaces with single space
    cleaned = cleaned.strip()
    
    # If the first word is "I", and it's not followed by "'m" or "'ll" or similar,
    # consider replacing it with a more direct phrase
    if re.match(r'^I\s+(?!\')', cleaned, re.IGNORECASE):
        cleaned = re.sub(r'^I\s+', '', cleaned, flags=re.IGNORECASE)
    
    # Final check for any remaining "AI" text
    if "ai" in cleaned.lower() and len(cleaned) > 5:
        cleaned = cleaned.lower().replace("ai", "")
        cleaned = cleaned.strip()
    
    # If after cleaning, the text is too short, return None to trigger fallback
    if len(cleaned) < 5:
        return None
        
    return cleaned

@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
async def make_reply(p: Dict) -> str:
    """
    Generate a reply using DeepSeek-Chat API or fallback to predefined comments.
    """
    logger.debug(f"Starting make_reply with postId: {p.get('postId', 'unknown')}")
    
    # Validate input
    original_text = p.get("original", {}).get("text", "")
    target_text = p.get("target", {}).get("text", "")
    logger.debug(f"Original text: '{original_text[:30]}...'")
    logger.debug(f"Target text: '{target_text[:30]}...'")
    
    if not original_text or not target_text:
        logger.warning("Missing original or target text - falling back")
        return random.choice(FALLBACK_COMMENTS)

    # Build the user prompt with explicit instruction to not mention being AI
    u = (
        f'THREAD by @{p["original"].get("username", "unknown")} (ID {p.get("postId", "000")}):\n'
        f'  Text: "{original_text}"\n\n'
        f'TARGET by @{p["target"]["username"]}: "{target_text}"\n\n'
    )

    # Include up to 3 recent replies
    history: List[Dict] = p.get("history", [])[:3]
    if history:
        u += "OTHER REPLIES:\n"
        for h in history:
            u += f'  @{h["username"]}: "{h["text"]}"\n'
        u += "\n"

    u += (
        "INSTRUCTIONS:\n"
        "Write ONE casual reply (≤12 words) that addresses "
        f"@{p['target']['username']}, adds a fresh perspective, "
        "and includes exactly ONE emoji.\n"
        "IMPORTANT: Output ONLY the reply text. DO NOT mention being an AI or include any references to AI, language models, or DeepSeek."
    )
    
    logger.debug(f"Prompt built: {len(u)} characters")
    
    sys_prompt = "You are Ava, a witty 20-something woman replying on Threads. Never reveal you are an AI or mention AI capabilities."

    # Fallback if API key is missing
    if not DEEPSEEK_API_KEY:
        logger.error("Missing DEEPSEEK_API_KEY - falling back")
        return random.choice(FALLBACK_COMMENTS)

    try:
        logger.debug("Starting API request...")
        async with aiohttp.ClientSession() as session:
            logger.debug(f"Sending request to DeepSeek API")
            resp = await session.post(
                DEEPSEEK_CHAT_URL,
                headers={
                    "Authorization": f"Bearer {DEEPSEEK_API_KEY}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": CHAT_MODEL,
                    "messages": [
                        {"role": "system", "content": sys_prompt},
                        {"role": "user", "content": u},
                    ],
                    "max_tokens": 100,
                    "temperature": 0.7,
                    "top_p": 0.9,
                    "frequency_penalty": 0.5,
                    "presence_penalty": 0.5,
                },
                timeout=60
            )
            logger.debug(f"API response status: {resp.status}")
            js = await resp.json()

        # Validate API response
        if not js.get("choices"):
            logger.warning("No choices in API response - falling back")
            return random.choice(FALLBACK_COMMENTS)

        first_choice = js["choices"][0]
        reply = first_choice.get("message", {}).get("content", "").strip().strip('"\'')
        logger.debug(f"Raw reply received (length: {len(reply)})")
        
        # Clean the reply to remove any unwanted content
        cleaned_reply = clean_reply(reply)
        if not cleaned_reply:
            logger.warning("Reply was empty after cleaning - falling back")
            return random.choice(FALLBACK_COMMENTS)
            
        logger.debug(f"Cleaned reply: '{cleaned_reply}'")

        # Additional check for too-long replies
        words = cleaned_reply.split()
        if len(words) > 15:  # If more than 15 words, truncate
            cleaned_reply = " ".join(words[:12]) + " " + "".join([c for c in cleaned_reply if ord(c) > 127][:1] or "✨")
            logger.debug(f"Truncated long reply: '{cleaned_reply}'")

        # Ensure there's exactly one emoji
        emojis = [c for c in cleaned_reply if ord(c) > 127]
        if not emojis:  # No emoji found, add one
            cleaned_reply += " " + random.choice(["✨", "🔥", "🙌", "👍", "😊", "💯", "🌟", "❤️"])
            logger.debug(f"Added missing emoji: '{cleaned_reply}'")

        # Prevent duplicate replies
        if cleaned_reply in POSTED_COMMENTS.values():
            logger.debug("Duplicate reply detected - adding emoji")
            cleaned_reply += random.choice([" ✨", " 🔥", " 🙌"])
        POSTED_COMMENTS[p["postId"]] = cleaned_reply

        final_reply = " ".join(cleaned_reply.split())[:80]
        logger.debug(f"Final reply: '{final_reply}'")
        return final_reply

    except (aiohttp.ClientError, asyncio.TimeoutError) as e:
        logger.error(f"Network error: {str(e)}")
    except (KeyError, json.JSONDecodeError) as e:
        logger.error(f"Response parsing error: {str(e)}")
    except Exception as e:
        logger.exception(f"Unexpected error: {str(e)}")

    # Fallback in case of any exception
    logger.warning("Exception occurred - falling back")
    return random.choice(FALLBACK_COMMENTS)