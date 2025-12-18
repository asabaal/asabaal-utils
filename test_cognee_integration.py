#!/usr/bin/env python3
"""
Test script for Cognee integration
"""
import asyncio
import requests
import json

# Base URL for the API
BASE_URL = "http://localhost:8002"

async def test_integration():
    print("Testing Cognee integration...")
    
    # 1. Add some memory items
    print("\n1. Adding memory items...")
    
    memories = [
        {
            "title": "Python Programming",
            "content": "Python is a high-level programming language known for its simplicity and readability. It supports multiple programming paradigms including procedural, object-oriented, and functional programming.",
            "tags": ["programming", "python", "technology"]
        },
        {
            "title": "Machine Learning Basics",
            "content": "Machine learning is a subset of artificial intelligence that enables systems to learn and improve from experience without being explicitly programmed. Common algorithms include neural networks, decision trees, and support vector machines.",
            "tags": ["machine learning", "AI", "algorithms"]
        },
        {
            "title": "Web Development",
            "content": "Web development involves creating websites and web applications. It includes frontend development (HTML, CSS, JavaScript) and backend development (server-side languages, databases, APIs).",
            "tags": ["web development", "frontend", "backend"]
        }
    ]
    
    for memory in memories:
        response = requests.post(
            f"{BASE_URL}/api/memory/items",
            json=memory
        )
        if response.status_code == 200:
            print(f"✓ Added: {memory['title']}")
        else:
            print(f"✗ Failed to add {memory['title']}: {response.status_code} - {response.text}")
    
    # Wait a bit for Cognee to process
    print("\n2. Waiting for Cognee to process memories...")
    await asyncio.sleep(3)
    
    # 3. Test chat completion with semantic search
    print("\n3. Testing chat completion...")
    test_queries = [
        "What programming language is good for beginners?",
        "Tell me about artificial intelligence",
        "How do I create a website?"
    ]
    
    for query in test_queries:
        response = requests.post(
            f"{BASE_URL}/api/chat/complete",
            json={"message": query}
        )
        if response.status_code == 200:
            result = response.json()
            print(f"\nQuery: {query}")
            print(f"Response: {result['text'][:200]}...")
            print(f"Memory hits: {len(result['used_memory'])}")
            for hit in result['used_memory']:
                print(f"  - Hit: {hit}")
        else:
            print(f"✗ Query failed: {response.status_code} - {response.text}")
    
    print("\n4. Testing memory list...")
    response = requests.get(f"{BASE_URL}/api/memory/items")
    if response.status_code == 200:
        items = response.json()
        print(f"Total memory items: {len(items)}")
        for item in items:
            print(f"  - {item['title']} ({', '.join(item['tags'])})")
    else:
        print(f"✗ Failed to list memories: {response.status_code} - {response.text}")

if __name__ == "__main__":
    asyncio.run(test_integration())