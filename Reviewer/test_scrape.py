import requests
from bs4 import BeautifulSoup

url = "https://www.spharetech.com/products/kamal-kpb0161-160000mah-power-bank"

response = requests.get(url)
print(response)

soup = BeautifulSoup(response.text, 'html.parser')
script_tag = soup.find("script", {"data-page-type": "product"})
print(script_tag)

shop_id = script_tag.get('data-shop-id')
product_id = script_tag.get('data-product-id')

print(shop_id, product_id)
