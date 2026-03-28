from __future__ import annotations

from fastapi import APIRouter, Query

from shopscout.api.deps import get_shopify
from shopscout.api.schemas import ProductResponse

router = APIRouter()


@router.get('/products', response_model=list[ProductResponse])
async def get_products(
    domain: str = Query(..., description='Shopify store domain (e.g. spharetech.com)'),
    collection: str | None = Query(None, description='Filter by collection handle'),
    page: int | None = Query(None, ge=1, description='Page number (omit to fetch all)'),
    limit: int = Query(30, ge=1, le=250, description='Products per page (1-250)'),
) -> list[ProductResponse]:
    """Scrape products from a Shopify store.

    Omit `page` to auto-paginate and fetch all products.
    Pass `page` to fetch a single page.
    """
    shop = get_shopify(domain)

    if page is not None:
        if collection:
            products = shop.collection_products_page(collection, page=page, limit=limit)
        else:
            products = shop.products_page(page=page, limit=limit)
    else:
        products = shop.collection_products(collection) if collection else shop.products()

    return [ProductResponse(**p.to_dict()) for p in products]


@router.get('/products/{handle}', response_model=ProductResponse)
async def get_product(
    handle: str,
    domain: str = Query(..., description='Shopify store domain'),
) -> ProductResponse:
    """Scrape a single product by handle."""
    shop = get_shopify(domain)
    product = shop.product(handle)
    return ProductResponse(**product.to_dict())
