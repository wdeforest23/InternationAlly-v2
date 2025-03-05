import asyncio
from app.utils.chat_manager import ChatManager

async def test_chat():
    chat_manager = ChatManager()
    
    # Test different types of queries
    queries = [
        "What are the requirements for maintaining F-1 status?",
        "Can you help me find a 2-bedroom apartment near UChicago under $2000?",
        "What are some good restaurants near campus?",
        "How do I apply for OPT?"
    ]
    
    for query in queries:
        print(f"\nTesting query: {query}")
        response = await chat_manager.process_message(query)
        print(f"Success: {response['success']}")
        if response['success']:
            print(f"Analysis: {response['analysis']}")
            print(f"Response: {response['response'][:200]}...")
        else:
            print(f"Error: {response.get('error')}")

if __name__ == "__main__":
    asyncio.run(test_chat()) 