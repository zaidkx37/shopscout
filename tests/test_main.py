from shopifyscrape import Shopify
import json

shop = Shopify('spharetech.com')
products = shop.products()
for p in products:
    for img in p.images:
        print(img.src)
