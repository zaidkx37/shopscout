"""Tests for data models."""

from shopifyscrape.models import Collection, Product, Variant


class TestVariant:
    def test_discount_percentage(self):
        v = Variant(id=1, title='test', price='3499.00', compare_at_price='4999.00',
                    available=True)
        assert v.discount_percentage == 30.0

    def test_discount_none_when_no_compare(self):
        v = Variant(id=1, title='test', price='3499.00', compare_at_price=None,
                    available=True)
        assert v.discount_percentage is None

    def test_to_dict_excludes_default_title(self):
        v = Variant(id=1, title='Default Title', price='100.00',
                    compare_at_price=None, available=True, option1='Default Title')
        d = v.to_dict()
        assert 'option1' not in d


class TestProduct:
    def test_available_any_variant(self):
        p = Product(
            id=1, title='Test', handle='test', vendor='V', product_type='',
            body_html='', published_at='', updated_at='',
            variants=[
                Variant(id=1, title='A', price='10', compare_at_price=None, available=False),
                Variant(id=2, title='B', price='20', compare_at_price=None, available=True),
            ],
        )
        assert p.available is True

    def test_not_available_when_all_out(self):
        p = Product(
            id=1, title='Test', handle='test', vendor='V', product_type='',
            body_html='', published_at='', updated_at='',
            variants=[
                Variant(id=1, title='A', price='10', compare_at_price=None, available=False),
            ],
        )
        assert p.available is False

    def test_url(self):
        p = Product(
            id=1, title='Test', handle='my-product', vendor='V', product_type='',
            body_html='', published_at='', updated_at='',
        )
        assert p.url == '/products/my-product'


class TestCollection:
    def test_url(self):
        c = Collection(
            id=1, title='Test', handle='test-col', description='',
            published_at='', updated_at='',
        )
        assert c.url == '/collections/test-col'
