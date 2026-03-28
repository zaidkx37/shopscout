from __future__ import annotations

from shopscout.client import Shopify

_proxy: str | None = None


def set_proxy(proxy: str | None) -> None:
    """Set the global proxy for API-created Shopify instances."""
    global _proxy
    _proxy = proxy


def get_shopify(domain: str) -> Shopify:
    """Create a Shopify client for the given domain."""
    return Shopify(domain, proxy=_proxy)
