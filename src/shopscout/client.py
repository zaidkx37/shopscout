"""Main Shopify client - public entry point for shopscout."""

from __future__ import annotations

import logging

from shopscout._endpoints import (
    collection_products_url,
    collections_url,
    meta_url,
    normalize_domain,
    page_url,
    pages_url,
    product_url,
    products_url,
)
from shopscout._http import HTTPClient
from shopscout._parsers import (
    parse_collections,
    parse_page,
    parse_pages,
    parse_product,
    parse_products,
    parse_store,
)
from shopscout.exceptions import (
    CollectionNotFoundError,
    PageNotFoundError,
    ProductNotFoundError,
    RequestError,
    StoreNotFoundError,
)
from shopscout.models import Collection, Page, Product, Store

logger = logging.getLogger('shopscout')


class Shopify:
    """Scrape any Shopify store's public JSON endpoints.

    No API key or authentication required. Works with any Shopify store
    that has the public ``.json`` endpoints enabled (most stores do).

    Args:
        domain: Store domain (e.g. ``'spharetech.com'``, ``'store.myshopify.com'``).
                Accepts with or without ``https://`` and ``www.`` prefix.
        proxy: Optional proxy URL (e.g. ``'http://user:pass@host:port'``).
        timeout: Request timeout in seconds.
        max_retries: Maximum retry attempts on transient failures.

    Examples::

        shop = Shopify('spharetech.com')
        products = shop.products()
        collections = shop.collections()

        # With proxy
        shop = Shopify('store.myshopify.com', proxy='http://user:pass@host:8080')
    """

    def __init__(
        self,
        domain: str,
        proxy: str | None = None,
        timeout: float = 30.0,
        max_retries: int = 3,
    ) -> None:
        self._base = normalize_domain(domain)
        self._domain = domain
        self._http = HTTPClient(
            proxy=proxy,
            timeout=timeout,
            max_retries=max_retries,
        )

    def _get_json(self, url: str) -> dict:
        """Fetch a URL and return parsed JSON."""
        response = self._http.get(url)
        return response.json()

    # ── Store ──

    def store(self) -> Store:
        """Fetch store metadata.

        Returns:
            Store object with name, currency, product count, etc.

        Raises:
            StoreNotFoundError: If the domain is not a Shopify store.
        """
        try:
            data = self._get_json(meta_url(self._base))
        except RequestError:
            raise StoreNotFoundError(self._domain) from None
        return parse_store(data)

    # ── Products ──

    def products(self, limit: int = 250) -> list[Product]:
        """Fetch all products from the store, auto-paginating.

        Args:
            limit: Products per page (max 250). Pagination is automatic.

        Returns:
            List of all Product objects in the store.
        """
        all_products: list[Product] = []
        page = 1

        while True:
            url = products_url(self._base, page=page, limit=limit)
            data = self._get_json(url)
            batch = parse_products(data)
            if not batch:
                break
            all_products.extend(batch)
            if len(batch) < limit:
                break
            page += 1

        logger.info('Fetched %d products from %s', len(all_products), self._domain)
        return all_products

    def products_page(self, page: int = 1, limit: int = 30) -> list[Product]:
        """Fetch a single page of products (no auto-pagination).

        Args:
            page: Page number (1-indexed).
            limit: Products per page (1-250).

        Returns:
            List of Product objects for that page. Empty list if no more pages.
        """
        url = products_url(self._base, page=page, limit=limit)
        data = self._get_json(url)
        return parse_products(data)

    def product(self, handle: str) -> Product:
        """Fetch a single product by handle.

        Args:
            handle: Product URL slug (e.g. ``'66w-transparent-power-bank-20000mah'``).

        Returns:
            Product object.

        Raises:
            ProductNotFoundError: If the product handle doesn't exist.
        """
        try:
            data = self._get_json(product_url(self._base, handle))
        except RequestError:
            raise ProductNotFoundError(handle) from None
        return parse_product(data.get('product', data))

    # ── Collections ──

    def collections(self) -> list[Collection]:
        """Fetch all collections from the store.

        Returns:
            List of Collection objects.
        """
        data = self._get_json(collections_url(self._base))
        result = parse_collections(data)
        logger.info('Fetched %d collections from %s', len(result), self._domain)
        return result

    def collection_products(self, handle: str, limit: int = 250) -> list[Product]:
        """Fetch all products in a specific collection, auto-paginating.

        Args:
            handle: Collection URL slug (e.g. ``'power-banks'``).
            limit: Products per page (max 250).

        Returns:
            List of Product objects in the collection.

        Raises:
            CollectionNotFoundError: If the collection handle doesn't exist.
        """
        all_products: list[Product] = []
        page = 1

        while True:
            url = collection_products_url(self._base, handle, page=page, limit=limit)
            try:
                data = self._get_json(url)
            except RequestError:
                if page == 1:
                    raise CollectionNotFoundError(handle) from None
                break
            batch = parse_products(data)
            if not batch:
                break
            all_products.extend(batch)
            if len(batch) < limit:
                break
            page += 1

        logger.info(
            'Fetched %d products from collection %r', len(all_products), handle,
        )
        return all_products

    def collection_products_page(
        self, handle: str, page: int = 1, limit: int = 30,
    ) -> list[Product]:
        """Fetch a single page of products from a collection (no auto-pagination).

        Args:
            handle: Collection URL slug (e.g. ``'power-banks'``).
            page: Page number (1-indexed).
            limit: Products per page (1-250).

        Returns:
            List of Product objects for that page.

        Raises:
            CollectionNotFoundError: If the collection handle doesn't exist.
        """
        url = collection_products_url(self._base, handle, page=page, limit=limit)
        try:
            data = self._get_json(url)
        except RequestError:
            raise CollectionNotFoundError(handle) from None
        return parse_products(data)

    # ── Pages ──

    def pages(self) -> list[Page]:
        """Fetch all pages from the store.

        Returns:
            List of Page objects.
        """
        data = self._get_json(pages_url(self._base))
        return parse_pages(data)

    def page(self, handle: str) -> Page:
        """Fetch a single page by handle.

        Args:
            handle: Page URL slug (e.g. ``'contact'``).

        Returns:
            Page object.

        Raises:
            PageNotFoundError: If the page handle doesn't exist.
        """
        try:
            data = self._get_json(page_url(self._base, handle))
        except RequestError:
            raise PageNotFoundError(handle) from None
        return parse_page(data.get('page', data))

    def __repr__(self) -> str:
        return f'Shopify({self._domain!r})'
