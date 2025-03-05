import asyncio
import logging
from app.utils.chat_manager import ChatManager
import re

# Set up logging to see detailed output
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

def clean_json_response(text: str) -> str:
    """Remove markdown formatting and extract just the JSON content"""
    # Remove markdown code blocks
    text = re.sub(r'```json\s*|\s*```', '', text)
    return text.strip()

async def test_gemini_analysis():
    chat_manager = ChatManager()
    
    test_query = "I need a furnished 2-bedroom apartment in Hyde Park under $2000 with parking and in-unit laundry, and also tell me about grocery stores within a 10-minute walk"
    
    print("\n=== Testing Gemini Query Analysis ===")
    print(f"\nQuery: {test_query}")
    
    try:
        # First, send the system prompt to set up the context
        system_prompt = """You are a query analysis system. Your ONLY task is to extract structured information from user queries and output it in the exact JSON format shown in the examples. Do not provide any additional information or explanations.

Example 1 Input: "Find me a furnished studio near campus under $1500"
{
    "intents": ["housing_search", "general_information"],
    "parameters": {
        "housing": {
            "location": "Hyde Park, Chicago",
            "price_range": [0, 1500],
            "bedrooms": 0,
            "property_type": "apartment",
            "amenities": ["furnished"],
            "radius_miles": 1
        },
        "location": {}
    }
}

Example 2 Input: "What Asian restaurants are open now within 10 minutes walk of UChicago?"
{
    "intents": ["location_info", "general_information"],
    "parameters": {
        "housing": {},
        "location": {
            "search_type": "restaurant",
            "location": "University of Chicago",
            "radius_meters": 800,
            "keywords": ["Asian", "restaurant"],
            "open_now": true
        }
    }
}

IMPORTANT: Your response must ONLY contain the JSON object, nothing else. No explanations, no additional text."""

        # Send system prompt
        chat_manager.gemini_chat.send_message(system_prompt)
        
        # Now send the actual query
        print("\n=== Raw Gemini Response ===")
        response = chat_manager.gemini_chat.send_message(f"Parse this query into the exact JSON format shown above: {test_query}")
        print(response.text)
        
        # Clean and parse the response
        if response.text:
            print("\n=== Cleaned Response ===")
            cleaned_text = clean_json_response(response.text)
            print(cleaned_text)
            
            print("\n=== Parsed JSON ===")
            try:
                import json
                parsed = json.loads(cleaned_text)
                print(json.dumps(parsed, indent=2))
                print("\nJSON parsing successful!")
            except json.JSONDecodeError as je:
                print(f"JSON Parse Failed: {str(je)}")
                print("Raw text causing the error:")
                print(cleaned_text)
        else:
            print("\nNo response text received from Gemini")
            
    except Exception as e:
        print("\n=== Error Occurred ===")
        print(f"Error type: {type(e).__name__}")
        print(f"Error message: {str(e)}")
        logging.exception("Detailed error information:")

if __name__ == "__main__":
    asyncio.run(test_gemini_analysis()) 