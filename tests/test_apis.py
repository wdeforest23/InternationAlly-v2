import asyncio
import logging
from app.utils.chat_manager import ChatManager
import json

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

async def test_chat():
    print("\n=== Testing ChatManager with Various Queries ===\n")
    
    chat_manager = ChatManager()
    
    # Single comprehensive test case that covers both housing and location
    test_message = "I need a furnished 2-bedroom apartment in Hyde Park under $2000 with parking and in-unit laundry, and also tell me about grocery stores within a 10-minute walk"
    
    print(f"\nTesting query: {test_message}")
    print("-" * 80)
    
    try:
        result = await chat_manager.process_message(test_message)
        
        if result["success"]:
            print("\nIntent Analysis & Extracted Parameters:")
            print(json.dumps(result["analysis"], indent=2))
            
            print("\nAPI Data Retrieved:")
            if result["api_data"]["housing"]:
                print(f"\nHousing: Found {len(result['api_data']['housing'])} properties")
            else:
                print("\nHousing: No data retrieved")
            
            if result["api_data"]["places"]:
                print(f"\nPlaces: Found {len(result['api_data']['places'])} places")
            else:
                print("\nPlaces: No data retrieved")
            
            print("\nGenerated Response:")
            print(result["response"])
        else:
            print(f"Error: {result['error']}")
        
    except Exception as e:
        print(f"Error processing message: {str(e)}")
        logger.exception("Detailed error information:")
    
    print("\n" + "=" * 80)

if __name__ == "__main__":
    asyncio.run(test_chat()) 