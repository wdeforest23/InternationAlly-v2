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
from datetime import datetime, timedelta
from ..models.conversation import Conversation, Message
from ..models.user import User
from ..services.cache_service import CacheService
from ..models.db import db

# Create logs directory if it doesn't exist
if not os.path.exists('logs'):
    os.makedirs('logs')

# Configure module logger
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

# Create file handler
file_handler = logging.FileHandler('logs/app.log')
file_handler.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
file_handler.setFormatter(formatter)

# Add handlers
logger.addHandler(file_handler)

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
            
            # Add cache service
            self.cache_service = CacheService()
            
            logger.info("ChatManager initialized successfully with all tools")
            
        except Exception as e:
            logger.error(f"Error initializing ChatManager: {str(e)}")
            raise

    def analyze_query(self, query: str) -> Dict[str, Any]:
        """Make synchronous version of analyze_query"""
        try:
            # Keep existing prompt
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
            
            # Set up the context and get response synchronously
            self.gemini_chat.send_message(prompt)
            response = self.gemini_chat.send_message(f"Parse this query into the exact JSON format shown above: {query}")
            logger.debug(f"Raw Gemini response:\n{response.text}")
            
            # Clean the response
            cleaned_text = re.sub(r'```json\s*|\s*```', '', response.text).strip()
            logger.debug(f"Cleaned response text:\n{cleaned_text}")
            
            try:
                parsed = json.loads(cleaned_text)
                logger.debug(f"Successfully parsed JSON:\n{json.dumps(parsed, indent=2)}")
                return parsed
                
            except json.JSONDecodeError as e:
                logger.error(f"JSON decode error: {str(e)}")
                logger.error(f"Problem text: {cleaned_text}")
                raise
            
        except Exception as e:
            logger.error(f"Error in analyze_query: {str(e)}", exc_info=True)
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

    def get_or_create_conversation(self, user_id: int, create_new: bool = False) -> Conversation:
        """Synchronous version of get_or_create_conversation"""
        if create_new:
            # End any existing active conversation
            active_conv = Conversation.query.filter_by(
                user_id=user_id, 
                is_active=True
            ).first()
            if active_conv:
                active_conv.is_active = False
                db.session.commit()
            
            # Create new conversation
            conv = Conversation(user_id=user_id)
            db.session.add(conv)
            db.session.commit()
            return conv
            
        return (Conversation.query.filter_by(
            user_id=user_id,
            is_active=True
        ).first() or self.get_or_create_conversation(user_id, create_new=True))

    def get_conversation_context(self, user_id: int, conversation_id: int) -> str:
        """Synchronous version of get_conversation_context"""
        # Get user profile
        user = User.query.get(user_id)
        
        # Get recent messages
        recent_messages = Message.query.filter_by(
            conversation_id=conversation_id
        ).order_by(Message.timestamp.desc()).limit(5).all()
        
        # Get relevant messages from other conversations
        other_relevant = Message.query.join(Conversation).filter(
            Conversation.user_id == user_id,
            Conversation.id != conversation_id,
            Message.timestamp > (datetime.utcnow() - timedelta(days=30))
        ).order_by(Message.timestamp.desc()).limit(3).all()
        
        context = f"""User Profile:
        - Name: {user.first_name} {user.last_name}
        - University: {user.university or 'Not specified'}
        - Student Status: {user.student_status or 'Not specified'}
        - Visa Type: {user.visa_type or 'Not specified'}
        - Housing Preferences: {user.housing_preferences or {}}
        
        Current Conversation:
        {self._format_messages(recent_messages) if recent_messages else 'No previous messages'}
        
        Relevant Past Interactions:
        {self._format_messages(other_relevant) if other_relevant else 'No relevant past interactions'}
        """
        
        return context

    def _format_messages(self, messages: List[Message]) -> str:
        """Helper method to format messages"""
        if not messages:
            return "No messages"
        
        formatted = []
        for msg in messages:
            formatted.append(f"{msg.role}: {msg.content}")
        return "\n".join(formatted)

    def format_zillow_listing(self, prop):
        address = prop.get('address', '')
        units = prop.get('units', [])
        detail_url = prop.get('detailUrl', '')
        
        # Format bed/bath/price info
        unit_info = []
        for unit in units:
            beds = unit.get('beds', 'N/A')
            price = unit.get('price', '').replace('+', '') # Remove the '+' from price
            if beds and price:
                unit_info.append(f"{beds} bed • {price}")
        
        # Clean up the URL
        base_url = "https://www.zillow.com"
        full_url = base_url + detail_url if detail_url else ""
        
        # Format the listing text
        listing_text = f"🏠 {address}"
        if unit_info:
            listing_text += f" • {' | '.join(unit_info)}"
        if full_url:
            listing_text += f" • More info: {full_url}"
        
        return listing_text

    def process_housing_search(self, params):
        try:
            # Extract search parameters
            location = params.get('location', 'Hyde Park, Chicago')
            price_range = params.get('price_range', [0, 2000])
            bedrooms = params.get('bedrooms')
            property_type = params.get('property_type', 'apartment')
            
            # Use the existing zillow_api instance
            zillow_response = self.zillow_api.search_properties(
                location=location,
                min_price=price_range[0],
                max_price=price_range[1],
                bedrooms=bedrooms,
                property_type=property_type
            )
            
            # Format results
            listings = []
            for prop in zillow_response[:5]:  # Limit to 5 properties
                try:
                    # Handle multi-unit buildings
                    if 'units' in prop:
                        building_name = prop.get('buildingName', '')
                        address = prop.get('address', '')
                        display_address = f"{building_name} - {address}" if building_name else address
                        
                        units_info = []
                        for unit in prop['units']:
                            beds = unit.get('beds', 'N/A')
                            price = unit.get('price', '').replace('$', '').replace('+', '')
                            units_info.append(f"{beds} bed • ${price}")
                        
                        listing_text = f"🏢 {display_address}\n"
                        listing_text += f"• Available units: {' | '.join(units_info)}\n"
                        if prop.get('detailUrl'):
                            listing_text += f"• More info: https://www.zillow.com{prop['detailUrl']}"
                    
                    # Handle single units
                    else:
                        address = prop.get('address', '')
                        price = prop.get('price', 'N/A')
                        beds = prop.get('bedrooms', 'N/A')
                        baths = prop.get('bathrooms', 'N/A')
                        
                        listing_text = f"🏠 {address}\n"
                        listing_text += f"• {beds} bed, {baths} bath\n"
                        listing_text += f"• Price: ${price}/month\n"
                        if prop.get('detailUrl'):
                            listing_text += f"• More info: https://www.zillow.com{prop['detailUrl']}"
                    
                    listings.append(listing_text)
                    
                except Exception as e:
                    logger.error(f"Error formatting property: {str(e)}")
                    continue
            
            if not listings:
                return "I apologize, but I couldn't find any properties matching your criteria at this time."
            
            return "Here are some available properties I found:\n\n" + "\n\n".join(listings)
            
        except Exception as e:
            logger.error(f"Error in process_housing_search: {str(e)}")
            return "I apologize, but I encountered an error while searching for properties. Please try again."

    def process_message(self, message: str, user_id: int) -> Dict[str, Any]:
        """Process message with detailed error logging"""
        try:
            logger.info(f"Starting to process message: '{message}' for user {user_id}")
            
            # Get or create conversation
            conversation = self.get_or_create_conversation(user_id)
            logger.info(f"Using conversation {conversation.id}")
            
            # Store user message
            user_message = Message(
                conversation_id=conversation.id,
                role='user',
                content=message
            )
            db.session.add(user_message)
            db.session.commit()
            
            # Analyze query
            analysis = self.analyze_query(message)
            logger.info(f"Query analysis: {json.dumps(analysis, indent=2)}")
            
            # Initialize response
            response_parts = []
            api_data = {"housing": None, "places": None, "rag": None}
            
            # Process intents
            try:
                if "housing_search" in analysis.get("intents", []):
                    housing_params = analysis["parameters"]["housing"]
                    logger.info(f"Processing housing search with params: {housing_params}")
                    
                    # Get the response from Zillow API
                    zillow_response = self.zillow_api.search_properties(
                        location=housing_params.get('location', 'Hyde Park, Chicago'),
                        min_price=housing_params.get('price_range', [0, 2000])[0],
                        max_price=housing_params.get('price_range', [0, 2000])[1],
                        bedrooms=housing_params.get('bedrooms'),
                        property_type=housing_params.get('property_type', 'apartment')
                    )
                    
                    # Store the API response in api_data
                    api_data["housing"] = zillow_response
                    
                    # Format and append the response
                    response_parts.append(self.process_housing_search(housing_params))
                    
                elif "location_info" in analysis.get("intents", []):
                    location_params = analysis["parameters"]["location"]
                    logger.info(f"Processing location search with params: {location_params}")
                    
                    try:
                        # Extract parameters with defaults
                        search_type = location_params.get("search_type", "grocery_store")
                        location = location_params.get("location", "University of Chicago")
                        radius = location_params.get("radius_meters", 1000)
                        keywords = location_params.get("keywords", [])
                        
                        # Build the query string
                        query = f"{search_type}"
                        if keywords:
                            query = f"{' '.join(keywords)} {query}"
                        
                        # Call Google Maps API with correct parameters
                        places = self.google_maps_api.search_places(
                            query=query,
                            location=location,
                            radius=radius,
                            keywords=keywords if keywords else None,
                            open_now=location_params.get("open_now", False)
                        )
                        
                        if places:
                            api_data["places"] = places
                            response_parts.append(self._format_places_response(places))
                        else:
                            response_parts.append("I couldn't find any places matching your criteria. Would you like to try a broader search?")
                        
                    except Exception as e:
                        logger.error(f"Error processing location search: {str(e)}")
                        response_parts.append("I encountered an error processing your request. Please try again.")
                    
                elif "student_info" in analysis.get("intents", []):
                    student_params = analysis["parameters"]["student_info"]
                    logger.info(f"Processing student info query with params: {student_params}")
                    
                    try:
                        # Get relevant context from conversation
                        context = self.get_conversation_context(user_id, conversation.id)
                        
                        # Build the query with more context
                        query_context = {
                            "topic": student_params.get("topic", ""),
                            "subtopic": student_params.get("subtopic", ""),
                            "visa_type": student_params.get("visa_type", ""),
                            "document_type": student_params.get("document_type", "")
                        }
                        
                        # First try to get relevant documents
                        relevant_docs = self.rag.query(message, n_results=3)
                        
                        if relevant_docs:
                            # Generate response using the documents
                            response = self.rag.generate_response(message, relevant_docs)
                            api_data["rag"] = {
                                "query": message,
                                "context": query_context,
                                "docs": relevant_docs
                            }
                            response_parts.append(response)
                        else:
                            # Try a broader search without specific parameters
                            broader_docs = self.rag.query(message, n_results=1)
                            if broader_docs:
                                response = self.rag.generate_response(message, broader_docs)
                                api_data["rag"] = {
                                    "query": message,
                                    "context": query_context,
                                    "docs": broader_docs
                                }
                                response_parts.append(response)
                            else:
                                response_parts.append("I couldn't find specific information about that. Could you please rephrase your question?")
                        
                    except Exception as e:
                        logger.error(f"Error processing student info query: {str(e)}")
                        response_parts.append("I encountered an error processing your request. Please try again.")
                    
                else:
                    # Handle general conversation with Gemini
                    chat_response = self.gemini_chat.send_message(
                        f"You are a helpful assistant for international students. Respond to: {message}"
                    )
                    response_parts.append(chat_response.text)
                    
            except Exception as tool_error:
                logger.error(f"Error using tools: {str(tool_error)}")
                response_parts.append("I encountered an error processing your request. Please try again.")
            
            # Generate final response
            final_response = " ".join(response_parts) or f"I understand you said: {message}"
            
            # Store assistant response
            assistant_message = Message(
                conversation_id=conversation.id,
                role='assistant',
                content=final_response,
                message_metadata={
                    "timestamp": datetime.utcnow().isoformat(),
                    "analysis": analysis,
                    "api_data": api_data
                }
            )
            db.session.add(assistant_message)
            db.session.commit()
            
            return {
                "success": True,
                "response": final_response,
                "conversation_id": conversation.id
            }
            
        except Exception as e:
            logger.error(f"Error in process_message: {str(e)}", exc_info=True)
            return {"success": False, "error": str(e)}

    def clear_history(self):
        """Clear the conversation history"""
        self.conversation_history = [] 