import asyncio
import re
from typing import Optional, Dict, Any, Tuple
from playwright.async_api import BrowserContext, Page
from ..utils.mouse import HumanMouse
from ..utils.logger import setup_logger

logger = setup_logger()


class TaobaoSkuInspector:
    """Probes into item detail pages, selects targeted SKU specs, and retrieves real prices."""

    SKU_CONTAINER_SELECTORS = [
        "[class*='skuItem']",
        "[class*='sku-item']",
        "[class*='skuProp'] li",
        "[class*='property'] [role='radio']",
        "[class*='SkuContent'] button",
        "[class*='skuValue']",
        "[class*='ItemDetail'] [class*='valueItem']",
    ]

    PRICE_SELECTORS = [
        "[class*='Price--priceText']",
        "[class*='priceText']",
        "[class*='tb-price']",
        "[class*='promo-price']",
        "[class*='price-wrap'] [class*='price']",
        "#J_PromoPriceNum",
        "#J_StrPrice",
    ]

    BAIT_SKU_WORDS = ["定金", "订金", "坏", "维修", "风扇", "外壳", "支架", "瑕疵", "残疾", "散装芯片"]

    def __init__(self, context: BrowserContext):
        self.context = context

    async def _handle_slider(self, page: Page, timeout_sec: int = 30) -> bool:
        """Handle WAF slider verification if encountered in detail page."""
        if "punish" in page.url or await page.query_selector("iframe[src*='punish'], #nc_1_n1z, .nc_scale"):
            print("\n" + "=" * 65)
            print("[⚠️  商品詳情頁觸發淘寶安全驗證碼（滑塊驗證）]")
            print(">> 請在瀏覽器中將滑塊向右拖動完成驗證...")
            print("=" * 65 + "\n")
            for _ in range(timeout_sec):
                await asyncio.sleep(1.0)
                if "punish" not in page.url and not await page.query_selector("iframe[src*='punish'], #nc_1_n1z"):
                    print("[✓] 詳情頁滑塊驗證通過！繼續抓取規格...\n")
                    await asyncio.sleep(1.5)
                    return True
            return False
        return True

    async def inspect_product_sku(
        self,
        detail_url: str,
        target_keyword: str = "3080",
        timeout_ms: int = 20000,
    ) -> Tuple[Optional[str], Optional[float]]:
        """
        Open product page, click matching target SKU, and extract real updated price.
        Returns: (real_sku_name, real_price)
        """
        if not detail_url or not detail_url.startswith("http"):
            return None, None

        # Ignore store links or non-item links
        if "store.taobao.com" in detail_url or "shop.taobao.com" in detail_url:
            logger.debug(f"Skipping store URL: {detail_url}")
            return None, None

        page: Page = await self.context.new_page()
        try:
            logger.info(f"Inspecting detail page for target '{target_keyword}': {detail_url}")
            await page.goto(detail_url, wait_until="domcontentloaded", timeout=timeout_ms)

            # Check slider
            await self._handle_slider(page)

            # Dismiss login or popups if blocking
            try:
                close_btn = await page.query_selector("[class*='close-btn'], [class*='dialog-close'], [aria-label='Close'], .bui-dialog-close")
                if close_btn:
                    await close_btn.click()
            except Exception:
                pass

            await asyncio.sleep(1.2)

            # Look for SKU options
            sku_elements = []
            for sel in self.SKU_CONTAINER_SELECTORS:
                elements = await page.query_selector_all(sel)
                if elements:
                    sku_elements = elements
                    break

            best_sku_text = None
            best_element = None

            target_kw = target_keyword.lower()
            for el in sku_elements:
                text = (await el.inner_text()).strip()
                if not text:
                    continue
                lower_text = text.lower()
                # Must match keyword and avoid obvious bait words
                if target_kw in lower_text:
                    is_bad = any(bw in lower_text for bw in self.BAIT_SKU_WORDS)
                    if not is_bad:
                        best_sku_text = text
                        best_element = el
                        break

            # If matching SKU found, move mouse around and click it to update price
            if best_element:
                mouse = HumanMouse(page)
                logger.info(f"Simulating human mouse browsing & clicking SKU: '{best_sku_text}'...")
                await mouse.hover_and_click(best_element, wander_first=True, wander_times=2)
                await asyncio.sleep(1.5)  # Wait for price JS update

            # Check slider again if triggered by click
            await self._handle_slider(page)

            # Extract current rendered price
            real_price = None
            for p_sel in self.PRICE_SELECTORS:
                p_el = await page.query_selector(p_sel)
                if p_el:
                    raw_text = await p_el.inner_text()
                    match = re.search(r"(\d+(\.\d+)?)", raw_text.replace(",", ""))
                    if match:
                        real_price = float(match.group(1))
                        break

            logger.info(f"Detail inspection completed. SKU: '{best_sku_text}', Real Price: ¥{real_price}")
            return best_sku_text, real_price

        except Exception as e:
            logger.warning(f"Error inspecting detail page {detail_url}: {e}")
            return None, None
        finally:
            await page.close()
