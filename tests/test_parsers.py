"""Tests for response parsers."""

from shopifyscrape._parsers import parse_collections, parse_products, parse_store


class TestParseStore:
    def test_basic(self):
        data = {
            'id': 123,
            'name': 'Test Store',
            'domain': 'test.com',
            'url': 'https://test.com',
            'myshopify_domain': 'test.myshopify.com',
            'country': 'US',
            'currency': 'USD',
            'money_format': '${{amount}}',
            'published_products_count': 10,
            'published_collections_count': 3,
        }
        store = parse_store(data)
        assert store.name == 'Test Store'
        assert store.currency == 'USD'
        assert store.published_products_count == 10


class TestParseProducts:
    def test_empty(self):
        assert parse_products({'products': []}) == []

    def test_single_product(self):
        data = {
            'products': [{
                'id': 1,
                'title': 'Test Product',
                'handle': 'test-product',
                'vendor': 'TestVendor',
                'product_type': '',
                'body_html': '<p>Description</p>',
                'published_at': '2026-01-01',
                'updated_at': '2026-01-02',
                'tags': ['tag1'],
                'variants': [{
                    'id': 10,
                    'title': 'Default Title',
                    'price': '29.99',
                    'compare_at_price': '49.99',
                    'available': True,
                }],
                'images': [{
                    'id': 100,
                    'src': 'https://cdn.shopify.com/image.jpg',
                    'width': 500,
                    'height': 500,
                    'position': 1,
                }],
                'options': [{
                    'name': 'Title',
                    'position': 1,
                    'values': ['Default Title'],
                }],
            }],
        }
        products = parse_products(data)
        assert len(products) == 1
        assert products[0].title == 'Test Product'
        assert products[0].variants[0].price == '29.99'
        assert products[0].images[0].src == 'https://cdn.shopify.com/image.jpg'


class TestParseCollections:
    def test_empty(self):
        assert parse_collections({'collections': []}) == []

    def test_with_image(self):
        data = {
            'collections': [{
                'id': 1,
                'title': 'Test Collection',
                'handle': 'test',
                'description': 'A collection',
                'published_at': '2026-01-01',
                'updated_at': '2026-01-02',
                'products_count': 5,
                'image': {
                    'id': 10,
                    'src': 'https://cdn.shopify.com/col.jpg',
                    'alt': None,
                },
            }],
        }
        cols = parse_collections(data)
        assert len(cols) == 1
        assert cols[0].products_count == 5
        assert cols[0].image is not None
        assert cols[0].image.src == 'https://cdn.shopify.com/col.jpg'
