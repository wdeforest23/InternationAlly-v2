from typing import Dict, Any, List, Optional
import os
from openai import OpenAI
import vertexai
from vertexai.preview.generative_models import GenerativeModel, ChatSession
from vertexai.generative_models import SafetySetting, HarmCategory, HarmBlockThreshold
from .rag_system import RAGSystem
from .zillow_api import ZillowAPI
from .google_maps_api import GoogleMapsAPI
import logging
import json
import asyncio
import re

# Enhanced logging
logging.basicConfig(
    filename='chat.log',
    level=logging.DEBUG,  # Changed to DEBUG for more detail
    format='%(asctime)s - %(levelname)s - %(message)s'
)

class ChatError(Exception):
    """Custom exception for chat-related errors"""
    pass

class ChatManager:
    def __init__(self):
        """Initialize the chat manager with all required components"""
        try:
            # Initialize OpenAI
            if not os.getenv('OPENAI_API_KEY'):
                raise ValueError("OpenAI API key not found")
            self.openai_client = OpenAI()
            
            # Initialize Vertex AI
            vertexai.init(project="internationally", location="us-central1")
            safety_config = [
                SafetySetting(category=cat, threshold=HarmBlockThreshold.OFF)
                for cat in [
                    HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT,
                    HarmCategory.HARM_CATEGORY_HATE_SPEECH,
                    HarmCategory.HARM_CATEGORY_HARASSMENT,
                ]
            ]
            self.gemini = GenerativeModel("gemini-2.0-flash-001", safety_settings=safety_config)
            self.gemini_chat = self.gemini.start_chat(response_validation=False)
            
            # Initialize all tools
            self.rag = RAGSystem()
            self.zillow_api = ZillowAPI()
            self.google_maps_api = GoogleMapsAPI()
            
            # Initialize conversation history
            self.conversation_history = []
            
            logging.info("ChatManager initialized successfully with all tools")
            
        except Exception as e:
            logging.error(f"Error initializing ChatManager: {str(e)}")
            raise

    async def analyze_query(self, query: str) -> Dict[str, Any]:
        """Use Gemini to analyze query intent and extract parameters"""
        try:
            # Simplified, strict prompt focused on JSON output
            prompt = """You are a query analysis system. Your ONLY task is to extract structured information from user queries and output it in the exact JSON format shown in the examples. Do not provide any additional information or explanations.

Example 1 Input: "Find me a furnished studio near campus under $1500"
{
    "intents": ["housing_search"],
    "parameters": {
        "housing": {
            "location": "Hyde Park, Chicago",
            "price_range": [0, 1500],
            "bedrooms": 0,
            "property_type": "apartment",
            "amenities": ["furnished"],
            "radius_miles": 1
        },
        "location": {},
        "student_info": {}
    }
}

Example 2 Input: "What Asian restaurants are open now within 10 minutes walk of UChicago?"
{
    "intents": ["location_info"],
    "parameters": {
        "housing": {},
        "location": {
            "search_type": "restaurant",
            "location": "University of Chicago",
            "radius_meters": 800,
            "keywords": ["Asian", "restaurant"],
            "open_now": true
        },
        "student_info": {}
    }
}

Example 3 Input: "How many hours can I work on campus with an F-1 visa?"
{
    "intents": ["student_info"],
    "parameters": {
        "housing": {},
        "location": {},
        "student_info": {
            "topic": "employment",
            "subtopic": "on_campus_work",
            "visa_type": "F-1"
        }
    }
}

Example 4 Input: "What documents do I need for OPT application?"
{
    "intents": ["student_info"],
    "parameters": {
        "housing": {},
        "location": {},
        "student_info": {
            "topic": "employment",
            "subtopic": "opt",
            "document_type": "application_requirements"
        }
    }
}

IMPORTANT: Your response must ONLY contain the JSON object, nothing else. No explanations, no additional text."""
            
            # Set up the context
            self.gemini_chat.send_message(prompt)
            
            # Get the analysis
            response = self.gemini_chat.send_message(f"Parse this query into the exact JSON format shown above: {query}")
            logging.debug(f"Raw Gemini response:\n{response.text}")
            
            # Clean the response
            cleaned_text = re.sub(r'```json\s*|\s*```', '', response.text).strip()
            logging.debug(f"Cleaned response text:\n{cleaned_text}")
            
            try:
                parsed = json.loads(cleaned_text)
                logging.debug(f"Successfully parsed JSON:\n{json.dumps(parsed, indent=2)}")
                return parsed
                
            except json.JSONDecodeError as e:
                logging.error(f"JSON decode error: {str(e)}")
                logging.error(f"Problem text: {cleaned_text}")
                raise
            
        except Exception as e:
            logging.error(f"Error in analyze_query: {str(e)}", exc_info=True)
            raise

    def _format_property_response(self, properties: List[Dict]) -> str:
        """Format property data into a readable response"""
        if not properties:
            return "I couldn't find any properties matching your criteria."
        
        response_parts = ["Here are some available properties I found:\n"]
        
        for prop in properties:
            # Handle both single units and multi-unit buildings
            if 'units' in prop:
                units = prop['units']
                prices = [unit['price'] for unit in units]
                beds = [unit['beds'] for unit in units]
                response_parts.append(
                    f"🏢 {prop['buildingName'] or prop['address']}\n"
                    f"• Available units: {', '.join(f'{beds[i]} bed @ {prices[i]}' for i in range(len(units)))}\n"
                    f"• Location: {prop['address']}\n"
                    f"• More info: {prop.get('detailUrl', 'Contact for details')}\n"
                )
            else:
                response_parts.append(
                    f"🏠 {prop['address']}\n"
                    f"• {prop['bedrooms']} bed, {prop['bathrooms']} bath\n"
                    f"• Price: ${prop['price']}/month\n"
                    f"• More info: {prop['url']}\n"
                )
        
        return "\n".join(response_parts)

    def _format_places_response(self, places: List[Dict]) -> str:
        """Format places data into a readable response"""
        if not places:
            return "I couldn't find any places matching your criteria."
        
        response_parts = ["Here are some places I found:\n"]
        
        for place in places:
            rating_stars = "⭐" * int(place.get('rating', 0))
            response_parts.append(
                f"�� {place['name']}\n"
                f"• Rating: {rating_stars} ({place.get('rating', 'N/A')}/5 from {place.get('user_ratings', 0)} reviews)\n"
                f"• Address: {place['address']}\n"
                f"• Google Maps: {place['google_maps_link']}\n"
            )
        
        return "\n".join(response_parts)

    async def process_message(self, message: str) -> Dict[str, Any]:
        """Process a user message and generate a response"""
        try:
            logging.info(f"Starting to process message: {message}")
            
            # Analyze query intents
            analysis = await self.analyze_query(message)
            logging.info(f"Query analysis: {json.dumps(analysis, indent=2)}")
            
            # Initialize context and data collectors
            context_parts = []
            api_data = {"housing": None, "places": None, "rag": None}
            
            # Get RAG context only for student_info queries
            if "student_info" in analysis["intents"]:
                try:
                    student_params = analysis["parameters"].get("student_info", {})
                    # Enhance the query with specific parameters for better RAG results
                    enhanced_query = f"{message} {student_params.get('topic', '')} {student_params.get('subtopic', '')}"
                    
                    rag_docs = self.rag.query(enhanced_query, n_results=3)
                    rag_context = self.rag.generate_response(enhanced_query, rag_docs)
                    context_parts.append(f"Official Information:\n{rag_context}")
                    api_data["rag"] = rag_docs
                    logging.info("RAG context retrieved successfully")
                except Exception as e:
                    logging.error(f"Error getting RAG context: {str(e)}")
            
            # Get housing information if relevant
            if "housing_search" in analysis["intents"]:
                try:
                    housing_params = analysis["parameters"].get("housing", {})
                    logging.debug(f"Calling Zillow API with params: {json.dumps(housing_params, indent=2)}")
                    
                    properties = self.zillow_api.search_properties(
                        location=housing_params.get("location"),
                        min_price=housing_params.get("price_range", [0, 2000])[0],
                        max_price=housing_params.get("price_range", [0, 2000])[1],
                        property_type=housing_params.get("property_type"),
                        bedrooms=housing_params.get("bedrooms"),
                        amenities=housing_params.get("amenities", []),
                        radius=housing_params.get("radius_miles", 1)
                    )
                    
                    if properties:
                        logging.info(f"Found {len(properties)} properties")
                        api_data["housing"] = properties
                        context_parts.append(self._format_property_response(properties))
                    else:
                        logging.warning("No properties found from Zillow API")
                        
                except Exception as e:
                    logging.error(f"Error getting housing information: {str(e)}", exc_info=True)
            
            # Get location information if relevant
            if "location_info" in analysis["intents"]:
                try:
                    location_params = analysis["parameters"].get("location", {})
                    logging.debug(f"Calling Google Maps API with params: {json.dumps(location_params, indent=2)}")
                    
                    places = self.google_maps_api.search_places(
                        query=location_params.get("search_type"),
                        location=location_params.get("location"),
                        radius=location_params.get("radius_meters", 1000),
                        keywords=location_params.get("keywords", []),
                        open_now=location_params.get("open_now", False)
                    )
                    
                    if places:
                        logging.info(f"Found {len(places)} places")
                        api_data["places"] = places
                        context_parts.append(self._format_places_response(places))
                    else:
                        logging.warning("No places found from Google Maps API")
                        
                except Exception as e:
                    logging.error(f"Error getting location information: {str(e)}", exc_info=True)
            
            # Generate final response using GPT-4
            system_message = """You are InternationAlly, an AI assistant helping international students at the University of Chicago.
            Use the following information to provide a helpful, natural response that combines background knowledge with real-time data.
            When mentioning properties or places, reference specific details but maintain a conversational tone.
            
            {context}
            
            Important: These are current listings and places - encourage users to check the provided links for the most up-to-date information.
            Always mention if you're showing a subset of available options and suggest refining the search if needed."""
            
            completion = self.openai_client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": system_message.format(context="\n\n".join(context_parts))},
                    {"role": "user", "content": message}
                ],
                temperature=0.7,
            )
            
            response_text = completion.choices[0].message.content
            logging.info("Response generated successfully")
            
            return {
                "success": True,
                "response": response_text,
                "analysis": analysis,
                "api_data": api_data
            }
            
        except Exception as e:
            logging.error(f"Error in process_message: {str(e)}", exc_info=True)
            return {
                "success": False,
                "error": str(e)
            }

    def clear_history(self):
        """Clear the conversation history"""
        self.conversation_history = [] 