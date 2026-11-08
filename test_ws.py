"""Test jokes and conversation via WebSocket"""
import asyncio
import websockets
import json

async def test():
    uri = "ws://localhost:8080/ws"
    async with websockets.connect(uri) as ws:
        # Test jokes
        print("=== Testing Jokes ===")
        jokes = []
        for i in range(5):
            await ws.send(json.dumps({"type": "command", "text": "tell me a joke"}))
            resp = await asyncio.wait_for(ws.recv(), timeout=5)
            data = json.loads(resp)
            joke = data.get("text", "")
            jokes.append(joke)
            print(f"Joke {i+1}: {joke[:80]}")
        
        unique = len(set(jokes))
        print(f"\nUnique jokes: {unique}/5")
        if unique >= 4:
            print("OK - Jokes are diverse!")
        else:
            print("FAIL - Jokes are repetitive")
        
        # Test conversation
        print("\n=== Testing Conversation ===")
        tests = [
            ("hello", "greeting"),
            ("how are you", "casual"),
            ("what is love", "open-ended"),
            ("tell me a fun fact", "fun fact"),
            ("I'm bored", "boredom"),
            ("what do you think about AI", "opinion"),
            ("why is the sky blue", "unknown"),
            ("thanks for helping", "gratitude"),
            ("I'm tired", "empathy"),
            ("what is success", "philosophical"),
        ]
        
        for text, category in tests:
            await ws.send(json.dumps({"type": "command", "text": text}))
            resp = await asyncio.wait_for(ws.recv(), timeout=5)
            data = json.loads(resp)
            response = data.get("text", "")
            print(f"[{category}] '{text}' -> {response[:100]}")
        
        print("\nAll tests completed!")

asyncio.run(test())
