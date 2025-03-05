import os
import json
import requests
from typing import List, Dict, Any, Optional
from dotenv import load_dotenv
import logging

# Load environment variables
load_dotenv()

# Get API key from environment
GOOGLE_MAPS_API_KEY = os.getenv("GOOGLE_API_KEY")

class GoogleMapsAPI:
    def __init__(self):
        self.api_key = os.getenv("GOOGLE_API_KEY")
        self.base_url = "https://maps.googleapis.com/maps/api"

    def search_places(
        self,
        query: str,
        location: str,
        radius: int = 1000,
        keywords: Optional[List[str]] = None,
        open_now: bool = False
    ) -> List[Dict[str, Any]]:
        """Search for places using Google Maps API"""
        try:
            logging.info(f"Starting Google Maps search with query: {query}")
            logging.debug(f"API Key present: {bool(self.api_key)}")
            
            # Get coordinates for the location
            coords = self._get_location_coordinates(location)
            logging.debug(f"Coordinates for {location}: {coords}")
            if not coords:
                return []
            
            # Build search parameters
            search_params = {
                "key": self.api_key,
                "location": f"{coords['lat']},{coords['lng']}",
                "radius": radius,
                "keyword": query
            }
            
            if keywords:
                search_params["keyword"] = " ".join([query] + keywords)
            
            if open_now:
                search_params["opennow"] = "true"
            
            logging.debug(f"Making Google Maps API request with params: {search_params}")
            
            response = requests.get(self.base_url + "/place/nearbysearch/json", params=search_params)
            print(f"Google Maps API response status: {response.status_code}")  # Debug print
            
            if response.status_code != 200:
                print(f"Error response: {response.text}")
                return []
                
            data = response.json()
            if "error_message" in data:
                print(f"API Error: {data['error_message']}")
                return []
                
            results = data.get("results", [])
            return self._format_places(results)
            
        except Exception as e:
            print(f"Error searching places: {str(e)}")
            return []

    def _get_location_coordinates(self, location: str) -> Dict[str, float]:
        """Get coordinates for a location"""
        try:
            params = {
                "address": location,
                "key": self.api_key
            }
            
            response = requests.get(
                f"{self.base_url}/geocode/json",
                params=params
            )
            response.raise_for_status()
            
            result = response.json()
            if result["results"]:
                location = result["results"][0]["geometry"]["location"]
                return location
            
            # Default to UChicago coordinates
            return {"lat": 41.7886, "lng": -87.5987}
            
        except Exception as e:
            print(f"Error getting coordinates: {str(e)}")
            return {"lat": 41.7886, "lng": -87.5987}

    def _format_places(self, places: List[Dict]) -> List[Dict]:
        """Format place results with additional information"""
        formatted_places = []
        
        for place in places[:5]:  # Limit to top 5 places
            formatted_place = {
                "name": place.get("name", ""),
                "address": place.get("vicinity", ""),
                "rating": place.get("rating", 0),
                "user_ratings": place.get("user_ratings_total", 0),
                "types": place.get("types", []),
                "location": place.get("geometry", {}).get("location", {}),
                "place_id": place.get("place_id", ""),
                "google_maps_link": f"https://www.google.com/maps/place/?q=place_id:{place.get('place_id', '')}"
            }
            
            # Add photo reference if available
            if place.get("photos"):
                photo_ref = place["photos"][0]["photo_reference"]
                formatted_place["photo_url"] = (
                    f"{self.base_url}/place/photo"
                    f"?maxwidth=400&photo_reference={photo_ref}&key={self.api_key}"
                )
            
            formatted_places.append(formatted_place)
            
        return formatted_places

def get_location_coordinates(location: str) -> Dict[str, float]:
    """
    Get coordinates for a location using the Google Maps Geocoding API
    
    Args:
        location: The city or neighborhood
    
    Returns:
        Dictionary with lat and lng keys
    """
    # Set up the API request
    url = "https://maps.googleapis.com/maps/api/geocode/json"
    
    # Build query parameters
    query_params = {
        "address": location,
        "key": GOOGLE_MAPS_API_KEY
    }
    
    # Make the API request
    try:
        response = requests.get(url, params=query_params)
        response.raise_for_status()  # Raise an exception for HTTP errors
        
        # Parse the response
        data = response.json()
        
        # Extract coordinates
        if data.get("results"):
            location = data["results"][0]["geometry"]["location"]
            return {
                "lat": location["lat"],
                "lng": location["lng"]
            }
        else:
            # Default to Chicago
            return {"lat": 41.8781, "lng": -87.6298}
    
    except requests.RequestException:
        # Default to Chicago
        return {"lat": 41.8781, "lng": -87.6298}

def extract_params_manually(params_str: str) -> Dict[str, Any]:
    """
    Extract search parameters manually from a string
    
    Args:
        params_str: String with search parameters
    
    Returns:
        Dictionary of parameters
    """
    params = {}
    
    # Try to extract location
    if "in" in params_str.lower():
        location_parts = params_str.lower().split("in")
        if len(location_parts) > 1:
            location = location_parts[1].strip().split(" ")[0]
            params["location"] = location
    else:
        # Default to Chicago
        params["location"] = "Chicago"
    
    # Try to extract place type
    place_types = {
        "restaurant": "restaurant",
        "cafe": "cafe",
        "coffee": "cafe",
        "grocery": "grocery_or_supermarket",
        "supermarket": "grocery_or_supermarket",
        "store": "store",
        "shop": "store",
        "bank": "bank",
        "atm": "atm",
        "hospital": "hospital",
        "clinic": "doctor",
        "doctor": "doctor",
        "pharmacy": "pharmacy",
        "drugstore": "pharmacy",
        "school": "school",
        "university": "university",
        "college": "university",
        "library": "library",
        "park": "park",
        "gym": "gym",
        "fitness": "gym",
        "transit": "transit_station",
        "bus": "bus_station",
        "train": "train_station",
        "subway": "subway_station",
        "airport": "airport",
        "hotel": "lodging",
        "lodging": "lodging",
        "gas": "gas_station",
        "gas station": "gas_station",
        "police": "police",
        "post office": "post_office",
        "mall": "shopping_mall",
        "shopping": "shopping_mall"
    }
    
    for key, value in place_types.items():
        if key in params_str.lower():
            params["place_type"] = value
            break
    
    # Try to extract radius
    radius_keywords = ["within", "radius", "distance", "miles", "kilometers", "km", "mi"]
    for keyword in radius_keywords:
        if keyword in params_str.lower():
            # Look for numbers before the keyword
            parts = params_str.lower().split(keyword)
            if len(parts) > 1:
                number_part = parts[0].strip().split(" ")[-1]
                if number_part.isdigit():
                    number = int(number_part)
                    # Convert to meters
                    if "mile" in keyword:
                        params["radius"] = number * 1609  # miles to meters
                    elif "km" in keyword or "kilometer" in keyword:
                        params["radius"] = number * 1000  # km to meters
                    else:
                        params["radius"] = number
    
    return params

def get_mock_places(params: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Get mock place data for development and testing
    
    Args:
        params: Dictionary of search parameters
    
    Returns:
        List of mock place data dictionaries
    """
    location = params.get("location", "Chicago")
    place_type = params.get("place_type", "restaurant")
    
    # Set default coordinates based on location
    if location.lower() == "chicago":
        base_lat, base_lng = 41.8781, -87.6298
    elif location.lower() == "new york":
        base_lat, base_lng = 40.7128, -74.0060
    elif location.lower() == "los angeles":
        base_lat, base_lng = 34.0522, -118.2437
    else:
        base_lat, base_lng = 41.8781, -87.6298  # Default to Chicago
    
    # Generate mock places
    mock_places = []
    
    # Define place names based on type
    place_names = {
        "restaurant": ["Delicious Eats", "Tasty Bites", "Gourmet Kitchen", "Flavor Fusion", "Savory Spot"],
        "cafe": ["Coffee Corner", "Brew House", "Bean & Leaf", "Morning Cup", "Espresso Express"],
        "grocery_or_supermarket": ["Fresh Market", "Daily Grocers", "Food Emporium", "Super Foods", "Market Place"],
        "bank": ["City Bank", "Financial Trust", "Money Matters", "Secure Savings", "Capital Credit"],
        "hospital": ["Care Center", "Wellness Hospital", "Health Haven", "Medical Center", "Healing Hands"],
        "school": ["Learning Academy", "Knowledge School", "Education Center", "Scholars Institute", "Study Hall"],
        "park": ["Green Meadows", "Sunset Park", "Riverside Gardens", "Central Commons", "Nature Retreat"],
        "gym": ["Fitness First", "Power Gym", "Strength Studio", "Active Athletics", "Muscle Mansion"],
        "transit_station": ["Central Station", "Metro Hub", "Transit Center", "City Terminal", "Transport Exchange"],
        "lodging": ["Comfort Inn", "Restful Retreat", "Cozy Quarters", "Sleep Well Hotel", "Dream Lodge"]
    }
    
    # Use default names if place type not found
    names = place_names.get(place_type, ["Local Business", "City Service", "Community Center", "Public Facility", "Neighborhood Spot"])
    
    for i in range(5):
        # Vary the coordinates slightly
        lat_offset = (i - 2) * 0.01
        lng_offset = (i - 2) * 0.01
        
        # Create place object
        place_data = {
            "id": f"mock-place-{i}",
            "name": names[i],
            "address": f"{100 + i} Main St, {location}",
            "rating": 3.5 + (i * 0.3),
            "user_ratings_total": 50 + (i * 20),
            "price_level": (i % 3) + 1,
            "types": [place_type],
            "open_now": i % 2 == 0,
            "photos": [],
            "location": {"lat": base_lat + lat_offset, "lng": base_lng + lng_offset}
        }
        
        mock_places.append(place_data)
    
    return mock_places
