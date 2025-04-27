import asyncio
from app.services.reply import make_reply

async def test_reply_service():
    test_post = {
        "postId": "test-123",
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
    
    print("Testing reply service...")
    reply = await make_reply(test_post)
    print(f"Final reply: {reply}")
    print("Is this a fallback reply?", reply in ["Main-character energy ✨", "Love this vibe 😍", "Absolute fire 🔥", 
                                                "Gym goals! 💪", "Chef's kiss 😘", "Instant mood-boost 💯"])

if __name__ == "__main__":
    asyncio.run(test_reply_service()) 