"""
shopifyscrape — Shopify store scraper SDK.

Quick start::

    from shopifyscrape import Shopify

    shop = Shopify('spharetech.com')
    products = shop.products()
    collections = shop.collections()

"""

from shopifyscrape.client import Shopify
from shopifyscrape.exceptions import (
    CollectionNotFoundError,
    PageNotFoundError,
    ParsingError,
    ProductNotFoundError,
    RateLimitError,
    RequestError,
    ShopifyError,
    StoreNotFoundError,
)
from shopifyscrape.exporter import Exporter
from shopifyscrape.models import (
    Collection,
    CollectionImage,
    Page,
    Product,
    ProductImage,
    ProductOption,
    Store,
    Variant,
)

__version__ = '0.1.0'

__all__ = [
    # Client
    'Shopify',
    # Export
    'Exporter',
    # Exceptions
    'ShopifyError',
    'StoreNotFoundError',
    'CollectionNotFoundError',
    'ProductNotFoundError',
    'PageNotFoundError',
    'RateLimitError',
    'RequestError',
    'ParsingError',
    # Models
    'Store',
    'Product',
    'Variant',
    'ProductImage',
    'ProductOption',
    'Collection',
    'CollectionImage',
    'Page',
]
