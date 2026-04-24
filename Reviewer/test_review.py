import requests

data = '{"content":"value for money powerbank h fast charging b h type c port se  or is price tag mn best h  khud b jalde charge hojata h design b unique h must buy👍 doosre stores se kaafi mehenga mil rha but yahan se achi price mn mila ir cheez b blkl new h 💯💯","author":"Maghaz Khan","author_email":"maghaz134@gmail.com","author_country":"PK","resources":[],"product_id":9309304946934,"shop_id":79801712886,"rating":5}'

response = requests.post(
    'https://www.spharetech.com/apps/trustoo/api/v1/reviews/add_review_via_shopify',
    data=data,
)
print(response.status_code)
print(response.text)