"""Test custom LLM via WebSocket"""
import asyncio
import websockets
import json

async def test():
    async with websockets.connect('ws://localhost:8080/ws') as ws:
        tests = [
            'hello',
            'how are you',
            'what is love',
            'tell me about yourself',
            "i'm happy today",
            "i'm feeling sad",
            'thank you',
            "you're amazing",
            "i'm bored",
            'what is the meaning of life',
        ]
        for text in tests:
            await ws.send(json.dumps({'type': 'command', 'text': text}))
            resp = await asyncio.wait_for(ws.recv(), timeout=10)
            data = json.loads(resp)
            print(f"User: {text}")
            print(f"JARVIS: {data.get('text', '')}")
            print()

asyncio.run(test())
