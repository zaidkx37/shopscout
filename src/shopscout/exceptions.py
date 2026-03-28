"""Exception hierarchy for shopscout."""

from __future__ import annotations


class ShopifyError(Exception):
    """Base exception for all shopscout errors."""


class StoreNotFoundError(ShopifyError):
    """Store does not exist or is not a Shopify store."""

    def __init__(self, domain: str) -> None:
        self.domain = domain
        super().__init__(f"Store not found or not a Shopify store: '{domain}'")


class CollectionNotFoundError(ShopifyError):
    """Collection handle does not exist."""

    def __init__(self, handle: str) -> None:
        self.handle = handle
        super().__init__(f"Collection not found: '{handle}'")


class ProductNotFoundError(ShopifyError):
    """Product handle does not exist."""

    def __init__(self, handle: str) -> None:
        self.handle = handle
        super().__init__(f"Product not found: '{handle}'")


class PageNotFoundError(ShopifyError):
    """Page handle does not exist."""

    def __init__(self, handle: str) -> None:
        self.handle = handle
        super().__init__(f"Page not found: '{handle}'")


class RateLimitError(ShopifyError):
    """Store rate limit hit (HTTP 429 or 430)."""

    def __init__(self, message: str = 'Rate limited by Shopify') -> None:
        super().__init__(message)


class RequestError(ShopifyError):
    """HTTP request failed."""

    def __init__(self, status_code: int, message: str = '') -> None:
        self.status_code = status_code
        super().__init__(f'HTTP {status_code}: {message}' if message else f'HTTP {status_code}')


class ParsingError(ShopifyError):
    """Failed to parse store response."""
