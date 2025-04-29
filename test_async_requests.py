import asyncio
import aiohttp
import json
import time
from typing import List, Dict
import random

# Test data
TEST_POSTS = [
    {
        "original": {
            "username": "user1",
            "text": "Just finished a 10K run and feeling amazing!"
        },
        "target": {
            "username": "user2",
            "text": "That's awesome! I'm training for a half marathon next month."
        },
        "history": [
            {
                "username": "user3",
                "text": "Great job! What was your time?"
            }
        ]
    },
    {
        "original": {
            "username": "foodie",
            "text": "Made the most delicious pasta carbonara tonight!"
        },
        "target": {
            "username": "chef",
            "text": "What's your secret ingredient?"
        },
        "history": []
    },
    {
        "original": {
            "username": "traveler",
            "text": "Just landed in Tokyo! Any must-visit spots?"
        },
        "target": {
            "username": "local",
            "text": "Welcome! You should definitely check out the Tsukiji fish market."
        },
        "history": [
            {
                "username": "tourist",
                "text": "Don't forget to try the sushi!"
            }
        ]
    }
]

async def make_request(session: aiohttp.ClientSession, data: Dict) -> Dict:
    """Make a single request to generate a reply."""
    try:
        # First, enqueue the task
        async with session.post(
            'http://localhost:8000/generate-reply',
            json=data
        ) as resp:
            if resp.status != 200:
                return {"error": f"Failed to enqueue: {resp.status}"}
            
            result = await resp.json()
            task_id = result.get("task_id")
            if not task_id:
                return {"error": "No task_id received"}
            
            # Now poll for the result
            for _ in range(10):  # Try up to 10 times
                async with session.get(
                    f'http://localhost:8000/generate-reply/{task_id}'
                ) as poll_resp:
                    if poll_resp.status != 200:
                        return {"error": f"Poll failed: {poll_resp.status}"}
                    
                    poll_result = await poll_resp.json()
                    if poll_result["status"] == "done":
                        return {
                            "success": True,
                            "reply": poll_result["reply"],
                            "task_id": task_id
                        }
                    elif poll_result["status"] == "failure":
                        return {"error": f"Task failed: {poll_result.get('error')}"}
                
                await asyncio.sleep(1)  # Wait 1 second between polls
            
            return {"error": "Timeout waiting for task completion"}
            
    except Exception as e:
        return {"error": str(e)}

async def test_concurrent_requests(num_requests: int = 5):
    """Test multiple concurrent requests."""
    print(f"\n=== Testing {num_requests} Concurrent Requests ===\n")
    
    start_time = time.time()
    async with aiohttp.ClientSession() as session:
        # Create tasks for concurrent execution
        tasks = [
            make_request(session, random.choice(TEST_POSTS))
            for _ in range(num_requests)
        ]
        
        # Run all tasks concurrently
        results = await asyncio.gather(*tasks)
    
    end_time = time.time()
    total_time = end_time - start_time
    
    # Analyze results
    successes = [r for r in results if r.get("success")]
    failures = [r for r in results if "error" in r]
    
    print(f"\nResults:")
    print(f"Total requests: {num_requests}")
    print(f"Successful: {len(successes)}")
    print(f"Failed: {len(failures)}")
    print(f"Total time: {total_time:.2f} seconds")
    print(f"Average time per request: {total_time/num_requests:.2f} seconds")
    
    if successes:
        print("\nSample successful replies:")
        for i, result in enumerate(successes[:3], 1):
            print(f"{i}. Task ID: {result['task_id']}")
            print(f"   Reply: {result['reply']}")
    
    if failures:
        print("\nSample failures:")
        for i, result in enumerate(failures[:3], 1):
            print(f"{i}. Error: {result['error']}")

if __name__ == "__main__":
    # Run the test with 5 concurrent requests
    asyncio.run(test_concurrent_requests(5)) 