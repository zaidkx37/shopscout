"""Response parsers - JSON dicts to dataclass models."""

from __future__ import annotations

from shopscout.models import (
    Collection,
    CollectionImage,
    Page,
    Product,
    ProductImage,
    ProductOption,
    Store,
    Variant,
)


def parse_store(data: dict) -> Store:
    """Parse /meta.json response into a Store model."""
    return Store(
        id=data.get('id', 0),
        name=data.get('name', ''),
        domain=data.get('domain', ''),
        url=data.get('url', ''),
        myshopify_domain=data.get('myshopify_domain', ''),
        country=data.get('country', ''),
        currency=data.get('currency', ''),
        money_format=data.get('money_format', ''),
        published_products_count=data.get('published_products_count', 0),
        published_collections_count=data.get('published_collections_count', 0),
        description=data.get('description', ''),
        city=data.get('city', ''),
        ships_to_countries=data.get('ships_to_countries', []),
    )


def parse_variant(data: dict) -> Variant:
    """Parse a single variant dict."""
    return Variant(
        id=data.get('id', 0),
        title=data.get('title', ''),
        price=data.get('price', '0.00'),
        compare_at_price=data.get('compare_at_price'),
        available=data.get('available', False),
        option1=data.get('option1'),
        option2=data.get('option2'),
        option3=data.get('option3'),
        sku=data.get('sku'),
        grams=data.get('grams', 0),
        requires_shipping=data.get('requires_shipping', True),
        taxable=data.get('taxable', False),
        position=data.get('position', 1),
    )


def parse_image(data: dict) -> ProductImage:
    """Parse a single product image dict."""
    return ProductImage(
        id=data.get('id', 0),
        src=data.get('src', ''),
        width=data.get('width', 0),
        height=data.get('height', 0),
        position=data.get('position', 1),
    )


def parse_option(data: dict) -> ProductOption:
    """Parse a single product option dict."""
    return ProductOption(
        name=data.get('name', ''),
        position=data.get('position', 1),
        values=data.get('values', []),
    )


def parse_product(data: dict) -> Product:
    """Parse a single product dict."""
    return Product(
        id=data.get('id', 0),
        title=data.get('title', ''),
        handle=data.get('handle', ''),
        vendor=data.get('vendor', ''),
        product_type=data.get('product_type', ''),
        body_html=data.get('body_html', ''),
        published_at=data.get('published_at', ''),
        updated_at=data.get('updated_at', ''),
        tags=data.get('tags', []),
        variants=[parse_variant(v) for v in data.get('variants', [])],
        images=[parse_image(i) for i in data.get('images', [])],
        options=[parse_option(o) for o in data.get('options', [])],
    )


def parse_products(data: dict) -> list[Product]:
    """Parse /products.json response."""
    return [parse_product(p) for p in data.get('products', [])]


def parse_collection_image(data: dict | None) -> CollectionImage | None:
    """Parse a collection image dict."""
    if not data:
        return None
    return CollectionImage(
        id=data.get('id', 0),
        src=data.get('src', ''),
        alt=data.get('alt'),
    )


def parse_collection(data: dict) -> Collection:
    """Parse a single collection dict."""
    return Collection(
        id=data.get('id', 0),
        title=data.get('title', ''),
        handle=data.get('handle', ''),
        description=data.get('description', ''),
        published_at=data.get('published_at', ''),
        updated_at=data.get('updated_at', ''),
        products_count=data.get('products_count', 0),
        image=parse_collection_image(data.get('image')),
    )


def parse_collections(data: dict) -> list[Collection]:
    """Parse /collections.json response."""
    return [parse_collection(c) for c in data.get('collections', [])]


def parse_page(data: dict) -> Page:
    """Parse a single page dict."""
    return Page(
        id=data.get('id', 0),
        title=data.get('title', ''),
        handle=data.get('handle', ''),
        body_html=data.get('body_html'),
        published_at=data.get('published_at', ''),
        updated_at=data.get('updated_at', ''),
    )


def parse_pages(data: dict) -> list[Page]:
    """Parse /pages.json response."""
    return [parse_page(p) for p in data.get('pages', [])]
