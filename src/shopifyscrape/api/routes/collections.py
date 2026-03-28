from __future__ import annotations

from fastapi import APIRouter, Query

from shopifyscrape.api.deps import get_shopify
from shopifyscrape.api.schemas import CollectionResponse

router = APIRouter()


@router.get('/collections', response_model=list[CollectionResponse])
async def get_collections(
    domain: str = Query(..., description='Shopify store domain (e.g. spharetech.com)'),
) -> list[CollectionResponse]:
    """Scrape all collections from a Shopify store."""
    shop = get_shopify(domain)
    collections = shop.collections()
    return [CollectionResponse(**c.to_dict()) for c in collections]
