"""URL builders for Shopify storefront JSON endpoints."""

from __future__ import annotations


def normalize_domain(domain: str) -> str:
    """Normalize a domain to 'https://domain' format.

    Accepts:
        'spharetech.com'
        'www.spharetech.com'
        'https://spharetech.com'
        'https://www.spharetech.com/'
        'store.myshopify.com'
    """
    domain = domain.strip().rstrip('/')
    if domain.startswith('http://') or domain.startswith('https://'):
        return domain.rstrip('/')
    return f'https://{domain}'


def meta_url(base: str) -> str:
    return f'{base}/meta.json'


def products_url(base: str, page: int = 1, limit: int = 250) -> str:
    return f'{base}/products.json?limit={limit}&page={page}'


def product_url(base: str, handle: str) -> str:
    return f'{base}/products/{handle}.json'


def collections_url(base: str) -> str:
    return f'{base}/collections.json'


def collection_products_url(
    base: str, handle: str, page: int = 1, limit: int = 250,
) -> str:
    return f'{base}/collections/{handle}/products.json?limit={limit}&page={page}'


def pages_url(base: str) -> str:
    return f'{base}/pages.json'


def page_url(base: str, handle: str) -> str:
    return f'{base}/pages/{handle}.json'
