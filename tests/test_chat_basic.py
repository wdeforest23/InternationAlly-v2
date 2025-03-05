import asyncio
import logging
from app.utils.chat_manager import ChatManager
import json

logging.basicConfig(level=logging.DEBUG)

async def test_chat():
    chat_manager = ChatManager()
    
    # Test cases with multi-intent queries
    test_messages = [
        "I'm looking for an apartment near campus and some good restaurants nearby",
        "Can you tell me about student housing options and study spots around UChicago?",
        "What are some affordable apartments near good coffee shops?",
        "Tell me about visa requirements and where international students usually live",
        "Show me apartments under $2000 near campus",
        "What coffee shops are open right now near UChicago?",
        "I need a 2-bedroom apartment near some good restaurants",
    ]
    
    for message in test_messages:
        print(f"\n=== Testing message: {message} ===")
        
        try:
            # Test full message processing
            print("\nProcessing response...")
            response = await chat_manager.process_message(message)
            
            if response.get('success'):
                print("\nIntent Analysis:")
                print(json.dumps(response['analysis'], indent=2))
                
                print("\nAPI Data Retrieved:")
                print(json.dumps(response['api_data'], indent=2))
                
                print("\nFinal Response:")
                print(response['response'])
            else:
                print(f"Error: {response.get('error')}")
            
        except Exception as e:
            print(f"Error during testing: {str(e)}")
        
        print("\n" + "="*50)

if __name__ == "__main__":
    asyncio.run(test_chat()) 