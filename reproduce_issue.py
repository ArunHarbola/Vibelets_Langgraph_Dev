import requests
import json

url = "http://127.0.0.1:8001/api/scripts"

product_data = {
    "url": "https://example.com/product",
    "title": "Example Product",
    "description": "This is an example product.",
    "price": "$10.00",
    "images": [],
    "is_store": False,
    "products": [],
    "raw_text": "Example product raw text."
}

analysis = {
    "category": "Gadgets",
    "features": ["Feature 1", "Feature 2"],
    "target_audience": "Tech enthusiasts",
    "usps": "High quality, low price",
    "marketing_angles": "Innovation",
    "positioning": "Premium affordable"
}

payload = {
    "product_data": product_data,
    # "analysis": analysis
}

try:
    response = requests.post(url, json=payload)
    print(f"Status Code: {response.status_code}")
    print(f"Response: {response.text}")
except Exception as e:
    print(f"Error: {e}")
