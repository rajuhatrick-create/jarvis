"""
Test script for validating Firebase connectivity and basic JARVIS operations.
Run this after setting up Firebase to verify everything works.
"""

import asyncio
import json
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

import websockets


async def test_basic_commands():
    """Test basic JARVIS commands via WebSocket"""
    print("\n=== Testing Basic Commands ===\n")
    
    tests = [
        ("hello", "greeting"),
        ("what time is it", "time"),
        ("tell me a joke", "joke"),
        ("system status", "system"),
    ]
    
    passed = 0
    failed = 0
    
    async with websockets.connect("ws://localhost:8080/ws") as ws:
        for command, test_name in tests:
            try:
                await ws.send(json.dumps({
                    'type': 'command',
                    'text': command
                }))
                response = await asyncio.wait_for(ws.recv(), timeout=10)
                data = json.loads(response)
                text = data.get('text', '')
                
                if text and len(text) > 5:
                    print(f"✓ {test_name}: {text[:60]}...")
                    passed += 1
                else:
                    print(f"✗ {test_name}: Empty response")
                    failed += 1
            except Exception as e:
                print(f"✗ {test_name}: {e}")
                failed += 1
    
    print(f"\nResults: {passed} passed, {failed} failed\n")
    return passed, failed


async def test_learning():
    """Test teaching and recalling facts"""
    print("\n=== Testing Learning AI ===\n")
    
    async with websockets.connect("ws://localhost:8080/ws") as ws:
        # Teach a fact
        await ws.send(json.dumps({
            'type': 'command',
            'text': 'teach me test fact is a verification of the learning system'
        }))
        response = await asyncio.wait_for(ws.recv(), timeout=10)
        data = json.loads(response)
        print(f"Teach: {data.get('text', '')}")
        
        # Recall the fact
        await ws.send(json.dumps({
            'type': 'command',
            'text': 'what is test fact'
        }))
        response = await asyncio.wait_for(ws.recv(), timeout=10)
        data = json.loads(response)
        text = data.get('text', '')
        
        if 'verification' in text.lower() or 'learning' in text.lower():
            print(f"✓ Recall: {text[:60]}...")
        else:
            print(f"✗ Recall failed: {text[:60]}...")


async def test_sync_status():
    """Test sync status API"""
    print("\n=== Testing Sync Status ===\n")
    
    import urllib.request
    try:
        with urllib.request.urlopen("http://localhost:8080/api/sync/status") as response:
            data = json.loads(response.read().decode())
            print(f"Mode: {data.get('mode', 'N/A')}")
            print(f"Firebase connected: {data.get('firebase_connected', False)}")
            print(f"Memories: {data.get('memories_count', 0)}")
            print(f"Topics: {data.get('topics_learned', 0)}")
    except Exception as e:
        print(f"✗ Sync status error: {e}")


async def test_learning_stats():
    """Test learning stats API"""
    print("\n=== Testing Learning Stats ===\n")
    
    import urllib.request
    try:
        with urllib.request.urlopen("http://localhost:8080/api/learning/stats") as response:
            data = json.loads(response.read().decode())
            print(f"Total memories: {data.get('total_memories', 0)}")
            print(f"Total patterns: {data.get('total_patterns', 0)}")
            print(f"Accuracy: {data.get('accuracy', 0):.2%}")
    except Exception as e:
        print(f"✗ Learning stats error: {e}")


async def main():
    """Run all tests"""
    print("=" * 50)
    print("  JARVIS Cloud Deployment Test Suite")
    print("=" * 50)
    
    # Check if server is running
    try:
        async with websockets.connect("ws://localhost:8080/ws") as ws:
            print("\n✓ Server is running on localhost:8080\n")
    except Exception as e:
        print(f"\n✗ Server not running! Start JARVIS first.")
        print(f"  Error: {e}")
        return
    
    await test_basic_commands()
    await test_learning()
    await test_sync_status()
    await test_learning_stats()
    
    print("\n" + "=" * 50)
    print("  Tests Complete")
    print("=" * 50)


if __name__ == "__main__":
    asyncio.run(main())
