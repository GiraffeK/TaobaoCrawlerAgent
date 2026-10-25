import urllib.parse
from typing import List
from playwright.async_api import Page
from ..models import ProductItem, SearchQuery
from .parser import ProductParser
from ..utils.logger import setup_logger

logger = setup_logger()


class TaobaoSearchScraper:
    """Automates Taobao search page querying and extraction."""

    TAOBAO_SEARCH_URL = "https://s.taobao.com/search"

    def __init__(self, page: Page):
        self.page = page

    async def search(self, query: SearchQuery) -> List[ProductItem]:
        """Execute search on Taobao and extract items from result page."""
        params = {"q": query.keyword}
        if query.sort_by:
            params["sort"] = query.sort_by
            
        url = f"{self.TAOBAO_SEARCH_URL}?{urllib.parse.urlencode(params)}"
        logger.info(f"Navigating to {url}")
        
        await self.page.goto(url, wait_until="domcontentloaded")
        
        # Check if redirected to login
        current_url = self.page.url
        if "login.taobao.com" in current_url:
            logger.warning("Taobao redirected to login page. Session/cookies required.")
            print("\n[!] Notice: Taobao requires login. Please run 'python main.py login' to log in and save cookies.\n")
            return []

        # Wait for product container or cards
        try:
            await self.page.wait_for_selector("[class*='item'], [class*='Card']", timeout=8000)
        except Exception as e:
            logger.warning(f"Timeout waiting for standard product selector: {e}")

        # Extract product cards from page
        cards = await self.page.query_selector_all("[class*='item'], [class*='Card'], .Content--content--")
        results: List[ProductItem] = []
        for card in cards[:30]:  # limit top items per page
            html = await card.inner_html()
            item = ProductParser.parse_card_html(html)
            if item and item.title and item.title != "Unknown Title":
                results.append(item)

        logger.info(f"Extracted {len(results)} items for query: '{query.keyword}'")
        return results
