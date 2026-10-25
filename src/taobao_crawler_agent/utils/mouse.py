import asyncio
import math
import random
from typing import Tuple, Union, Optional
from playwright.async_api import Page, ElementHandle
from .logger import setup_logger

logger = setup_logger()


def _cubic_bezier(
    p0: Tuple[float, float],
    p1: Tuple[float, float],
    p2: Tuple[float, float],
    p3: Tuple[float, float],
    t: float,
) -> Tuple[float, float]:
    """Calculate point on cubic Bezier curve at parameter t (0.0 to 1.0)."""
    omt = 1.0 - t
    x = (omt**3 * p0[0] +
         3 * omt**2 * t * p1[0] +
         3 * omt * t**2 * p2[0] +
         t**3 * p3[0])
    y = (omt**3 * p0[1] +
         3 * omt**2 * t * p1[1] +
         3 * omt * t**2 * p2[1] +
         t**3 * p3[1])
    return x, y


class HumanMouse:
    """Simulates realistic human mouse trajectories, browsing wandering, and click physics."""

    def __init__(self, page: Page):
        self.page = page
        self.last_pos: Tuple[float, float] = (
            random.uniform(200, 600),
            random.uniform(200, 400),
        )

    async def move_smooth(
        self,
        target_x: float,
        target_y: float,
        steps: int = 25,
        add_jitter: bool = True,
    ):
        """Move mouse from current position to target along a natural Bezier curve with micro-jitter."""
        p0 = self.last_pos
        p3 = (target_x, target_y)

        # Generate realistic curved control points
        dx = p3[0] - p0[0]
        dy = p3[1] - p0[1]
        dist = math.hypot(dx, dy)

        # Deviate sideways
        deviation = min(dist * 0.35, 150.0)
        p1 = (
            p0[0] + dx * random.uniform(0.2, 0.4) + random.uniform(-deviation, deviation),
            p0[1] + dy * random.uniform(0.1, 0.3) + random.uniform(-deviation, deviation),
        )
        p2 = (
            p0[0] + dx * random.uniform(0.6, 0.8) + random.uniform(-deviation, deviation),
            p0[1] + dy * random.uniform(0.7, 0.9) + random.uniform(-deviation, deviation),
        )

        # Dynamic step count based on distance
        adjusted_steps = max(15, min(45, int(dist / 25)))

        for i in range(1, adjusted_steps + 1):
            t = i / adjusted_steps
            # Non-linear easing (slow down near target - Fitts's Law)
            eased_t = math.sin(t * math.pi / 2)
            cur_x, cur_y = _cubic_bezier(p0, p1, p2, p3, eased_t)

            if add_jitter and i < adjusted_steps:
                cur_x += random.gauss(0, 1.2)
                cur_y += random.gauss(0, 1.2)

            await self.page.mouse.move(cur_x, cur_y)
            # Human micro-pause between movement steps (8ms ~ 20ms)
            await asyncio.sleep(random.uniform(0.008, 0.022))

        self.last_pos = (target_x, target_y)

    async def wander(self, times: int = 2):
        """Simulate a human user browsing, glancing at screen, moving mouse around casually."""
        viewport = self.page.viewport_size or {"width": 1920, "height": 1080}
        w = viewport["width"]
        h = viewport["height"]

        for _ in range(times):
            # Pick a random plausible viewing region on screen
            rand_x = random.uniform(w * 0.15, w * 0.75)
            rand_y = random.uniform(h * 0.15, h * 0.75)
            await self.move_smooth(rand_x, rand_y)
            # Brief pause as if human is reading/looking at an item
            await asyncio.sleep(random.uniform(0.3, 0.8))

    async def hover_and_click(
        self,
        element: Union[ElementHandle, str],
        wander_first: bool = True,
        wander_times: int = 1,
    ) -> bool:
        """
        Human-like interaction:
        1. Optionally wander around (滑鼠滑來滑去)
        2. Smoothly approach the target element
        3. Hover briefly
        4. Click with realistic down/up delay
        """
        # Resolve element handle if selector string passed
        el_handle = element
        if isinstance(element, str):
            el_handle = await self.page.query_selector(element)
            if not el_handle:
                logger.warning(f"Element not found for selector: {element}")
                return False

        # Ensure element is scrolled into view so coordinates are within viewport
        try:
            await el_handle.scroll_into_view_if_needed(timeout=3000)
            await asyncio.sleep(0.3)
        except Exception as e:
            logger.debug(f"scroll_into_view_if_needed failed or timed out: {e}")

        box = await el_handle.bounding_box()
        if not box:
            logger.warning("Could not obtain bounding box for element, falling back to direct click.")
            await el_handle.click()
            return True

        # 1. Wander around first if requested (simulate browsing)
        if wander_first:
            await self.wander(times=wander_times)

        # 2. Pick a natural click coordinate inside the bounding box (avoid extreme borders)
        target_x = box["x"] + random.uniform(box["width"] * 0.2, box["width"] * 0.8)
        target_y = box["y"] + random.uniform(box["height"] * 0.2, box["height"] * 0.8)

        # 3. Smoothly move to target
        await self.move_smooth(target_x, target_y)

        # 4. Hover pause (human eye confirms mouse is on button)
        await asyncio.sleep(random.uniform(0.18, 0.42))

        # 5. Click with realistic mouse down/up delay (80ms ~ 160ms)
        await self.page.mouse.down()
        await asyncio.sleep(random.uniform(0.08, 0.16))
        await self.page.mouse.up()

        logger.debug(f"Human-clicked element at ({target_x:.1f}, {target_y:.1f})")
        return True

