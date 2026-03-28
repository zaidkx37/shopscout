from __future__ import annotations

import click


@click.command()
@click.option('--host', '-h', default='127.0.0.1', help='Host to bind to.')
@click.option('--port', '-p', default=8000, type=int, help='Port to bind to.')
@click.pass_context
def serve(ctx: click.Context, host: str, port: int) -> None:
    """Start the REST API server.

    \b
    Examples:
        shopifyscrape serve
        shopifyscrape serve --port 3000
        shopifyscrape serve --host 0.0.0.0 --port 8080
    """
    import uvicorn

    from shopifyscrape.api.app import create_app

    proxy = ctx.obj.get('proxy')
    app = create_app(proxy=proxy)
    click.echo(f'Starting ShopifyScrape API on {host}:{port}')
    uvicorn.run(app, host=host, port=port)
