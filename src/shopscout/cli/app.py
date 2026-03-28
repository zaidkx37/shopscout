from __future__ import annotations

import click

from shopscout import __version__


@click.group()
@click.version_option(version=__version__, prog_name='shopscout')
@click.option('--proxy', envvar='SHOPIFYSCRAPE_PROXY', default=None, help='HTTP proxy URL.')
@click.pass_context
def main(ctx: click.Context, proxy: str | None) -> None:
    """shopscout - Shopify store scraping toolkit.

    Scrape products, collections, and metadata from any Shopify store.
    No API key required.
    """
    ctx.ensure_object(dict)
    ctx.obj['proxy'] = proxy


def _register_commands() -> None:
    """Register CLI commands. Deferred to avoid import errors when extras not installed."""
    from shopscout.cli.commands.collections import collections
    from shopscout.cli.commands.products import products
    from shopscout.cli.commands.store import store

    main.add_command(products)
    main.add_command(collections)
    main.add_command(store)

    try:
        from shopscout.cli.commands.serve import serve
        main.add_command(serve)
    except ImportError:
        pass


_register_commands()


if __name__ == '__main__':
    main()
