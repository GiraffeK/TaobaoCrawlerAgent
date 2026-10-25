from typing import List, Optional
from ..models import ProductItem, SearchQuery, AgentAnalysisResult
from ..crawler.browser import BrowserManager
from ..crawler.search import TaobaoSearchScraper
from ..storage.exporter import DataExporter
from ..utils.logger import setup_logger

logger = setup_logger()


class TaobaoAgent:
    """Intelligent agent that handles user search queries, crawling, and recommendation."""

    def __init__(self, headless: bool = True):
        self.browser_manager = BrowserManager(headless=headless)
        self.exporter = DataExporter()

    async def run_search(self, query_text: str, max_items: int = 20) -> AgentAnalysisResult:
        """Execute autonomous search, extraction, and ranking."""
        logger.info(f"Agent starting search mission for: '{query_text}'")
        
        # 1. Start browser
        page = await self.browser_manager.new_page()
        scraper = TaobaoSearchScraper(page)

        try:
            # 2. Scrape results
            query = SearchQuery(keyword=query_text)
            items = await scraper.search(query)
            
            # 3. Simple heuristic analysis / ranking (LLM can be connected here)
            valid_items = [item for item in items if item.price > 0]
            valid_items.sort(key=lambda x: x.price)

            prices = [it.price for it in valid_items] if valid_items else [0.0]
            min_p = min(prices) if prices else 0.0
            max_p = max(prices) if prices else 0.0
            avg_p = sum(prices) / len(prices) if prices else 0.0

            summary = (
                f"Searched '{query_text}'. Found {len(valid_items)} products. "
                f"Price range: ¥{min_p:.2f} ~ ¥{max_p:.2f} (Average: ¥{avg_p:.2f})."
            )

            result = AgentAnalysisResult(
                query=query_text,
                total_found=len(valid_items),
                top_recommendations=valid_items[:5],
                summary=summary,
                price_range={"min": min_p, "max": max_p, "avg": round(avg_p, 2)},
            )
            return result
        finally:
            await self.browser_manager.close()
