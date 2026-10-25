import re
from typing import Optional, Dict, Any
from bs4 import BeautifulSoup
from ..models import ProductItem
from ..utils.logger import setup_logger

logger = setup_logger()


class ProductParser:
    """Parses raw HTML / DOM elements into structured ProductItem models."""

    @staticmethod
    def parse_price(raw_text: str) -> float:
        """Extract float price from string like '¥ 129.00' or '129.5'."""
        if not raw_text:
            return 0.0
        match = re.search(r"(\d+(\.\d+)?)", raw_text.replace(",", ""))
        return float(match.group(1)) if match else 0.0

    @classmethod
    def parse_card_html(cls, html_snippet: str) -> Optional[ProductItem]:
        """Parse individual item card element."""
        soup = BeautifulSoup(html_snippet, "html.parser")
        
        # Example selector parsing (flexible fallback)
        title_el = soup.select_one(".title, .item-title, [class*='title']")
        price_el = soup.select_one(".price, [class*='price']")
        deal_el = soup.select_one(".deal-cnt, [class*='deal'], [class*='sales']")
        shop_el = soup.select_one(".shop, [class*='shopname'], [class*='shop']")
        link_el = soup.select_one("a[href*='item.taobao.com'], a[href*='detail.tmall.com'], a[href]")

        title = title_el.get_text(strip=True) if title_el else "Unknown Title"
        price = cls.parse_price(price_el.get_text(strip=True)) if price_el else 0.0
        sales = deal_el.get_text(strip=True) if deal_el else None
        shop = shop_el.get_text(strip=True) if shop_el else None
        detail_url = link_el["href"] if link_el and "href" in link_el.attrs else ""

        if detail_url.startswith("//"):
            detail_url = "https:" + detail_url

        item_id_match = re.search(r"[?&]id=(\d+)", detail_url)
        item_id = item_id_match.group(1) if item_id_match else None

        return ProductItem(
            item_id=item_id,
            title=title,
            price=price,
            sales_count=sales,
            shop_name=shop,
            detail_url=detail_url,
        )
