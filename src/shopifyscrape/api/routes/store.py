from __future__ import annotations

from fastapi import APIRouter, Query

from shopifyscrape.api.deps import get_shopify
from shopifyscrape.api.schemas import PageResponse, StoreResponse

router = APIRouter()


@router.get('/store', response_model=StoreResponse)
async def get_store(
    domain: str = Query(..., description='Shopify store domain (e.g. spharetech.com)'),
) -> StoreResponse:
    """Fetch store metadata from a Shopify store."""
    shop = get_shopify(domain)
    store = shop.store()
    return StoreResponse(**store.to_dict())


@router.get('/pages', response_model=list[PageResponse])
async def get_pages(
    domain: str = Query(..., description='Shopify store domain (e.g. spharetech.com)'),
) -> list[PageResponse]:
    """Fetch all pages from a Shopify store."""
    shop = get_shopify(domain)
    pages = shop.pages()
    return [PageResponse(**p.to_dict()) for p in pages]
