import asyncio
import aiohttp
import json
import sys

async def test_with_proper_request():
    # This is a properly formatted request with both original and target text
    test_data = {
        "original": {
            "username": "hiking_enthusiast", 
            "text": "Just wrapped up a sunset summit hike and the views were absolutely breathtaking! Nature's magic at its finest."
        },
        "target": {
            "username": "nature_lover", 
            "text": "That sounds amazing! Which trail did you take? I've been looking for new hiking spots."
        },
        "history": [
            {
                "username": "adventure_seeker",
                "text": "Summit hikes are the best! Did you see any wildlife?"
            }
        ]
    }
    
    print("\n--- Testing with properly formatted request ---")
    print(f"Original text: '{test_data['original']['text']}'")
    print(f"Target text: '{test_data['target']['text']}'")
    
    try:
        async with aiohttp.ClientSession() as session:
            # Make the request
            print("\nSending request to /generate-reply endpoint...")
            resp = await session.post(
                'http://localhost:8000/generate-reply',
                json=test_data
            )
            
            status = resp.status
            print(f"Response status: {status}")
            
            try:
                js = await resp.json()
                print(f"Response: {json.dumps(js, indent=2)}")
                
                # Check if we got a fallback or a real reply
                reply = js.get("reply", "")
                fallbacks = [
                    "Main-character energy ✨", "Love this vibe 😍", "Absolute fire 🔥",
                    "Gym goals! 💪", "Chef's kiss 😘", "Instant mood-boost 💯"
                ]
                
                if reply in fallbacks:
                    print("\n⚠️ WARNING: Received fallback reply!")
                else:
                    print("\n✅ Success! Received AI-generated reply.")
                    
            except json.JSONDecodeError:
                text = await resp.text()
                print(f"Non-JSON response: {text[:200]}...")
                
    except aiohttp.ClientError as e:
        print(f"Client error: {str(e)}")
    except asyncio.TimeoutError:
        print("Request timed out")
    except Exception as e:
        print(f"Unexpected error: {str(e)}")

if __name__ == "__main__":
    asyncio.run(test_with_proper_request()) 