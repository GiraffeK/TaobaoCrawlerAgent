import asyncio
from pathlib import Path
from typing import Optional
from playwright.async_api import async_playwright, Browser, BrowserContext, Page
from ..config import settings
from ..utils.logger import setup_logger

logger = setup_logger()


class BrowserManager:
    """Manages browser lifecycle, context persistence, and anti-detection settings."""

    def __init__(self, headless: Optional[bool] = None, user_data_dir: Optional[Path] = None):
        self.headless = headless if headless is not None else settings.headless
        self.user_data_dir = user_data_dir or settings.session_dir
        self._playwright = None
        self._browser = None
        self._context: Optional[BrowserContext] = None

    async def start(self) -> BrowserContext:
        """Launch browser with persistent context to keep login cookies."""
        self._playwright = await async_playwright().start()
        
        args = [
            "--disable-blink-features=AutomationControlled",
            "--no-sandbox",
            "--disable-setuid-sandbox",
            "--disable-infobars",
            "--window-size=1920,1080",
        ]

        logger.info(f"Launching browser (headless={self.headless}) with storage at {self.user_data_dir}")
        self._context = await self._playwright.chromium.launch_persistent_context(
            user_data_dir=str(self.user_data_dir),
            headless=self.headless,
            slow_mo=settings.slow_mo_ms,
            user_agent=settings.user_agent,
            viewport={"width": 1920, "height": 1080},
            args=args,
        )

        # Anti-detect script injection
        await self._context.add_init_script("""
            Object.defineProperty(navigator, 'webdriver', {
                get: () => undefined
            });
        """)

        return self._context

    async def new_page(self) -> Page:
        """Get or create an active page."""
        if not self._context:
            await self.start()
        return await self._context.new_page()

    async def close(self):
        """Clean up and close browser sessions."""
        if self._context:
            await self._context.close()
            self._context = None
        if self._playwright:
            await self._playwright.stop()
            self._playwright = None
        logger.info("Browser closed.")
