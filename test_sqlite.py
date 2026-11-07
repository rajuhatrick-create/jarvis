"""Quick test for SQLite database and basic JARVIS functionality"""
# -*- coding: utf-8 -*-
import json
import urllib.request
import time
import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

base = "http://localhost:8080"

def test_api():
    print("=== Testing Sync Status ===")
    req = urllib.request.Request(f"{base}/api/sync/status")
    resp = urllib.request.urlopen(req)
    data = json.loads(resp.read())
    print(f"Mode: {data['mode']}")
    print(f"Database connected: {data['database_connected']}")
    print(f"Memories: {data['memories_count']}")
    print(f"Topics: {data['topics_learned']}")
    assert data['database_connected'] == True, "Database should be connected!"
    print("✅ Sync status OK\n")

def test_learning_stats():
    print("=== Testing Learning Stats ===")
    req = urllib.request.Request(f"{base}/api/learning/stats")
    resp = urllib.request.urlopen(req)
    data = json.loads(resp.read())
    print(f"Memories: {data['total_memories']}")
    print(f"Patterns: {data['total_patterns']}")
    print("✅ Learning stats OK\n")

def test_websocket():
    print("=== Testing WebSocket Chat ===")
    import websocket
    ws = websocket.create_connection("ws://localhost:8080/ws", timeout=5)
    
    # Test greeting
    ws.send("hello")
    result = json.loads(ws.recv())
    print(f"Hello -> {result['text'][:60]}...")
    
    # Test teach command
    ws.send("teach me Python is a programming language")
    result = json.loads(ws.recv())
    print(f"Teach -> {result['text'][:60]}...")
    
    # Test recall
    ws.send("what is Python")
    result = json.loads(ws.recv())
    print(f"What is Python -> {result['text'][:60]}...")
    
    # Test time
    ws.send("what time is it")
    result = json.loads(ws.recv())
    print(f"Time -> {result['text'][:60]}...")
    
    ws.close()
    print("✅ WebSocket chat OK\n")

def test_memory_persistence():
    print("=== Testing Memory Persistence ===")
    time.sleep(1)
    req = urllib.request.Request(f"{base}/api/learning/stats")
    resp = urllib.request.urlopen(req)
    data = json.loads(resp.read())
    print(f"Memories after teaching: {data['total_memories']}")
    assert data['total_memories'] >= 1, "Should have at least 1 memory!"
    print("✅ Memory persistence OK\n")

if __name__ == "__main__":
    test_api()
    test_learning_stats()
    test_websocket()
    test_memory_persistence()
    print("=" * 40)
    print("All tests passed! ✅")
