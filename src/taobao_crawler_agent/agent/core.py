import asyncio
from typing import List, Optional
from ..models import ProductItem, SearchQuery, AgentAnalysisResult
from ..crawler.browser import BrowserManager
from ..crawler.search import TaobaoSearchScraper
from ..crawler.sku_inspector import TaobaoSkuInspector
from ..storage.exporter import DataExporter
from ..utils.logger import setup_logger

logger = setup_logger()


class TaobaoAgent:
    """Intelligent agent that handles multi-page crawling, anti-bait filtering, and SKU price inspection."""

    def __init__(self, headless: bool = True):
        self.browser_manager = BrowserManager(headless=headless)
        self.exporter = DataExporter()

    async def run_search(
        self,
        query_text: str,
        max_pages: int = 1,
        deep_sku: bool = False,
        min_price_floor: Optional[float] = None,
        max_sku_inspections: int = 10,
    ) -> AgentAnalysisResult:
        """Execute autonomous multi-page search, anti-bait filtering, and optional deep SKU probing."""
        logger.info(
            f"Agent starting search mission for: '{query_text}' "
            f"(pages={max_pages}, deep_sku={deep_sku}, min_floor={min_price_floor})"
        )

        context = await self.browser_manager.start()
        page = await self.browser_manager.new_page()
        scraper = TaobaoSearchScraper(page)

        try:
            # 1. Multi-page scraping with smooth scroll
            query = SearchQuery(
                keyword=query_text,
                max_pages=max_pages,
                min_price_floor=min_price_floor,
                deep_sku=deep_sku,
                max_sku_inspections=max_sku_inspections,
            )
            raw_items = await scraper.search(query)
            logger.info(f"Total raw items scraped: {len(raw_items)}")

            # 2. Filter bait / fake price items and sort candidates by relevance score
            filtered_items = [item for item in raw_items if not item.is_bait and item.price > 0]
            logger.info(f"Items remaining after bait/floor filtering: {len(filtered_items)}")

            # If all items were flagged as bait or list is empty, fallback to raw valid items
            candidate_items = filtered_items if filtered_items else [it for it in raw_items if it.price > 0]
            # Prioritize candidates with highest relevance score (genuine single-model cards first)
            candidate_items.sort(key=lambda x: x.relevance_score, reverse=True)

            # 3. Optional Deep SKU Inspection on top candidates
            if deep_sku and candidate_items:
                logger.info(f"Starting Deep SKU Inspection on top {min(len(candidate_items), max_sku_inspections)} candidates...")
                inspector = TaobaoSkuInspector(context)
                
                # Check top candidates
                for idx, item in enumerate(candidate_items[:max_sku_inspections]):
                    print(f"[*] Deep inspecting [{idx+1}/{min(len(candidate_items), max_sku_inspections)}] SKU for: {item.title[:35]}...")
                    real_sku, real_price = await inspector.inspect_product_sku(
                        detail_url=item.detail_url,
                        target_keyword=query_text,
                    )
                    if real_sku:
                        item.real_sku = real_sku
                    if real_price and real_price > 0:
                        item.real_price = real_price
                    # Small delay between inspections to prevent WAF throttling
                    await asyncio.sleep(1.5)

            # 4. Sort and rank by effective price (real_price if available, else list price)
            def effective_price(it: ProductItem) -> float:
                return it.real_price if it.real_price and it.real_price > 0 else it.price

            candidate_items.sort(key=effective_price)

            prices = [effective_price(it) for it in candidate_items] if candidate_items else [0.0]
            min_p = min(prices) if prices else 0.0
            max_p = max(prices) if prices else 0.0
            avg_p = sum(prices) / len(prices) if prices else 0.0

            inspected_count = sum(1 for it in candidate_items if it.real_price)
            summary = (
                f"Searched '{query_text}' across {max_pages} pages. Discovered {len(raw_items)} items "
                f"({len(candidate_items)} valid after anti-bait filter). "
                f"{f'Deep verified {inspected_count} SKUs. ' if deep_sku else ''}"
                f"Price range: ¥{min_p:.2f} ~ ¥{max_p:.2f} (Average: ¥{avg_p:.2f})."
            )

            result = AgentAnalysisResult(
                query=query_text,
                total_found=len(candidate_items),
                top_recommendations=candidate_items,
                summary=summary,
                price_range={"min": min_p, "max": max_p, "avg": round(avg_p, 2)},
            )
            return result

        finally:
            await self.browser_manager.close()
