import os
from dotenv import load_dotenv

load_dotenv(override=True)  # Force reload environment variables

# Validate API configuration
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY")
if not DEEPSEEK_API_KEY:
    raise ValueError("DEEPSEEK_API_KEY must be set in .env file")
DEEPSEEK_CHAT_URL   = "https://api.deepseek.com/v1/chat/completions"
DEEPSEEK_VISION_URL = "https://api.deepseek.com/v1/chat/completions"

CHAT_MODEL   = "deepseek-chat"
VISION_MODEL = "deepseek-vision"

FALLBACK_COMMENTS = [
    "Main-character energy ✨", "Love this vibe 😍", "Absolute fire 🔥",
    "Gym goals! 💪", "Chef's kiss 😘", "Instant mood-boost 💯"
]

EVENT_FALLBACK_COMMENTS = [
    # ... same as before ...
]

# session-level duplicate prevention
POSTED_COMMENTS = {}
