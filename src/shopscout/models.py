"""Data models for shopscout."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True, slots=True)
class Store:
    """Shopify store metadata from /meta.json."""

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
    description: str = ''
    city: str = ''
    ships_to_countries: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            'id': self.id,
            'name': self.name,
            'domain': self.domain,
            'url': self.url,
            'myshopify_domain': self.myshopify_domain,
            'country': self.country,
            'currency': self.currency,
            'money_format': self.money_format,
            'published_products_count': self.published_products_count,
            'published_collections_count': self.published_collections_count,
            'description': self.description,
            'city': self.city,
            'ships_to_countries': self.ships_to_countries,
        }


@dataclass(frozen=True, slots=True)
class ProductImage:
    """A single product image."""

    id: int
    src: str
    width: int
    height: int
    position: int

    def to_dict(self) -> dict:
        return {
            'id': self.id,
            'src': self.src,
            'width': self.width,
            'height': self.height,
            'position': self.position,
        }


@dataclass(frozen=True, slots=True)
class ProductOption:
    """A product option (e.g. Size, Color)."""

    name: str
    position: int
    values: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            'name': self.name,
            'position': self.position,
            'values': self.values,
        }


@dataclass(frozen=True, slots=True)
class Variant:
    """A single product variant with pricing and stock."""

    id: int
    title: str
    price: str
    compare_at_price: str | None
    available: bool
    option1: str | None = None
    option2: str | None = None
    option3: str | None = None
    sku: str | None = None
    grams: int = 0
    requires_shipping: bool = True
    taxable: bool = False
    position: int = 1

    @property
    def discount_percentage(self) -> float | None:
        """Calculate discount percentage if compare_at_price exists."""
        if not self.compare_at_price:
            return None
        try:
            original = float(self.compare_at_price)
            current = float(self.price)
            if original > 0:
                return round((1 - current / original) * 100, 1)
        except ValueError:
            pass
        return None

    def to_dict(self) -> dict:
        result: dict = {
            'id': self.id,
            'title': self.title,
            'price': self.price,
            'compare_at_price': self.compare_at_price,
            'available': self.available,
            'sku': self.sku,
            'grams': self.grams,
            'position': self.position,
        }
        if self.option1 and self.option1 != 'Default Title':
            result['option1'] = self.option1
        if self.option2:
            result['option2'] = self.option2
        if self.option3:
            result['option3'] = self.option3
        discount = self.discount_percentage
        if discount is not None:
            result['discount_percentage'] = discount
        return result


@dataclass(frozen=True, slots=True)
class Product:
    """A Shopify product with variants, images, and options."""

    id: int
    title: str
    handle: str
    vendor: str
    product_type: str
    body_html: str
    published_at: str
    updated_at: str
    tags: list[str] = field(default_factory=list)
    variants: list[Variant] = field(default_factory=list)
    images: list[ProductImage] = field(default_factory=list)
    options: list[ProductOption] = field(default_factory=list)

    @property
    def url(self) -> str:
        """Product URL path."""
        return f'/products/{self.handle}'

    @property
    def price(self) -> str | None:
        """Price of the first variant."""
        if self.variants:
            return self.variants[0].price
        return None

    @property
    def compare_at_price(self) -> str | None:
        """Compare-at price of the first variant."""
        if self.variants:
            return self.variants[0].compare_at_price
        return None

    @property
    def available(self) -> bool:
        """True if any variant is available."""
        return any(v.available for v in self.variants)

    @property
    def primary_image(self) -> str | None:
        """URL of the first image."""
        if self.images:
            return self.images[0].src
        return None

    def to_dict(self) -> dict:
        return {
            'id': self.id,
            'title': self.title,
            'handle': self.handle,
            'vendor': self.vendor,
            'product_type': self.product_type,
            'body_html': self.body_html,
            'published_at': self.published_at,
            'updated_at': self.updated_at,
            'tags': self.tags,
            'url': self.url,
            'price': self.price,
            'compare_at_price': self.compare_at_price,
            'available': self.available,
            'primary_image': self.primary_image,
            'variants': [v.to_dict() for v in self.variants],
            'images': [i.to_dict() for i in self.images],
            'options': [o.to_dict() for o in self.options],
        }

    def to_flat_dict(self) -> dict:
        """Flat dictionary for CSV export."""
        return {
            'id': self.id,
            'title': self.title,
            'handle': self.handle,
            'vendor': self.vendor,
            'product_type': self.product_type,
            'published_at': self.published_at,
            'updated_at': self.updated_at,
            'tags': ', '.join(self.tags),
            'price': self.price,
            'compare_at_price': self.compare_at_price,
            'available': self.available,
            'primary_image': self.primary_image,
            'variant_count': len(self.variants),
            'image_count': len(self.images),
        }


@dataclass(frozen=True, slots=True)
class CollectionImage:
    """A collection image."""

    id: int
    src: str
    alt: str | None = None

    def to_dict(self) -> dict:
        return {
            'id': self.id,
            'src': self.src,
            'alt': self.alt,
        }


@dataclass(frozen=True, slots=True)
class Collection:
    """A Shopify collection."""

    id: int
    title: str
    handle: str
    description: str
    published_at: str
    updated_at: str
    products_count: int = 0
    image: CollectionImage | None = None

    @property
    def url(self) -> str:
        """Collection URL path."""
        return f'/collections/{self.handle}'

    def to_dict(self) -> dict:
        return {
            'id': self.id,
            'title': self.title,
            'handle': self.handle,
            'description': self.description,
            'published_at': self.published_at,
            'updated_at': self.updated_at,
            'products_count': self.products_count,
            'url': self.url,
            'image': self.image.to_dict() if self.image else None,
        }


@dataclass(frozen=True, slots=True)
class Page:
    """A Shopify page."""

    id: int
    title: str
    handle: str
    body_html: str | None
    published_at: str
    updated_at: str

    @property
    def url(self) -> str:
        return f'/pages/{self.handle}'

    def to_dict(self) -> dict:
        return {
            'id': self.id,
            'title': self.title,
            'handle': self.handle,
            'body_html': self.body_html,
            'published_at': self.published_at,
            'updated_at': self.updated_at,
            'url': self.url,
        }
