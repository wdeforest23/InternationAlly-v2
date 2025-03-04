import os
import json
import requests
from typing import List, Dict, Any, Optional
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Get API key from environment
ZILLOW_API_KEY = os.getenv("ZILLOW_API_KEY")

def search_properties(params_str: str) -> List[Dict[str, Any]]:
    """
    Search for properties using the Zillow API
    
    Args:
        params_str: JSON string with search parameters
            - location: The city or neighborhood
            - min_price: Minimum price (if specified)
            - max_price: Maximum price (if specified)
            - bedrooms: Number of bedrooms (if specified)
            - property_type: Type of property (apartment, house, etc.)
    
    Returns:
        List of property data dictionaries
    """
    # Parse the parameters
    try:
        params = json.loads(params_str)
    except json.JSONDecodeError:
        # If the string is not valid JSON, try to extract parameters manually
        params = extract_params_manually(params_str)
    
    # Set up the API request
    url = "https://zillow-com1.p.rapidapi.com/propertyExtendedSearch"
    
    # Build query parameters
    query_params = {
        "location": params.get("location", "Chicago"),
        "home_type": params.get("property_type", "Apartment")
    }
    
    # Add optional parameters if provided
    if "min_price" in params:
        query_params["price_min"] = params["min_price"]
    if "max_price" in params:
        query_params["price_max"] = params["max_price"]
    if "bedrooms" in params:
        query_params["beds_min"] = params["bedrooms"]
    
    # Set up headers
    headers = {
        "X-RapidAPI-Key": ZILLOW_API_KEY,
        "X-RapidAPI-Host": "zillow-com1.p.rapidapi.com"
    }
    
    # Make the API request
    try:
        response = requests.get(url, headers=headers, params=query_params)
        response.raise_for_status()  # Raise an exception for HTTP errors
        
        # Parse the response
        data = response.json()
        
        # Extract and format property data
        properties = []
        for prop in data.get("props", [])[:10]:  # Limit to 10 properties
            # Extract coordinates for mapping
            try:
                latitude = float(prop.get("latitude", 0))
                longitude = float(prop.get("longitude", 0))
                location = {"lat": latitude, "lng": longitude}
            except (ValueError, TypeError):
                location = {"lat": 41.8781, "lng": -87.6298}  # Default to Chicago
            
            # Create property object
            property_data = {
                "id": prop.get("zpid", ""),
                "address": prop.get("address", {}).get("streetAddress", ""),
                "city": prop.get("address", {}).get("city", ""),
                "state": prop.get("address", {}).get("state", ""),
                "zipcode": prop.get("address", {}).get("zipcode", ""),
                "price": prop.get("price", ""),
                "bedrooms": prop.get("bedrooms", ""),
                "bathrooms": prop.get("bathrooms", ""),
                "living_area": prop.get("livingArea", ""),
                "property_type": prop.get("propertyType", ""),
                "year_built": prop.get("yearBuilt", ""),
                "url": prop.get("detailUrl", ""),
                "location": location
            }
            
            properties.append(property_data)
        
        return properties
    
    except requests.RequestException as e:
        # If we're in development or testing mode, return mock data
        if os.getenv("FLASK_ENV") == "development" or not ZILLOW_API_KEY:
            return get_mock_properties(params)
        
        # Otherwise, raise the exception
        raise Exception(f"Error fetching property data: {str(e)}")

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
    
    # Try to extract price range
    if "$" in params_str:
        price_parts = params_str.split("$")
        if len(price_parts) > 1:
            price_text = price_parts[1]
            price_value = ""
            for char in price_text:
                if char.isdigit() or char == ",":
                    price_value += char
                else:
                    break
            
            price_value = price_value.replace(",", "")
            if price_value:
                if "max" in params_str.lower() or "under" in params_str.lower() or "less than" in params_str.lower():
                    params["max_price"] = price_value
                elif "min" in params_str.lower() or "over" in params_str.lower() or "more than" in params_str.lower():
                    params["min_price"] = price_value
                else:
                    # Assume it's a target price, set a range around it
                    price = int(price_value)
                    params["min_price"] = int(price * 0.8)
                    params["max_price"] = int(price * 1.2)
    
    # Try to extract bedrooms
    bedroom_keywords = ["bedroom", "bed", "br", "bdr"]
    for keyword in bedroom_keywords:
        if keyword in params_str.lower():
            for i in range(1, 6):  # Check for 1-5 bedrooms
                if f"{i} {keyword}" in params_str.lower() or f"{i}-{keyword}" in params_str.lower():
                    params["bedrooms"] = i
                    break
    
    # Try to extract property type
    property_types = {
        "apartment": "Apartment", 
        "house": "SingleFamily",
        "condo": "Condo",
        "townhouse": "Townhouse"
    }
    
    for key, value in property_types.items():
        if key in params_str.lower():
            params["property_type"] = value
            break
    
    return params

def get_mock_properties(params: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Get mock property data for development and testing
    
    Args:
        params: Dictionary of search parameters
    
    Returns:
        List of mock property data dictionaries
    """
    location = params.get("location", "Chicago")
    
    # Set default coordinates based on location
    if location.lower() == "chicago":
        base_lat, base_lng = 41.8781, -87.6298
    elif location.lower() == "new york":
        base_lat, base_lng = 40.7128, -74.0060
    elif location.lower() == "los angeles":
        base_lat, base_lng = 34.0522, -118.2437
    else:
        base_lat, base_lng = 41.8781, -87.6298  # Default to Chicago
    
    # Generate mock properties
    mock_properties = []
    for i in range(5):
        # Vary the coordinates slightly
        lat_offset = (i - 2) * 0.01
        lng_offset = (i - 2) * 0.01
        
        # Set price based on parameters
        min_price = int(params.get("min_price", 1000))
        max_price = int(params.get("max_price", 3000))
        price_range = max_price - min_price
        price = min_price + (i * price_range // 5)
        
        # Set bedrooms based on parameters
        bedrooms = params.get("bedrooms", i % 3 + 1)
        
        property_data = {
            "id": f"mock-{i}",
            "address": f"{100 + i} Main St",
            "city": location,
            "state": "IL" if location.lower() == "chicago" else "NY" if location.lower() == "new york" else "CA",
            "zipcode": f"6060{i}",
            "price": f"${price:,}",
            "bedrooms": bedrooms,
            "bathrooms": (i % 2) + 1,
            "living_area": f"{700 + i * 100} sqft",
            "property_type": params.get("property_type", "Apartment"),
            "year_built": 2000 + i,
            "url": "https://www.zillow.com/",
            "location": {"lat": base_lat + lat_offset, "lng": base_lng + lng_offset}
        }
        
        mock_properties.append(property_data)
    
    return mock_properties
