import aiohttp
from app.config import DEEPSEEK_API_KEY, DEEPSEEK_VISION_URL, VISION_MODEL

async def describe_image(url: str) -> str:
    """
    One-sentence caption via DeepSeek Vision.
    """
    if not (DEEPSEEK_API_KEY and url.startswith(("http://", "https://"))):
        return ""
    payload = {
        "model": VISION_MODEL,
        "messages": [{
            "role": "user",
            "content": [
                {"type": "text",
                 "text": "Describe this image in one concise sentence."},
                {"type": "image_url", "image_url": {"url": url}},
            ],
        }],
        "max_tokens": 60,
    }
    try:
        async with aiohttp.ClientSession() as s:
            r = await s.post(
                DEEPSEEK_VISION_URL,
                headers={
                    "Authorization": f"Bearer {DEEPSEEK_API_KEY}",
                    "Content-Type": "application/json",
                },
                json=payload, timeout=45
            )
            js = await r.json()
            return (js["choices"][0]["message"]["content"]
                      .strip().replace("\n", " "))[:200]
    except Exception:
        return ""
