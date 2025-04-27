import asyncio
import json
import os
import aiohttp
from dotenv import load_dotenv

load_dotenv(override=True)

DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY")
DEEPSEEK_CHAT_URL = "https://api.deepseek.com/v1/chat/completions"
CHAT_MODEL = "deepseek-chat"

async def test_api_call():
    print(f"Using API key: {DEEPSEEK_API_KEY[:5]}...")
    print(f"API URL: {DEEPSEEK_CHAT_URL}")
    print(f"Model: {CHAT_MODEL}")
    
    try:
        async with aiohttp.ClientSession() as session:
            print("Sending request to DeepSeek API...")
            resp = await session.post(
                DEEPSEEK_CHAT_URL,
                headers={
                    "Authorization": f"Bearer {DEEPSEEK_API_KEY}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": CHAT_MODEL,
                    "messages": [
                        {"role": "system", "content": "You are a helpful assistant."},
                        {"role": "user", "content": "Say hello!"},
                    ],
                    "max_tokens": 100,
                    "temperature": 0.7,
                },
                timeout=60
            )
            
            status = resp.status
            print(f"Response status: {status}")
            
            # Try to parse response as JSON
            try:
                js = await resp.json()
                print(f"Response: {json.dumps(js, indent=2)}")
                
                if "choices" in js:
                    content = js["choices"][0]["message"]["content"]
                    print(f"Generated text: {content}")
                else:
                    print("No choices in response")
                    
            except json.JSONDecodeError:
                # If not JSON, read as text
                text = await resp.text()
                print(f"Non-JSON response: {text[:200]}...")
                
    except aiohttp.ClientError as e:
        print(f"Client error: {str(e)}")
    except asyncio.TimeoutError:
        print("Request timed out")
    except Exception as e:
        print(f"Unexpected error: {str(e)}")

if __name__ == "__main__":
    asyncio.run(test_api_call()) 