# Changelog

## v0.2.2 (2026-04-24)

- Fix crash when Trustoo API returns `null` for `total_rating` or `data` (products with no reviews)

## v0.2.1 (2026-04-24)

### New Features

- **Review scraping** - Fetch product reviews from Shopify stores using the Trustoo reviews integration
  - `shop.reviews(product_id)` - Fetch reviews for a specific product (paginated)
  - `shop.review_count(product_id)` - Get review count for a product (efficient, single API call)
  - `shop.shop_id()` - Get the store's shop_id from store metadata via `store().id`
- **New models** - `Review` and `ReviewSummary` dataclasses with `to_dict()` support

### Usage

```python
from shopscout import Shopify

shop = Shopify('spharetech.com')

# Get shop_id from store metadata
sid = shop.shop_id()

# Fetch reviews for a product
reviews, summary = shop.reviews(product_id=9309304946934)
print(f"Total: {summary.total_reviews}, Avg: {summary.average_rating}")
for r in reviews:
    print(f"  {r.author} ({r.rating} stars): {r.content[:50]}")

# Just get the count (fast)
count = shop.review_count(product_id=9309304946934)
```

### Dependencies

- Added `beautifulsoup4>=4.12` as a core dependency

---

## v0.1.2 (2026-03-28)

- Fix CI: add types-requests to dev dependencies
- Add CI/CD workflows and fix lint issues

## v0.1.1 (2026-03-28)

- Update PyPI description and README with shopscout branding

## v0.1.0 (2026-03-11)

- Initial release
- Scrape products, collections, pages, and store metadata
- Python SDK, CLI, and REST API interfaces
- Proxy support
- CSV and JSON export
