    # shopifyscrape

Scrape any Shopify store — products, collections, pages & metadata from the public JSON API. No API key required.

**Three interfaces:** Python SDK, CLI, and REST API.

## Installation

```bash
# Core SDK only
pip install shopifyscrape

# With CLI (click + rich tables)
pip install shopifyscrape[cli]

# With REST API (FastAPI + uvicorn)
pip install shopifyscrape[api]

# Everything
pip install shopifyscrape[all]
```

## Quick Start

```python
from shopifyscrape import Shopify

shop = Shopify('spharetech.com')

# Store metadata
store = shop.store()
print(store.name, store.currency)

# All products (auto-paginated)
products = shop.products()
for p in products:
    print(p.title, p.price, p.available)

# All collections
collections = shop.collections()
for c in collections:
    print(c.title, c.products_count)

# Products in a specific collection
power_banks = shop.collection_products('power-banks')

# Single product
product = shop.product('66w-transparent-power-bank-20000mah')

# Pages
pages = shop.pages()
```

## Pagination

Fetch everything at once or paginate manually — your choice.

```python
shop = Shopify('spharetech.com')

# Auto-paginate: fetches ALL products in one call
all_products = shop.products()

# Manual pagination: fetch one page at a time
page1 = shop.products_page(page=1, limit=30)
page2 = shop.products_page(page=2, limit=30)

# Same for collection products
all_power_banks = shop.collection_products('power-banks')
first_page = shop.collection_products_page('power-banks', page=1, limit=10)
```

## Exporting

```python
from shopifyscrape import Exporter, Shopify

shop = Shopify('spharetech.com')
products = shop.products()

exporter = Exporter(output_dir='output')
exporter.products_to_json(products)
exporter.products_to_csv(products)
```

## Proxy Support

```python
shop = Shopify('store.com', proxy='http://user:pass@host:port')
```

## CLI

```bash
# Scrape products
shopifyscrape products spharetech.com
shopifyscrape products spharetech.com --collection power-banks
shopifyscrape products spharetech.com --json
shopifyscrape products spharetech.com --save products.csv

# Scrape collections
shopifyscrape collections spharetech.com

# Store metadata
shopifyscrape store spharetech.com

# With proxy
shopifyscrape --proxy http://host:port products spharetech.com
```

## REST API

```bash
# Start the API server
shopifyscrape serve
shopifyscrape serve --port 3000
```

### Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/products?domain=store.com` | All products |
| GET | `/api/v1/products?domain=store.com&collection=power-banks` | Collection products |
| GET | `/api/v1/products/{handle}?domain=store.com` | Single product |
| GET | `/api/v1/collections?domain=store.com` | All collections |
| GET | `/api/v1/store?domain=store.com` | Store metadata |
| GET | `/api/v1/pages?domain=store.com` | All pages |
| GET | `/health` | Health check |

Interactive docs at `http://localhost:8000/docs`

## Error Handling

```python
from shopifyscrape import Shopify, StoreNotFoundError, ProductNotFoundError

shop = Shopify('not-a-shopify-store.com')
try:
    store = shop.store()
except StoreNotFoundError:
    print('Not a Shopify store')

try:
    product = shop.product('nonexistent')
except ProductNotFoundError:
    print('Product not found')
```

## Exception Hierarchy

```
ShopifyError
├── StoreNotFoundError
├── ProductNotFoundError
├── CollectionNotFoundError
├── PageNotFoundError
├── RateLimitError
├── RequestError
└── ParsingError
```

## Data Models

| Model | Description |
|-------|-------------|
| `Store` | Store metadata (name, currency, counts) |
| `Product` | Product with variants, images, options |
| `Variant` | Pricing, stock, SKU, weight |
| `ProductImage` | Image URL with dimensions |
| `ProductOption` | Option name and values |
| `Collection` | Collection with image and product count |
| `Page` | Static page content |

All models have a `.to_dict()` method for serialization.

## License

MIT
