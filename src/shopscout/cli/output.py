from __future__ import annotations

import json
import sys

from shopscout.models import Collection, Product, Store


def _safe_str(text: str | None) -> str:
    """Replace characters that can't be encoded in the current terminal."""
    if not text:
        return ''
    try:
        text.encode(sys.stdout.encoding or 'utf-8')
        return text
    except (UnicodeEncodeError, LookupError):
        return text.encode('ascii', errors='replace').decode('ascii')


def print_products(products: list[Product], output_json: bool = False) -> None:
    """Print products to terminal."""
    if output_json:
        print(json.dumps([p.to_dict() for p in products], indent=2, ensure_ascii=False))
        return

    try:
        from rich.console import Console
        from rich.table import Table

        console = Console(force_terminal=True)
        table = Table(title='Products', show_lines=True)
        table.add_column('#', style='dim', width=4)
        table.add_column('Title', style='bold', max_width=45)
        table.add_column('Vendor', style='cyan', max_width=15)
        table.add_column('Price', justify='right', style='green')
        table.add_column('Compare', justify='right', style='dim')
        table.add_column('Stock', justify='center')

        for i, product in enumerate(products, start=1):
            stock = '[green]Yes[/green]' if product.available else '[red]No[/red]'
            table.add_row(
                str(i),
                _safe_str(product.title),
                _safe_str(product.vendor),
                _safe_str(product.price) or '-',
                _safe_str(product.compare_at_price) or '-',
                stock,
            )

        console.print(table)
        console.print(f'[dim]{len(products)} products[/dim]')

    except ImportError:
        _print_products_plain(products)


def print_collections(collections: list[Collection], output_json: bool = False) -> None:
    """Print collections to terminal."""
    if output_json:
        print(json.dumps([c.to_dict() for c in collections], indent=2, ensure_ascii=False))
        return

    try:
        from rich.console import Console
        from rich.table import Table

        console = Console(force_terminal=True)
        table = Table(title='Collections', show_lines=True)
        table.add_column('#', style='dim', width=4)
        table.add_column('Title', style='bold', max_width=40)
        table.add_column('Handle', style='cyan', max_width=30)
        table.add_column('Products', justify='right')

        for i, col in enumerate(collections, start=1):
            table.add_row(
                str(i),
                _safe_str(col.title),
                _safe_str(col.handle),
                str(col.products_count),
            )

        console.print(table)
        console.print(f'[dim]{len(collections)} collections[/dim]')

    except ImportError:
        _print_collections_plain(collections)


def print_store(store: Store, output_json: bool = False) -> None:
    """Print store metadata to terminal."""
    if output_json:
        print(json.dumps(store.to_dict(), indent=2, ensure_ascii=False))
        return

    try:
        from rich.console import Console
        from rich.panel import Panel
        from rich.table import Table

        console = Console(force_terminal=True)
        table = Table(show_header=False, box=None, padding=(0, 2))
        table.add_column('Key', style='bold')
        table.add_column('Value')
        table.add_row('Name', store.name)
        table.add_row('Domain', store.domain)
        table.add_row('URL', store.url)
        table.add_row('Shopify Domain', store.myshopify_domain)
        table.add_row('Country', store.country)
        table.add_row('Currency', store.currency)
        table.add_row('Money Format', store.money_format)
        table.add_row('Products', str(store.published_products_count))
        table.add_row('Collections', str(store.published_collections_count))
        if store.ships_to_countries:
            table.add_row('Ships To', ', '.join(store.ships_to_countries))

        console.print(Panel(table, title=store.name, border_style='cyan'))

    except ImportError:
        _print_store_plain(store)


def _print_products_plain(products: list[Product]) -> None:
    """Fallback plain text output for products."""
    print('Products\n')
    for i, p in enumerate(products, start=1):
        stock = 'In Stock' if p.available else 'Out of Stock'
        print(f'{i}. {p.title}')
        print(f'   Vendor: {p.vendor} | Price: {p.price or "-"} | {stock}')
        print()


def _print_collections_plain(collections: list[Collection]) -> None:
    """Fallback plain text output for collections."""
    print('Collections\n')
    for i, c in enumerate(collections, start=1):
        print(f'{i}. {c.title} ({c.handle}) - {c.products_count} products')


def _print_store_plain(store: Store) -> None:
    """Fallback plain text output for store."""
    print(f'Store: {store.name}')
    print(f'Domain: {store.domain}')
    print(f'Country: {store.country} | Currency: {store.currency}')
    print(f'Products: {store.published_products_count}')
    print(f'Collections: {store.published_collections_count}')
