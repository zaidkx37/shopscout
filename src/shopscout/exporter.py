"""Export scraped Shopify data to JSON and CSV."""

from __future__ import annotations

import csv
import json
import logging
from pathlib import Path

from shopscout.models import Collection, Product, Store

logger = logging.getLogger(__name__)


class Exporter:
    """Exports scraped Shopify data to JSON and CSV files."""

    def __init__(self, output_dir: str | Path = 'output') -> None:
        self._output_dir = Path(output_dir)
        self._output_dir.mkdir(parents=True, exist_ok=True)

    def products_to_json(
        self, products: list[Product], filename: str = 'products.json',
    ) -> Path:
        """Export products to a JSON file."""
        path = self._output_dir / filename
        data = [p.to_dict() for p in products]
        path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding='utf-8')
        logger.info('Exported %d products to %s', len(products), path)
        return path

    def products_to_csv(
        self, products: list[Product], filename: str = 'products.csv',
    ) -> Path:
        """Export products to a CSV file (flat format)."""
        path = self._output_dir / filename
        if not products:
            logger.warning('No products to export')
            return path

        rows = [p.to_flat_dict() for p in products]
        fieldnames = list(rows[0].keys())

        with open(path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(rows)

        logger.info('Exported %d products to %s', len(products), path)
        return path

    def collections_to_json(
        self, collections: list[Collection], filename: str = 'collections.json',
    ) -> Path:
        """Export collections to a JSON file."""
        path = self._output_dir / filename
        data = [c.to_dict() for c in collections]
        path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding='utf-8')
        logger.info('Exported %d collections to %s', len(collections), path)
        return path

    def store_to_json(self, store: Store, filename: str = 'store.json') -> Path:
        """Export store metadata to a JSON file."""
        path = self._output_dir / filename
        path.write_text(
            json.dumps(store.to_dict(), indent=2, ensure_ascii=False), encoding='utf-8',
        )
        logger.info('Exported store metadata to %s', path)
        return path
