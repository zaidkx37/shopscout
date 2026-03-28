from __future__ import annotations

import click

from shopifyscrape.cli.output import print_collections


@click.command()
@click.argument('domain')
@click.option('--json', 'output_json', is_flag=True, help='Output as JSON.')
@click.option('--save', '-s', default=None, help='Save to JSON file.')
@click.pass_context
def collections(
    ctx: click.Context,
    domain: str,
    output_json: bool,
    save: str | None,
) -> None:
    """Scrape collections from a Shopify store.

    \b
    Examples:
        shopifyscrape collections spharetech.com
        shopifyscrape collections spharetech.com --json
        shopifyscrape collections spharetech.com --save collections.json
    """
    from shopifyscrape import Exporter, Shopify

    proxy = ctx.obj.get('proxy')
    shop = Shopify(domain, proxy=proxy)
    result = shop.collections()

    if save:
        exporter = Exporter()
        exporter.collections_to_json(result, filename=save)
        click.echo(f'Saved {len(result)} collections to output/{save}')
    else:
        print_collections(result, output_json=output_json)
