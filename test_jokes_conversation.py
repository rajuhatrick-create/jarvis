"""Test the new joke system and conversation engine"""
import json
import urllib.request
import time

def test_api():
    base = "http://localhost:8080"
    
    # Test jokes - should be diverse
    print("=== Testing Jokes ===")
    jokes_told = []
    for i in range(5):
        req = urllib.request.Request(f"{base}/api/command")
        req.add_header('Content-Type', 'application/json')
        data = json.dumps({"type": "command", "text": "tell me a joke"}).encode()
        try:
            resp = urllib.request.urlopen(req, data)
            result = json.loads(resp.read().decode())
            joke = result.get("response", "")
            jokes_told.append(joke)
            print(f"Joke {i+1}: {joke[:80]}...")
        except Exception as e:
            print(f"Error: {e}")
        time.sleep(0.5)
    
    # Check diversity
    unique_jokes = len(set(jokes_told))
    print(f"\nUnique jokes out of 5: {unique_jokes}/5")
    if unique_jokes >= 4:
        print("✅ Jokes are diverse!")
    else:
        print("❌ Jokes are repetitive")
    
    # Test conversation
    print("\n=== Testing Conversation ===")
    test_cases = [
        ("hello", "greeting"),
        ("how are you", "casual"),
        ("what is love", "open-ended"),
        ("tell me a fun fact", "fun fact"),
        ("I'm bored", "boredom"),
        ("what do you think about AI", "opinion"),
        ("why is the sky blue", "unknown question"),
        ("thanks for helping", "gratitude"),
        ("I'm tired", "empathy"),
        ("what is success", "philosophical"),
    ]
    
    for text, category in test_cases:
        req = urllib.request.Request(f"{base}/api/command")
        req.add_header('Content-Type', 'application/json')
        data = json.dumps({"type": "command", "text": text}).encode()
        try:
            resp = urllib.request.urlopen(req, data)
            result = json.loads(resp.read().decode())
            response = result.get("response", "")
            print(f"[{category}] '{text}' → {response[:100]}...")
        except Exception as e:
            print(f"[{category}] '{text}' → Error: {e}")
        time.sleep(0.3)
    
    print("\n✅ All tests completed!")

if __name__ == "__main__":
    test_api()
