import asyncio
import aiohttp
import json

async def test_api_endpoint():
    test_data = {
        "original": {
            "username": "test_user", 
            "text": "Just finished a 10K run and feeling amazing!"
        },
        "target": {
            "username": "fitness_fanatic", 
            "text": "That's awesome! I'm training for a half marathon next month."
        },
        "history": [
            {
                "username": "runner123",
                "text": "Great job! What was your time?"
            }
        ]
    }
    
    print("Testing API endpoint...")
    
    try:
        async with aiohttp.ClientSession() as session:
            # First ensure server is running on port 8000
            try:
                check_resp = await session.get('http://localhost:8000', timeout=2)
                print(f"Server status: {check_resp.status}")
            except Exception as e:
                print(f"Server check failed: {e}")
                print("Ensure server is running with 'uvicorn app.main:app --reload'")
                return
                
            # Make the actual request
            print("Sending request to /generate-reply endpoint...")
            resp = await session.post(
                'http://localhost:8000/generate-reply',
                json=test_data
            )
            
            status = resp.status
            print(f"Response status: {status}")
            
            try:
                js = await resp.json()
                print(f"Response: {json.dumps(js, indent=2)}")
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
    asyncio.run(test_api_endpoint()) 