"""Test the conversation engine - makes JARVIS feel human-like"""
import asyncio
import websockets
import json

test_cases = [
    # Casual conversation
    ("hello", "greeting"),
    ("how are you", "casual - how are you"),
    ("what's up", "casual - what's up"),
    ("tell me about yourself", "casual - about yourself"),
    ("thanks", "casual - thanks"),
    ("you're awesome", "casual - compliment"),
    ("i'm bored", "casual - boredom"),
    ("goodbye", "goodbye"),
    
    # Commands
    ("what time is it", "time"),
    ("tell me a joke", "joke"),
    ("what is 15 * 3", "math"),
    
    # Unknown (should use natural fallback)
    ("what is the meaning of life", "unknown question"),
    ("can you fly", "unknown question"),
]

async def test():
    uri = "ws://localhost:8080/ws"
    async with websockets.connect(uri) as ws:
        for text, label in test_cases:
            await ws.send(json.dumps({"type": "command", "text": text}))
            response = await ws.recv()
            data = json.loads(response)
            print("TEST:", label)
            print("INPUT:", text)
            print("OUTPUT:", data['text'])
            print("---")

if __name__ == '__main__':
    asyncio.run(test())
