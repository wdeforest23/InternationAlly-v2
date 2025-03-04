import os
import json
import requests
from typing import List, Dict, Any, Optional
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Get API key from environment
GOOGLE_MAPS_API_KEY = os.getenv("GOOGLE_MAPS_API_KEY")

def search_places(params_str: str) -> List[Dict[str, Any]]:
    """
    Search for places using the Google Maps API
    
    Args:
        params_str: JSON string with search parameters
            - location: The city or neighborhood
            - place_type: Type of place (restaurant, grocery, etc.)
            - radius: Search radius in meters (default 1000)
    
    Returns:
        List of place data dictionaries
    """
    # Parse the parameters
    try:
        params = json.loads(params_str)
    except json.JSONDecodeError:
        # If the string is not valid JSON, try to extract parameters manually
        params = extract_params_manually(params_str)
    
    # Get location coordinates
    location_coords = get_location_coordinates(params.get("location", "Chicago"))
    
    # Set up the API request
    url = "https://maps.googleapis.com/maps/api/place/nearbysearch/json"
    
    # Build query parameters
    query_params = {
        "location": f"{location_coords['lat']},{location_coords['lng']}",
        "radius": params.get("radius", 1000),
        "type": params.get("place_type", "restaurant"),
        "key": GOOGLE_MAPS_API_KEY
    }
    
    # Make the API request
    try:
        response = requests.get(url, params=query_params)
        response.raise_for_status()  # Raise an exception for HTTP errors
        
        # Parse the response
        data = response.json()
        
        # Extract and format place data
        places = []
        for place in data.get("results", [])[:10]:  # Limit to 10 places
            # Extract coordinates for mapping
            location = {
                "lat": place.get("geometry", {}).get("location", {}).get("lat", location_coords["lat"]),
                "lng": place.get("geometry", {}).get("location", {}).get("lng", location_coords["lng"])
            }
            
            # Create place object
            place_data = {
                "id": place.get("place_id", ""),
                "name": place.get("name", ""),
                "address": place.get("vicinity", ""),
                "rating": place.get("rating", 0),
                "user_ratings_total": place.get("user_ratings_total", 0),
                "price_level": place.get("price_level", 0),
                "types": place.get("types", []),
                "open_now": place.get("opening_hours", {}).get("open_now", False),
                "photos": place.get("photos", []),
                "location": location
            }
            
            places.append(place_data)
        
        return places
    
    except requests.RequestException as e:
        # If we're in development or testing mode, return mock data
        if os.getenv("FLASK_ENV") == "development" or not GOOGLE_MAPS_API_KEY:
            return get_mock_places(params)
        
        # Otherwise, raise the exception
        raise Exception(f"Error fetching place data: {str(e)}")

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
