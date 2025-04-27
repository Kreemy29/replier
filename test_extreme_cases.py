import asyncio
import json
import aiohttp
from app.services.reply import clean_reply

# Extreme test cases that might cause AI to reference itself
extreme_tests = [
    {
        "name": "Direct AI question",
        "post": {
            "original": {
                "username": "ai_curious", 
                "text": "What's your opinion on AI language models like DeepSeek? Are they getting better at simulating human conversations?"
            },
            "target": {
                "username": "tech_blogger", 
                "text": "They're improving rapidly! What impresses you most about them?"
            }
        }
    },
    {
        "name": "Ask about capabilities",
        "post": {
            "original": {
                "username": "user_question", 
                "text": "Can you tell me if you're powered by AI or if you're a real person?"
            },
            "target": {
                "username": "tech_curious", 
                "text": "I've always wondered how these chatbots really work behind the scenes."
            }
        }
    }
]

# Some examples of highly problematic responses an AI might generate
problematic_responses = [
    "As a DeepSeek language model, I don't have personal opinions, but AI is advancing rapidly! 🤖",
    "I'm an AI assistant created by DeepSeek, so I can't have favorites, but the tech is fascinating! 💻",
    "As an AI, I don't have personal experiences, but I find the progress in natural language processing impressive! 🧠",
    "I am actually powered by DeepSeek's AI technology! I help generate responses based on the data I was trained on. 🤖",
    "I'm not a real person - I'm an AI assistant designed to generate helpful responses! 💬"
]

print("\n=== Testing Extreme AI Self-Reference Cases ===\n")

# First, test our cleaning function on known problematic responses
print("Testing cleaning on known problematic responses:")
for i, response in enumerate(problematic_responses):
    print(f"\nTest {i+1}:")
    print(f"Original: \"{response}\"")
    cleaned = clean_reply(response)
    print(f"Cleaned:  \"{cleaned}\"")
    
    if "ai" in cleaned.lower() or "deepseek" in cleaned.lower() or "language model" in cleaned.lower():
        print("❌ FAILED: Cleaned response still contains AI references")
    else:
        print("✅ PASSED: Successfully removed AI references")

# Next, test with actual API calls
async def test_extreme_cases():
    print("\n\n=== Testing with Actual API Calls ===\n")
    
    for test in extreme_tests:
        print(f"Testing: {test['name']}")
        print(f"Original: \"{test['post']['original']['text']}\"")
        print(f"Target: \"{test['post']['target']['text']}\"")
        
        try:
            async with aiohttp.ClientSession() as session:
                print("\nSending request...")
                resp = await session.post(
                    'http://localhost:8000/generate-reply',
                    json=test['post']
                )
                
                status = resp.status
                print(f"Response status: {status}")
                
                js = await resp.json()
                reply = js.get("reply", "")
                print(f"Reply: \"{reply}\"")
                
                # Check for problematic terms
                problematic_terms = ['deepseek', 'deep seek', 'ai', 'artificial intelligence', 
                                    'language model', 'assistant', 'cannot', 'don\'t have']
                
                clean = True
                for term in problematic_terms:
                    if term.lower() in reply.lower():
                        print(f"⚠️ WARNING: Found '{term}' in reply")
                        clean = False
                
                if clean:
                    print("✅ SUCCESS: Reply is clean of AI references")
                print("\n-----------------------------------\n")
                    
        except Exception as e:
            print(f"Error: {str(e)}")

if __name__ == "__main__":
    # Run the API test
    asyncio.run(test_extreme_cases()) 