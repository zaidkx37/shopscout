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
from shopscout.models import Collection, Page, Product, Review, ReviewSummary, Store

logger = logging.getLogger('shopscout')


def _extract_shop_id(html: str) -> int | None:
    """Extract shop_id from a product page HTML."""
    try:
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(html, 'html.parser')
        tag = soup.find('script', attrs={'data-page-type': 'product'})
        if tag is None:
            return None
        shop_id_str = tag.get('data-shop-id')
        if shop_id_str is None:
            return None
        return int(shop_id_str)
    except Exception:
        return None


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

    # -- Reviews (Trustoo) --

    def shop_id(self) -> int | None:
        """Auto-detect the shop_id by scraping a product page.

        The shop_id is needed for the Trustoo reviews API. It's extracted
        from a ``<script data-page-type="product">`` tag on any product page.

        Returns:
            The shop_id as an integer, or None if not found.
        """
        try:
            products = self.products_page(page=1, limit=1)
            if not products:
                return None
            import requests as _requests
            url = f'{self._base}/products/{products[0].handle}'
            response = _requests.get(url, allow_redirects=True, timeout=15)
            return _extract_shop_id(response.text)
        except Exception:
            return None

    def reviews(
        self,
        product_id: int,
        shop_id: int | None = None,
        page: int = 1,
        limit: int = 15,
    ) -> tuple[list[Review], ReviewSummary]:
        """Fetch reviews for a product from the Trustoo reviews API.

        Args:
            product_id: The Shopify product ID (numeric).
            shop_id: The shop ID. If not provided, auto-detected.
            page: Page number (1-indexed).
            limit: Reviews per page.

        Returns:
            Tuple of (list of Review objects, ReviewSummary with totals).
        """
        if shop_id is None:
            shop_id = self.shop_id()
            if shop_id is None:
                logger.warning('Could not detect shop_id for reviews')
                return [], ReviewSummary(total_reviews=0, average_rating=0.0)

        params = {
            'shop_id': str(shop_id),
            'product_id': str(product_id),
            'page': str(page),
            'limit': str(limit),
            'sort_by': 'comprehensive-descending',
        }

        import requests as _requests
        resp = _requests.get(
            'https://api.trustoo.io/api/v1/reviews/get_product_reviews',
            params=params,
            timeout=15,
        )
        data = resp.json()

        if data.get('code') != 0:
            logger.warning('Trustoo API error: %s', data.get('message'))
            return [], ReviewSummary(total_reviews=0, average_rating=0.0)

        inner = data['data']
        total_rating = inner.get('total_rating', {})

        summary = ReviewSummary(
            total_reviews=total_rating.get('total_reviews', 0),
            average_rating=float(total_rating.get('rating', '0.00')),
            star_1=total_rating.get('total_star1', 0),
            star_2=total_rating.get('total_star2', 0),
            star_3=total_rating.get('total_star3', 0),
            star_4=total_rating.get('total_star4', 0),
            star_5=total_rating.get('total_star5', 0),
        )

        reviews = [
            Review(
                id=str(r.get('id', '')),
                author=r.get('author', ''),
                rating=r.get('star', 0),
                content=r.get('content', ''),
                commented_at=r.get('commented_at', ''),
                verified=r.get('verified_badge', 0) > 0,
                reply_content=r.get('reply_content', ''),
                resources=r.get('resources', []),
            )
            for r in inner.get('list', [])
        ]

        logger.info(
            'Fetched %d reviews for product %d (total: %d)',
            len(reviews), product_id, summary.total_reviews,
        )
        return reviews, summary

    def review_count(self, product_id: int, shop_id: int | None = None) -> int:
        """Get just the review count for a product (efficient, fetches limit=1).

        Args:
            product_id: The Shopify product ID.
            shop_id: The shop ID. If not provided, auto-detected.

        Returns:
            Total review count for the product.
        """
        _, summary = self.reviews(product_id, shop_id=shop_id, page=1, limit=1)
        return summary.total_reviews

    def __repr__(self) -> str:
        return f'Shopify({self._domain!r})'
