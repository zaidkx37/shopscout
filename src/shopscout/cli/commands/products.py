from __future__ import annotations

import click

from shopscout.cli.output import print_products


@click.command()
@click.argument('domain')
@click.option('--collection', '-c', default=None, help='Filter by collection handle.')
@click.option('--page', '-p', default=None, type=int, help='Page number (manual pagination).')
@click.option('--limit', '-l', default=30, type=int, help='Products per page (1-250, default 30).')
@click.option('--json', 'output_json', is_flag=True, help='Output as JSON.')
@click.option('--save', '-s', default=None, help='Save to file (json or csv).')
@click.pass_context
def products(
    ctx: click.Context,
    domain: str,
    collection: str | None,
    page: int | None,
    limit: int,
    output_json: bool,
    save: str | None,
) -> None:
    """Scrape products from a Shopify store.

    \b
    Examples:
        shopscout products spharetech.com
        shopscout products spharetech.com --collection power-banks
        shopscout products spharetech.com --page 1 --limit 10
        shopscout products spharetech.com -c power-banks -p 1 -l 5
        shopscout products spharetech.com --json
        shopscout products spharetech.com --save products.csv
    """
    from shopscout import Exporter, Shopify

    proxy = ctx.obj.get('proxy')
    shop = Shopify(domain, proxy=proxy)

    if page is not None:
        if collection:
            result = shop.collection_products_page(collection, page=page, limit=limit)
        else:
            result = shop.products_page(page=page, limit=limit)
    else:
        if collection:
            result = shop.collection_products(collection)
        else:
            result = shop.products()

    if save:
        exporter = Exporter()
        if save.endswith('.csv'):
            exporter.products_to_csv(result, filename=save)
            click.echo(f'Saved {len(result)} products to output/{save}')
        else:
            exporter.products_to_json(result, filename=save)
            click.echo(f'Saved {len(result)} products to output/{save}')
    else:
        print_products(result, output_json=output_json)
