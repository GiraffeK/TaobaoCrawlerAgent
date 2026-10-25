import re
from typing import Optional, Dict, Any
from bs4 import BeautifulSoup
from ..models import ProductItem
from ..utils.logger import setup_logger

logger = setup_logger()


class ProductParser:
    """Parses raw HTML / DOM elements into structured ProductItem models and evaluates search relevance."""

    # Category disqualifiers: not a standalone GPU (整機、工控機、筆電、配件、圖紙)
    DISQUALIFIERS = [
        "主机", "整机", "工控机", "服务器", "笔记本", "台式机", "机箱",
        "图纸", "原理图", "点位图", "电路图",
        "维修", "修显卡", "坏卡", "尸体", "显卡支架", "散热风扇", "散热器", "散热片",
        "风扇", "外壳", "空盒", "模型", "显卡伴侣", "改水冷", "水冷头", "延长线", "转接线",
        "定金", "订金", "定金专拍", "补差价", "差价", "专拍", "链接", "运费", "押金", "租赁", "咨询"
    ]

    @classmethod
    def evaluate_relevance(
        cls,
        title: str,
        price: float = 0.0,
        target_keyword: str = "rtx3080",
        min_price_floor: float = 0.0,
    ) -> tuple[int, bool, Optional[str]]:
        """
        Evaluate whether the card title and price indicate a genuinely relevant product
        and whether it is worth clicking into for deep SKU inspection.
        Returns: (score: 0~100, is_worthy: bool, rejection_reason: Optional[str])
        """
        lower_title = title.lower()
        score = 80
        reason = None

        # 1. Hard Disqualifiers Check
        for kw in cls.DISQUALIFIERS:
            if kw in lower_title:
                return 10, False, f"包含排除關鍵字（配件/整機/維修/定金）: '{kw}'"

        # 2. Target Keyword Presence
        # Normalize target keyword: e.g. "rtx3080" -> check "3080"
        clean_target = re.sub(r"[^a-zA-Z0-9]", "", target_keyword.lower())
        if "3080" in clean_target and "3080" not in lower_title:
            return 20, False, "標題未包含目標核心型號 3080"

        # 3. Keyword Stuffing Detection (多型號雜貨鋪/引流陷阱)
        # Check how many distinct GPU models are crammed into title
        gpu_matches = re.findall(r"(?:rtx|gtx)?\s*(10[5-8]0|20[6-8]0|30[5-9]0|40[6-9]0|50[5-9]0)(?:\s*ti|\s*super)?", lower_title)
        unique_models = set(gpu_matches)
        if len(unique_models) >= 4:
            score -= 35
            reason = f"標題堆砌多達 {len(unique_models)} 種顯卡型號，疑似多規格拼裝或引流賣場"
        elif len(unique_models) >= 2:
            score -= 15

        # 4. Positive Core Subject Bonus
        if "显卡" in lower_title or "独显" in lower_title:
            score += 15
        if "10g" in lower_title or "12g" in lower_title or "涡轮" in lower_title or "oc" in lower_title:
            score += 10

        # 5. Price Sanity & Floor Check
        if min_price_floor > 0 and price > 0 and price < min_price_floor:
            return 15, False, f"標價 ¥{price:.2f} 低於安全價格底線 ¥{min_price_floor:.2f}（疑似定金/假標價）"

        if price > 20000.0:
            score -= 40
            reason = f"標價 ¥{price:.2f} 異常過高，疑似多卡伺服器或整機"

        final_score = max(0, min(100, score))
        is_worthy = final_score >= 50
        return final_score, is_worthy, reason

    @staticmethod
    def parse_price(raw_text: str) -> float:
        """Extract true float price from string like '¥ 129.00' avoiding concatenated sales counts."""
        if not raw_text:
            return 0.0
        cleaned = raw_text.replace(",", "")
        # Priority 1: Match directly after currency symbol ¥ (\u00a5) or ￥ (\uffe5)
        m = re.search(r"[\u00a5\uffe5]\s*(\d+(?:\.\d+)?)", cleaned)
        if m:
            return float(m.group(1))
        # Priority 2: Float/integer anchored at start of string
        m = re.search(r"^\s*(\d+(?:\.\d+)?)", cleaned)
        if m:
            return float(m.group(1))
        # Fallback
        m = re.search(r"(\d+(?:\.\d+)?)", cleaned)
        return float(m.group(1)) if m else 0.0

    @classmethod
    def parse_card_html(cls, html_snippet: str, min_price_floor: float = 0.0, target_keyword: str = "rtx3080") -> Optional[ProductItem]:
        """Parse individual item card element and score its relevance, strictly rejecting ads."""
        soup = BeautifulSoup(html_snippet, "html.parser")
        
        # 1. Reject sponsored ads (Simba / 直通車) or store links immediately
        link_el = soup.select_one("a[href*='item.taobao.com'], a[href*='detail.tmall.com']")
        if not link_el or not link_el.get("href"):
            link_el = soup.select_one("a[href*='id=']")
            if not link_el or not link_el.get("href"):
                return None

        raw_href = link_el["href"]
        if any(bad in raw_href for bad in ["simba.taobao.com", "store.taobao.com", "shop.taobao.com"]):
            return None

        if raw_href.startswith("//"):
            raw_href = "https:" + raw_href

        # 2. Extract genuine item ID
        item_id = None
        item_id_match = re.search(r"[?&]id=(\d+)", raw_href)
        if item_id_match:
            item_id = item_id_match.group(1)
        else:
            card_id = soup.get("data-item-id") or soup.get("data-id") or soup.get("data-nid")
            if card_id and card_id.isdigit():
                item_id = str(card_id)

        if not item_id:
            return None

        # Clean direct canonical link
        detail_url = f"https://item.taobao.com/item.htm?id={item_id}"

        # 3. Title extraction
        title_el = soup.select_one("[class*='title'], [class*='Title--'], .title, .item-title, h3, a[title]")
        title = ""
        if title_el:
            title = title_el.get("title") or title_el.get_text(strip=True)
        if not title:
            img_el = soup.select_one("img[alt]")
            if img_el and img_el.get("alt"):
                title = img_el["alt"].strip()
        if not title:
            return None

        # 4. Clean Price extraction (prefer priceInt + priceFloat over raw text to avoid sales concatenation)
        price_int_el = soup.select_one("[class*='priceInt'], [class*='Price--priceInt--']")
        price_float_el = soup.select_one("[class*='priceFloat'], [class*='Price--priceFloat--']")
        if price_int_el:
            int_txt = re.sub(r"\D", "", price_int_el.get_text(strip=True))
            float_txt = re.sub(r"\D", "", price_float_el.get_text(strip=True)) if price_float_el else "0"
            try:
                price = float(f"{int_txt}.{float_txt}") if int_txt else 0.0
            except ValueError:
                price = 0.0
        else:
            price_el = soup.select_one("[class*='Price--price--'], [class*='price'], .price")
            price = cls.parse_price(price_el.get_text(strip=True)) if price_el else 0.0

        # 5. Sales volume extraction
        sales_el = soup.select_one("[class*='realSales'], [class*='Price--realSales--'], [class*='deal-cnt'], [class*='sales']")
        sales = sales_el.get_text(strip=True) if sales_el else None
        if not sales:
            for span in soup.select("span, div"):
                t = span.get_text(strip=True)
                if any(k in t for k in ["人付款", "人收货", "已售", "人买过"]):
                    sales = t
                    break

        # 6. Shop name extraction
        shop_el = soup.select_one("[class*='shopName'], [class*='ShopInfo--shopName--'], [class*='shopname'], .shop")
        shop = shop_el.get_text(strip=True) if shop_el else None

        # 7. Shipping origin / location extraction
        loc_el = soup.select_one("[class*='procity'], [class*='Price--procity--'], [class*='location']")
        location = loc_el.get_text(strip=True) if loc_el else None

        # 8. High-res product thumbnail image extraction
        img_el = soup.select_one("img[src*='alicdn.com'], img[data-src*='alicdn.com'], img[src*='taobaocdn.com']")
        image_url = None
        if img_el:
            image_url = img_el.get("src") or img_el.get("data-src")
            if image_url and image_url.startswith("//"):
                image_url = "https:" + image_url

        # 9. Badges / Trust attributes (退貨寶、老店、金牌賣家等)
        badges = []
        for badge_el in soup.select("[class*='Icon--icon--'], [class*='badge'], [class*='tag']"):
            txt = badge_el.get_text(strip=True)
            if txt and len(txt) <= 8 and txt not in badges:
                badges.append(txt)

        extra = {}
        if badges:
            extra["badges"] = badges

        # 10. Relevance and Worthiness Scoring
        score, is_worthy, reason = cls.evaluate_relevance(title, price, target_keyword, min_price_floor)

        return ProductItem(
            item_id=item_id,
            title=title,
            price=price,
            sales_count=sales,
            shop_name=shop,
            location=location,
            detail_url=detail_url,
            image_url=image_url,
            is_bait=not is_worthy,
            relevance_score=score,
            rejection_reason=reason,
            extra_attributes=extra,
        )

