import requests
import json

# Test WITHOUT author_country field
data_no_country = {
    "content": "Excellent power bank, charges my phone 3 times on a single charge. Build quality is solid and the LED display showing battery percentage is very helpful. Delivery was fast too. Highly recommend for anyone looking for a reliable power bank.",
    "author": "Hamza Tariq",
    "author_email": "hamzatariq99@gmail.com",
    "resources": [],
    "product_id": 9309304946934,
    "shop_id": 79801712886,
    "rating": 5
}

print("=== Test WITHOUT author_country ===")
response = requests.post(
    'https://www.spharetech.com/apps/trustoo/api/v1/reviews/add_review_via_shopify',
    data=json.dumps(data_no_country),
    headers={"Content-Type": "text/plain;charset=UTF-8"}
)
print(f"Status: {response.status_code}")
print(f"Response: {response.text}")
