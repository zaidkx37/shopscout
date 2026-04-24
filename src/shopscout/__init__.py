"""
shopscout - Shopify store scraper SDK.

Quick start::

    from shopscout import Shopify

    shop = Shopify('spharetech.com')
    products = shop.products()
    collections = shop.collections()

"""

from shopscout.client import Shopify
from shopscout.exceptions import (
    CollectionNotFoundError,
    PageNotFoundError,
    ParsingError,
    ProductNotFoundError,
    RateLimitError,
    RequestError,
    ShopifyError,
    StoreNotFoundError,
)
from shopscout.exporter import Exporter
from shopscout.models import (
    Collection,
    CollectionImage,
    Page,
    Product,
    ProductImage,
    ProductOption,
    Review,
    ReviewSummary,
    Store,
    Variant,
)

__version__ = '0.1.2'

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
    'Review',
    'ReviewSummary',
]
