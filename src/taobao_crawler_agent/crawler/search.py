import asyncio
import random
import urllib.parse
from typing import List, Set, Optional
from playwright.async_api import Page
from ..models import ProductItem, SearchQuery
from .parser import ProductParser
from ..utils.mouse import HumanMouse
from ..utils.logger import setup_logger

logger = setup_logger()


class TaobaoSearchScraper:
    """Automates Taobao multi-page querying, smooth scrolling, anti-slider detection, and item card extraction."""

    TAOBAO_SEARCH_URL = "https://s.taobao.com/search"

    SLIDER_SELECTORS = [
        "#nc_1_n1z",
        "[class*='nc_iconfont']",
        "#baxia-dialog-content",
        "iframe[src*='punish']",
        "[class*='secsdk-captcha']",
        ".nc_scale",
        "[class*='punish']",
    ]

    def __init__(self, page: Page):
        self.page = page

    async def _handle_slider(self, timeout_sec: int = 35) -> bool:
        """Detect and allow user to manually resolve Alibaba WAF slider captcha."""
        has_slider = False
        if "punish" in self.page.url:
            has_slider = True
        else:
            for sel in self.SLIDER_SELECTORS:
                try:
                    el = await self.page.query_selector(sel)
                    if el and await el.is_visible():
                        has_slider = True
                        break
                except Exception:
                    pass

        if has_slider:
            print("\n" + "=" * 65)
            print("[⚠️  偵測到淘寶安全驗證碼（WAF 滑塊 / 證明非機器人）]")
            print(">> 請在彈出的瀏覽器視窗中，手動將滑塊拖動至最右邊以完成驗證！")
            print(f">> 程式將在背景等候您滑動（最多等候 {timeout_sec} 秒）...")
            print("=" * 65 + "\n")

            for i in range(timeout_sec):
                await asyncio.sleep(1.0)
                still_has_slider = False
                if "punish" in self.page.url:
                    still_has_slider = True
                else:
                    for sel in self.SLIDER_SELECTORS:
                        try:
                            el = await self.page.query_selector(sel)
                            if el and await el.is_visible():
                                still_has_slider = True
                                break
                        except Exception:
                            pass

                if not still_has_slider:
                    print("[✓] 滑塊驗證成功通過！繼續進行後續爬取任務...\n")
                    await asyncio.sleep(2.0)
                    return True

            logger.warning("Slider captcha timed out without resolution.")
            return False
        return True

    async def _smooth_scroll(self, steps: int = 5):
        """Scroll down smoothly in steps to trigger lazy loading of product cards and images."""
        logger.debug("Executing smooth scroll with human mouse wandering...")
        mouse = HumanMouse(self.page)
        for i in range(steps):
            scroll_delta = random.randint(700, 1100)
            await self.page.mouse.wheel(0, scroll_delta)
            # Casually move mouse around as a human reading titles
            if i % 2 == 1:
                await mouse.wander(times=1)
            else:
                await asyncio.sleep(random.uniform(0.6, 1.1))
        await asyncio.sleep(1.0)

    async def _dismiss_popups(self):
        """Dismiss common login popups or overlays if present."""
        try:
            close_selectors = [
                "[class*='close-btn']",
                "[class*='dialog-close']",
                ".bui-dialog-close",
                "button[aria-label='Close']",
                "[class*='Login--close']",
            ]
            for sel in close_selectors:
                btn = await self.page.query_selector(sel)
                if btn and await btn.is_visible():
                    await btn.click()
                    await asyncio.sleep(0.5)
                    break
        except Exception:
            pass

    def _build_search_url(self, keyword: str, page_no: int, query: Optional[SearchQuery] = None) -> str:
        """Construct standard, natural Taobao search URL."""
        s_offset = (page_no - 1) * 44
        params = {
            "q": keyword,
            "page": page_no,
            "s": s_offset,
            "tab": "all",
        }
        if query and query.sort_by:
            params["sort"] = query.sort_by

        return f"{self.TAOBAO_SEARCH_URL}?{urllib.parse.urlencode(params)}"

    async def _navigate_to_next_page(self, page_no: int, keyword: str, query: Optional[SearchQuery] = None) -> bool:
        """Attempt to click the pagination button with human trajectories, falling back to clean direct URL offset."""
        mouse = HumanMouse(self.page)
        
        # 1. Scroll down smoothly to make pagination bar fully visible
        try:
            await self.page.evaluate("window.scrollTo({top: document.body.scrollHeight, behavior: 'smooth'});")
            await asyncio.sleep(1.2)
        except Exception:
            pass

        # 2. First strategy: Click specific page number button (e.g. '2')
        target_clicked = False
        try:
            page_selectors = [
                f"[class*='pagination'] button:text-is('{page_no}')",
                f"[class*='Pagination'] button:text-is('{page_no}')",
                f"button.next-pagination-item:text-is('{page_no}')",
                f"[class*='pagination'] [role='button']:text-is('{page_no}')",
                f"[class*='pagination'] li:text-is('{page_no}')",
                f"[class*='pagination'] a:text-is('{page_no}')",
            ]
            for sel in page_selectors:
                page_btn = await self.page.query_selector(sel)
                if page_btn and await page_btn.is_visible():
                    logger.info(f"Found page number button '{page_no}' via '{sel}'. Moving mouse with human trajectory and clicking...")
                    clicked = await mouse.hover_and_click(page_btn, wander_first=True, wander_times=1)
                    if clicked:
                        target_clicked = True
                        break

            # If specific page number button not found/clickable, try the '下一页' button
            if not target_clicked:
                next_selectors = [
                    "button.next-next:not([disabled])",
                    "button.next-pagination-item.next-next:not([disabled])",
                    "[class*='pagination'] button:has-text('下一页'):not([disabled])",
                    "[class*='Pagination'] button:has-text('下一页'):not([disabled])",
                    "button[aria-label*='下一页']:not([disabled])",
                    "button[aria-label*='Next page']:not([disabled])",
                ]
                for sel in next_selectors:
                    next_btn = await self.page.query_selector(sel)
                    if next_btn and await next_btn.is_visible():
                        logger.info(f"Found next page button via '{sel}'. Moving mouse with human trajectory and clicking...")
                        clicked = await mouse.hover_and_click(next_btn, wander_first=True, wander_times=1)
                        if clicked:
                            target_clicked = True
                            break

            if target_clicked:
                # Give the SPA frontend 3.5 seconds to complete AJAX fetch and re-render cards
                logger.info(f"Pagination click dispatched for page {page_no}. Waiting for SPA content to update...")
                await asyncio.sleep(3.5)
                # Smoothly scroll back to top of the new page
                try:
                    await self.page.evaluate("window.scrollTo({top: 0, behavior: 'smooth'});")
                    await asyncio.sleep(1.0)
                except Exception:
                    pass
                return True
        except Exception as e:
            logger.debug(f"Click pagination attempt failed: {e}")

        # 3. Fallback strategy: Direct URL navigation ONLY if no pagination button was clickable at all
        if not target_clicked:
            url = self._build_search_url(keyword, page_no, query)
            logger.info(f"No pagination button found; falling back to direct URL navigation for page {page_no}: {url}")
            try:
                await self.page.goto(url, wait_until="domcontentloaded", timeout=25000)
                await asyncio.sleep(3.0)
                return True
            except Exception as e:
                logger.warning(f"Failed to navigate to page {page_no} via URL: {e}")
                return False

        return True

    async def search(self, query: SearchQuery) -> List[ProductItem]:
        """Execute multi-page search on Taobao and extract clean organic cards (zero ad pollution)."""
        max_pages = max(1, query.max_pages)
        all_results: List[ProductItem] = []
        seen_ids: Set[str] = set()

        for page_no in range(1, max_pages + 1):
            if page_no == 1:
                url = self._build_search_url(query.keyword, 1, query)
                logger.info(f"Navigating to page 1/{max_pages}: {url}")
                try:
                    await self.page.goto(url, wait_until="domcontentloaded", timeout=25000)
                except Exception as e:
                    logger.warning(f"Timeout navigating to page 1: {e}")
            else:
                success = await self._navigate_to_next_page(page_no, query.keyword, query)
                if not success:
                    break

            # Handle slider captcha if triggered
            await self._handle_slider()

            # Check if redirected to login page completely
            if "login.taobao.com" in self.page.url:
                logger.warning("Taobao redirected to login page. Session/cookies required.")
                print("\n[!] Notice: Taobao requires login. Please run 'python main.py login' to log in and save cookies.\n")
                break

            # Dismiss floating modal if possible
            await self._dismiss_popups()

            # Wait for organic product cards
            try:
                await self.page.wait_for_selector(
                    "[class*='Content--content--'], [class*='Card--doubleCardWrapper--'], a[href*='item.taobao.com'], a[href*='detail.tmall.com']",
                    timeout=8000
                )
            except Exception as e:
                logger.warning(f"Timeout waiting for product cards on page {page_no}: {e}")

            # Smooth scroll to load bottom products
            await self._smooth_scroll(steps=5)

            # Check slider again after scroll
            await self._handle_slider()

            # Query all organic product cards on current page (ignore simba ad containers)
            card_selectors = [
                "[class*='Content--content--'] > div",
                "[class*='Card--doubleCardWrapper--']",
                "[class*='Item--item--']",
                "a[href*='item.taobao.com']",
                "a[href*='detail.tmall.com']",
            ]
            cards = []
            for sel in card_selectors:
                found = await self.page.query_selector_all(sel)
                if len(found) > len(cards):
                    cards = found

            page_items_count = 0
            min_floor = query.min_price_floor or 0.0
            for card in cards:
                outer_html = await card.evaluate("el => el.outerHTML")
                item = ProductParser.parse_card_html(outer_html, min_price_floor=min_floor, target_keyword=query.keyword)
                if item and item.title and item.title != "Unknown Title":
                    # Deduplicate by item_id or detail_url
                    unique_key = item.item_id or item.detail_url
                    if unique_key and unique_key not in seen_ids:
                        seen_ids.add(unique_key)
                        all_results.append(item)
                        page_items_count += 1

            logger.info(f"Page {page_no}: extracted {page_items_count} new items (Total accumulated: {len(all_results)})")

            # Human-like delay between pages
            if page_no < max_pages:
                delay = random.uniform(2.5, 4.0)
                logger.debug(f"Waiting {delay:.1f}s before next page...")
                await asyncio.sleep(delay)

        return all_results
