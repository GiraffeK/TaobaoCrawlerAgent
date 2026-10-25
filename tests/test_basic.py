import pytest
from taobao_crawler_agent import __version__
from taobao_crawler_agent.crawler.parser import ProductParser
from taobao_crawler_agent.models import ProductItem


def test_version():
    assert __version__ == "0.1.0"


def test_parse_price():
    assert ProductParser.parse_price("¥ 129.00") == 129.0
    assert ProductParser.parse_price("99.9") == 99.9
    assert ProductParser.parse_price("¥1,234.50") == 1234.5
    assert ProductParser.parse_price("Free") == 0.0


def test_product_item_model():
    item = ProductItem(
        title="Wireless Bluetooth Mouse",
        price=59.9,
        detail_url="https://item.taobao.com/item.htm?id=12345678",
    )
    assert item.title == "Wireless Bluetooth Mouse"
    assert item.price == 59.9

