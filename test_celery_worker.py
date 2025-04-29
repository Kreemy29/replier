import asyncio
import time
from celery import Celery
from celery.result import AsyncResult
from app.tasks import generate_reply_task

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
        ],
        "postId": "test-1"
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
        "history": [],
        "postId": "test-2"
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
        ],
        "postId": "test-3"
    }
]

def test_celery_worker(num_tasks: int = 5):
    """Test Celery worker with multiple concurrent tasks."""
    print(f"\n=== Testing Celery Worker with {num_tasks} Concurrent Tasks ===\n")
    
    start_time = time.time()
    
    # Submit tasks
    tasks = []
    for i in range(num_tasks):
        task = generate_reply_task.delay(TEST_POSTS[i % len(TEST_POSTS)])
        tasks.append(task)
        print(f"Submitted task {i+1} with ID: {task.id}")
    
    # Wait for all tasks to complete
    results = []
    for i, task in enumerate(tasks, 1):
        try:
            result = task.get(timeout=30)  # Wait up to 30 seconds per task
            results.append({"success": True, "reply": result, "task_id": task.id})
            print(f"Task {i} completed successfully")
        except Exception as e:
            results.append({"error": str(e), "task_id": task.id})
            print(f"Task {i} failed: {str(e)}")
    
    end_time = time.time()
    total_time = end_time - start_time
    
    # Analyze results
    successes = [r for r in results if r.get("success")]
    failures = [r for r in results if "error" in r]
    
    print(f"\nResults:")
    print(f"Total tasks: {num_tasks}")
    print(f"Successful: {len(successes)}")
    print(f"Failed: {len(failures)}")
    print(f"Total time: {total_time:.2f} seconds")
    print(f"Average time per task: {total_time/num_tasks:.2f} seconds")
    
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
    test_celery_worker(5) 