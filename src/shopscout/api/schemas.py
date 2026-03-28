from __future__ import annotations

from pydantic import BaseModel


class VariantResponse(BaseModel):
    id: int
    title: str
    price: str
    compare_at_price: str | None
    available: bool
    sku: str | None = None
    grams: int = 0
    position: int = 1
    option1: str | None = None
    option2: str | None = None
    option3: str | None = None
    discount_percentage: float | None = None


class ProductImageResponse(BaseModel):
    id: int
    src: str
    width: int
    height: int
    position: int


class ProductOptionResponse(BaseModel):
    name: str
    position: int
    values: list[str]


class ProductResponse(BaseModel):
    id: int
    title: str
    handle: str
    vendor: str
    product_type: str
    published_at: str
    updated_at: str
    tags: list[str]
    url: str
    price: str | None
    compare_at_price: str | None
    available: bool
    primary_image: str | None
    variants: list[VariantResponse]
    images: list[ProductImageResponse]
    options: list[ProductOptionResponse]


class CollectionImageResponse(BaseModel):
    id: int
    src: str
    alt: str | None = None


class CollectionResponse(BaseModel):
    id: int
    title: str
    handle: str
    description: str
    published_at: str
    updated_at: str
    products_count: int
    url: str
    image: CollectionImageResponse | None = None


class StoreResponse(BaseModel):
    id: int
    name: str
    domain: str
    url: str
    myshopify_domain: str
    country: str
    currency: str
    money_format: str
    published_products_count: int
    published_collections_count: int
    description: str
    city: str
    ships_to_countries: list[str]


class PageResponse(BaseModel):
    id: int
    title: str
    handle: str
    body_html: str | None
    published_at: str
    updated_at: str
    url: str


class ErrorResponse(BaseModel):
    error: str
    detail: str | None = None


class HealthResponse(BaseModel):
    status: str = 'ok'
    version: str
