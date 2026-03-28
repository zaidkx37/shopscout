from __future__ import annotations

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from shopscout import __version__
from shopscout.api.deps import set_proxy
from shopscout.api.routes import collections, products, store
from shopscout.api.schemas import ErrorResponse, HealthResponse
from shopscout.exceptions import (
    CollectionNotFoundError,
    PageNotFoundError,
    ProductNotFoundError,
    RateLimitError,
    RequestError,
    ShopifyError,
    StoreNotFoundError,
)


def create_app(
    proxy: str | None = None,
    title: str = 'ShopifyScrape API',
) -> FastAPI:
    """Create and configure the FastAPI application.

    Args:
        proxy: Optional proxy URL for requests.
        title: API title shown in docs.

    Returns:
        Configured FastAPI application.
    """
    app = FastAPI(
        title=title,
        version=__version__,
        description='Shopify store scraping API: products, collections, pages & metadata.',
    )

    if proxy:
        set_proxy(proxy)

    # Routes
    app.include_router(products.router, prefix='/api/v1', tags=['products'])
    app.include_router(collections.router, prefix='/api/v1', tags=['collections'])
    app.include_router(store.router, prefix='/api/v1', tags=['store'])

    # Health check
    @app.get('/health', response_model=HealthResponse, tags=['health'])
    async def health():
        return HealthResponse(version=__version__)

    # Exception handlers
    @app.exception_handler(StoreNotFoundError)
    async def store_not_found_handler(request: Request, exc: StoreNotFoundError):
        return JSONResponse(
            status_code=404,
            content=ErrorResponse(error='store_not_found', detail=str(exc)).model_dump(),
        )

    @app.exception_handler(ProductNotFoundError)
    async def product_not_found_handler(request: Request, exc: ProductNotFoundError):
        return JSONResponse(
            status_code=404,
            content=ErrorResponse(error='product_not_found', detail=str(exc)).model_dump(),
        )

    @app.exception_handler(CollectionNotFoundError)
    async def collection_not_found_handler(request: Request, exc: CollectionNotFoundError):
        return JSONResponse(
            status_code=404,
            content=ErrorResponse(error='collection_not_found', detail=str(exc)).model_dump(),
        )

    @app.exception_handler(PageNotFoundError)
    async def page_not_found_handler(request: Request, exc: PageNotFoundError):
        return JSONResponse(
            status_code=404,
            content=ErrorResponse(error='page_not_found', detail=str(exc)).model_dump(),
        )

    @app.exception_handler(RateLimitError)
    async def rate_limit_handler(request: Request, exc: RateLimitError):
        return JSONResponse(
            status_code=429,
            content=ErrorResponse(error='rate_limited', detail=str(exc)).model_dump(),
        )

    @app.exception_handler(RequestError)
    async def request_error_handler(request: Request, exc: RequestError):
        return JSONResponse(
            status_code=502,
            content=ErrorResponse(error='upstream_error', detail=str(exc)).model_dump(),
        )

    @app.exception_handler(ShopifyError)
    async def shopify_error_handler(request: Request, exc: ShopifyError):
        return JSONResponse(
            status_code=500,
            content=ErrorResponse(error='shopify_error', detail=str(exc)).model_dump(),
        )

    return app
