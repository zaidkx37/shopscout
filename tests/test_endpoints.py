"""Tests for URL builders."""

from shopifyscrape._endpoints import (
    collection_products_url,
    collections_url,
    meta_url,
    normalize_domain,
    pages_url,
    product_url,
    products_url,
)


class TestNormalizeDomain:
    def test_plain_domain(self):
        assert normalize_domain('spharetech.com') == 'https://spharetech.com'

    def test_www_domain(self):
        assert normalize_domain('www.spharetech.com') == 'https://www.spharetech.com'

    def test_https_domain(self):
        assert normalize_domain('https://spharetech.com') == 'https://spharetech.com'

    def test_trailing_slash(self):
        assert normalize_domain('https://spharetech.com/') == 'https://spharetech.com'

    def test_myshopify_domain(self):
        assert normalize_domain('store.myshopify.com') == 'https://store.myshopify.com'


class TestURLBuilders:
    BASE = 'https://spharetech.com'

    def test_meta_url(self):
        assert meta_url(self.BASE) == 'https://spharetech.com/meta.json'

    def test_products_url(self):
        assert products_url(self.BASE) == 'https://spharetech.com/products.json?limit=250&page=1'

    def test_products_url_page2(self):
        url = products_url(self.BASE, page=2, limit=50)
        assert url == 'https://spharetech.com/products.json?limit=50&page=2'

    def test_product_url(self):
        url = product_url(self.BASE, 'test-product')
        assert url == 'https://spharetech.com/products/test-product.json'

    def test_collections_url(self):
        assert collections_url(self.BASE) == 'https://spharetech.com/collections.json'

    def test_collection_products_url(self):
        url = collection_products_url(self.BASE, 'power-banks')
        assert url == 'https://spharetech.com/collections/power-banks/products.json?limit=250&page=1'

    def test_pages_url(self):
        assert pages_url(self.BASE) == 'https://spharetech.com/pages.json'
