from app.utils.zillow_api import ZillowAPI
from app.utils.google_maps_api import GoogleMapsAPI
import json
import requests

def test_zillow_api():
    print("\n=== Testing Zillow API ===")
    zillow = ZillowAPI()
    
    # Print API key (partially masked)
    api_key = zillow.api_key
    masked_key = f"{api_key[:8]}...{api_key[-4:]}" if api_key else "None"
    print(f"Using Zillow API Key: {masked_key}")
    
    housing_params = {
        "location": "Hyde Park, Chicago, IL",
        "status_type": "ForRent",
        "home_type": "Apartments",
        "rentMinPrice": 1000,
        "rentMaxPrice": 2000,
        "page": "1"
    }
    
    try:
        # Test raw API request first
        print("\nTesting direct API request...")
        response = requests.get(
            "https://zillow-com1.p.rapidapi.com/propertyExtendedSearch",
            headers=zillow.headers,
            params=housing_params
        )
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.text[:500]}...")  # Print first 500 chars
        
        # Test the search_properties method
        print("\nTesting search_properties method...")
        properties = zillow.search_properties(json.dumps(housing_params))
        print(f"Found {len(properties)} properties")
        if properties:
            print(f"\nFound {len(properties)} properties:")
            for i, prop in enumerate(properties, 1):
                print(f"\nProperty {i}:")
                print(f"Address: {prop['address']}")
                print(f"Price: {prop['price']}")
                print(f"Bedrooms: {prop['bedrooms']}")
                print(f"URL: {prop['detailUrl']}")
                if 'features' in prop:
                    print("Features:")
                    for feature, value in prop['features'].items():
                        print(f"  {feature}: {value}")
            
    except Exception as e:
        print(f"Error: {str(e)}")

def test_google_maps_api():
    print("\n=== Testing Google Maps API ===")
    maps = GoogleMapsAPI()
    
    # Print API key (partially masked)
    api_key = maps.api_key
    masked_key = f"{api_key[:8]}...{api_key[-4:]}" if api_key else "None"
    print(f"Using Google Maps API Key: {masked_key}")
    
    # Test geocoding first
    print("\nTesting Geocoding...")
    try:
        coords = maps._get_location_coordinates("University of Chicago")
        print(f"Coordinates: {coords}")
        
        # Test places search
        print("\nTesting Places Search...")
        places_params = {
            "location": "University of Chicago",
            "type": "restaurant",
            "radius": 1000
        }
        
        # Test raw API request first
        base_url = "https://maps.googleapis.com/maps/api/place/nearbysearch/json"
        search_params = {
            "key": maps.api_key,
            "location": f"{coords['lat']},{coords['lng']}",
            "radius": 1000,
            "type": "restaurant"
        }
        
        print("\nTesting direct API request...")
        response = requests.get(base_url, params=search_params)
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.text[:500]}...")  # Print first 500 chars
        
        # Test the search_places method
        print("\nTesting search_places method...")
        places = maps.search_places(json.dumps(places_params))
        print(f"Found {len(places)} places")
        if places:
            print("\nFirst place:")
            print(json.dumps(places[0], indent=2))
            
    except Exception as e:
        print(f"Error: {str(e)}")

if __name__ == "__main__":
    test_zillow_api()
    test_google_maps_api() 