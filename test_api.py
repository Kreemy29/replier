import requests
import time
import json
from typing import Dict, Optional

def test_api() -> None:
    """Test the API endpoints."""
    print("\n=== Testing Reply Generation API ===\n")
    
    # Test data
    test_data = {
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
    }
    
    # Step 1: Submit a task
    print("1. Submitting task...")
    try:
        response = requests.post(
            "http://localhost:8000/generate-reply",
            json=test_data,
            headers={"Content-Type": "application/json"}
        )
        response.raise_for_status()
        task_id = response.json()["task_id"]
        print(f"Task ID: {task_id}")
    except requests.exceptions.RequestException as e:
        print(f"Error submitting task: {e}")
        return
    
    # Step 2: Poll for results
    print("\n2. Polling for results...")
    max_retries = 10
    retry_count = 0
    
    while retry_count < max_retries:
        try:
            response = requests.get(f"http://localhost:8000/generate-reply/{task_id}")
            response.raise_for_status()
            result = response.json()
            
            status = result["status"]
            print(f"Attempt {retry_count + 1}: Status = {status}")
            
            if status == "done":
                print("\nSuccess!")
                print(f"Reply: {result['reply']}")
                return
            elif status == "failure":
                print(f"\nTask failed: {result.get('error', 'Unknown error')}")
                return
            
            time.sleep(2)
            retry_count += 1
            
        except requests.exceptions.RequestException as e:
            print(f"Error polling task: {e}")
            return
    
    print("\nTimeout waiting for task completion")

if __name__ == "__main__":
    test_api() 