import asyncio
import re
from app.services.reply import clean_reply, make_reply

# Test cases with deliberate DeepSeek/AI content to ensure cleaning is working
test_replies = [
    "As a DeepSeek language model, I cannot go hiking with you, but that trail sounds amazing! 🏔",
    "DeepSeek thinks you should try the north trail! 🌲",
    "I'm an AI assistant but I'd recommend the Sunset Ridge trail! 🌄",
    "According to DeepSeek's analysis, you'd love the mountain view! 🗻",
    "As an AI language model I don't hike, but that summit looks breathtaking! 🌅",
    "Assistant: The western trail has the best wildlife viewing spots! 🦊",
    "User: Which trail is best? Assistant: Definitely try Eagle Ridge! 🦅",
    "I don't have personal experiences with hiking, but sunrise hikes are magical! ☀️",
    "I cannot physically hike, but those views must be worth the climb! 🏞",
]

def test_cleaning():
    print("\n=== Testing Reply Cleaning ===\n")
    
    passed = 0
    total = len(test_replies)
    
    for i, reply in enumerate(test_replies):
        print(f"Test {i+1}:")
        print(f"Original: \"{reply}\"")
        cleaned = clean_reply(reply)
        print(f"Cleaned:  \"{cleaned}\"")
        
        # Check if any banned words remain
        banned_patterns = [
            r'(?i)deepseek', r'(?i)deep\s*seek', r'(?i)as an AI', r'(?i)I\'m an AI',
            r'(?i)AI assistant', r'(?i)language model', r'(?i)I cannot',
            r'(?i)assistant:', r'(?i)^user:', r'(?i)^system:'
        ]
        
        test_passed = True
        for pattern in banned_patterns:
            if re.search(pattern, cleaned):
                print(f"❌ FAILED: Found banned pattern '{pattern}' in cleaned reply")
                test_passed = False
        
        if test_passed:
            print("✅ PASSED: No banned patterns found")
            passed += 1
        print()
    
    print(f"Summary: {passed}/{total} tests passed\n")
            
async def test_real_api():
    print("\n=== Testing With Real API ===\n")
    
    # Test cases with prompts likely to generate AI-related content
    test_cases = [
        {
            "name": "AI hiking recommendations",
            "post": {
                "postId": "test-api-clean-1",
                "original": {
                    "username": "curious_user", 
                    "text": "I'm wondering if AI can help me find good hiking trails. What do you think?"
                },
                "target": {
                    "username": "nature_guide", 
                    "text": "AI tools can be great for finding trails! I use several hiking apps myself."
                }
            }
        },
        {
            "name": "DeepSeek mention in original",
            "post": {
                "postId": "test-api-clean-2",
                "original": {
                    "username": "tech_fan", 
                    "text": "Just tried DeepSeek and it's amazing for generating creative content!"
                },
                "target": {
                    "username": "content_creator", 
                    "text": "That's interesting! What kind of content have you created with it?"
                }
            }
        }
    ]
    
    for test_case in test_cases:
        print(f"Testing: {test_case['name']}")
        print(f"Original post: \"{test_case['post']['original']['text']}\"")
        print(f"Target post: \"{test_case['post']['target']['text']}\"")
        
        print("\nGenerating reply...")
        reply = await make_reply(test_case['post'])
        print(f"Final reply: \"{reply}\"")
        
        # Check if any banned terms exist in the final reply
        banned_terms = ['deepseek', 'deep seek', 'ai', 'artificial intelligence', 
                       'language model', 'assistant', 'cannot', 'don\'t have']
        
        passed = True
        for term in banned_terms:
            if term.lower() in reply.lower():
                print(f"⚠️ WARNING: Found potentially problematic term '{term}' in reply")
                passed = False
        
        if passed:
            print("✅ SUCCESS: Reply is clean of AI references")
        print("\n-----------------------------------\n")
    
    print("Test complete!")

if __name__ == "__main__":
    # First test the cleaning function directly
    test_cleaning()
    
    # Then test with the real API
    asyncio.run(test_real_api()) 