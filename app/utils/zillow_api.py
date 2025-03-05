import os
import json
import requests
from typing import List, Dict, Any, Optional
from dotenv import load_dotenv
import logging

# Load environment variables
load_dotenv()

class ZillowAPI:
    def __init__(self):
        self.api_key = os.getenv("ZILLOW_API_KEY")
        self.base_url = "https://zillow-com1.p.rapidapi.com"
        self.headers = {
            "X-RapidAPI-Key": self.api_key,
            "X-RapidAPI-Host": "zillow-com1.p.rapidapi.com"
        }

    def search_properties(
        self,
        location: str = "Hyde Park, Chicago",
        min_price: int = 0,
        max_price: int = 5000,
        bedrooms: Optional[int] = None,
        property_type: Optional[str] = None,
        amenities: Optional[List[str]] = None,
        radius: Optional[float] = 1
    ) -> List[Dict[str, Any]]:
        """Search for properties using Zillow API"""
        try:
            logging.info(f"Starting Zillow search for location: {location}")
            logging.debug(f"API Key present: {bool(self.api_key)}")
            logging.debug(f"Headers: {self.headers}")
            
            # Ensure location is in Chicago
            if not location.lower().endswith(('chicago', 'chicago, il')):
                location += ", Chicago, IL"
            
            # Build search parameters
            search_params = {
                "location": location,
                "status_type": "ForRent",
                "home_type": "Apartments",
                "rentMinPrice": min_price,
                "rentMaxPrice": max_price,
                "page": "1"
            }
            
            # Add bedrooms if specified
            if bedrooms is not None:
                search_params["beds_min"] = bedrooms
                search_params["beds_max"] = bedrooms
            
            logging.debug(f"Making Zillow API request with params: {search_params}")
            
            # Make initial search request
            response = requests.get(
                f"{self.base_url}/propertyExtendedSearch",
                headers=self.headers,
                params=search_params
            )
            
            print(f"Zillow API response status: {response.status_code}")  # Debug print
            response.raise_for_status()
            data = response.json()
            print(f"Zillow API response data: {data}")  # Debug print
            
            # Extract properties
            properties = []
            for prop in data.get('props', []):
                property_data = {
                    'address': prop.get('address', 'Unknown Address'),
                    'price': prop.get('price', 'N/A'),
                    'bedrooms': prop.get('bedrooms', 'N/A'),
                    'bathrooms': prop.get('bathrooms', 'N/A'),
                    'availability': 'Available Now',
                    'url': f"https://www.zillow.com{prop.get('detailUrl', '')}",
                    'location': {
                        'lat': prop.get('latitude'),
                        'lng': prop.get('longitude')
                    }
                }
                properties.append(property_data)
            
            return properties[:5]  # Return top 5 properties
            
        except Exception as e:
            print(f"Error searching properties: {str(e)}")
            return []

    def _enrich_properties(self, properties: List[Dict]) -> List[Dict]:
        """Add additional property details"""
        for prop in properties:
            try:
                if not prop.get('detailUrl'):
                    continue
                    
                # Fetch property details
                response = requests.get(
                    f"{self.base_url}/property",
                    headers=self.headers,
                    params={"property_url": prop['detailUrl']}
                )
                if response.status_code == 200:
                    details = response.json()
                    
                    # Add additional information
                    prop.update({
                        'description': details.get('description', 'No description available'),
                        'features': {
                            'hasGarage': details.get('resoFacts', {}).get('hasGarage', 'N/A'),
                            'hasPetsAllowed': details.get('resoFacts', {}).get('hasPetsAllowed', 'N/A'),
                            'heating': details.get('resoFacts', {}).get('heating', 'N/A'),
                            'cooling': details.get('resoFacts', {}).get('cooling', 'N/A'),
                            'laundry': details.get('resoFacts', {}).get('laundryFeatures', 'N/A'),
                            'parkingFeatures': details.get('resoFacts', {}).get('parkingFeatures', 'N/A')
                        }
                    })
                
            except Exception as e:
                print(f"Error enriching property {prop.get('address')}: {str(e)}")
                continue
                
        return properties
