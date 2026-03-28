from __future__ import annotations

import click

from shopifyscrape.cli.output import print_store


@click.command()
@click.argument('domain')
@click.option('--json', 'output_json', is_flag=True, help='Output as JSON.')
@click.option('--save', '-s', default=None, help='Save to JSON file.')
@click.pass_context
def store(
    ctx: click.Context,
    domain: str,
    output_json: bool,
    save: str | None,
) -> None:
    """Fetch store metadata from a Shopify store.

    \b
    Examples:
        shopifyscrape store spharetech.com
        shopifyscrape store spharetech.com --json
        shopifyscrape store spharetech.com --save store.json
    """
    from shopifyscrape import Exporter, Shopify

    proxy = ctx.obj.get('proxy')
    shop = Shopify(domain, proxy=proxy)
    result = shop.store()

    if save:
        exporter = Exporter()
        exporter.store_to_json(result, filename=save)
        click.echo(f'Saved store metadata to output/{save}')
    else:
        print_store(result, output_json=output_json)
