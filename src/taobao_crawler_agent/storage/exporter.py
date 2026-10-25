import csv
import json
from pathlib import Path
from typing import List
from ..models import ProductItem
from ..config import settings
from ..utils.logger import setup_logger

logger = setup_logger()


class DataExporter:
    """Exports scraped product data to CSV, JSON, and other formats."""

    def __init__(self, output_dir: Path = None):
        self.output_dir = output_dir or settings.output_dir
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def export_json(self, items: List[ProductItem], filename: str) -> Path:
        """Save product items to a JSON file."""
        if not filename.endswith(".json"):
            filename += ".json"
        target_path = self.output_dir / filename
        data = [item.model_dump() for item in items]
        with open(target_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        logger.info(f"Saved {len(items)} items to {target_path}")
        return target_path

    def export_csv(self, items: List[ProductItem], filename: str) -> Path:
        """Save product items to a CSV file."""
        if not filename.endswith(".csv"):
            filename += ".csv"
        target_path = self.output_dir / filename
        if not items:
            logger.warning("No items to export to CSV.")
            return target_path

        fieldnames = list(ProductItem.model_fields.keys())
        with open(target_path, "w", newline="", encoding="utf-8-sig") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            for item in items:
                row = item.model_dump()
                # flatten dict attributes if any
                row["extra_attributes"] = json.dumps(row.get("extra_attributes", {}), ensure_ascii=False)
                writer.writerow(row)
        logger.info(f"Saved {len(items)} items to {target_path}")
        return target_path

    def export_markdown_report(
        self,
        query: str,
        items: List[ProductItem],
        summary: str,
        price_range: dict,
        filename: str = "hunter_report"
    ) -> Path:
        """Generate a high-value Executive Buyer's Intelligence Report in Markdown format."""
        if not filename.endswith(".md"):
            filename += ".md"
        target_path = self.output_dir / filename

        valid_items = [it for it in items if not it.is_bait and it.price > 0]
        bait_items = [it for it in items if it.is_bait]

        def get_effective_price(it: ProductItem) -> float:
            return it.real_price if it.real_price and it.real_price > 0 else it.price

        valid_items.sort(key=get_effective_price)

        lines = []
        lines.append(f"# 🛡️ 淘寶獵卡買家決策情報簡報：{query.upper()}\n")
        lines.append(f"> **生成時間**：系統自動即時分析 | **目標品類**：獨立顯卡 (cat=50024403)\n")
        lines.append(f"> **分析摘要**：{summary}\n")
        lines.append("---\n")

        # 1. Executive Summary Table
        min_p = price_range.get("min", 0.0)
        max_p = price_range.get("max", 0.0)
        avg_p = price_range.get("avg", 0.0)
        lines.append("## 📊 市場行情與大盤指標\n")
        lines.append(f"- **有效候選顯卡數量**：`{len(valid_items)}` 張 (已自動剔除 `{len(bait_items)}` 筆定金/工控機/配件雜訊)")
        lines.append(f"- **市場參考價格區間**：`¥ {min_p:.2f} ~ ¥ {max_p:.2f}` (均價：`¥ {avg_p:.2f}`)\n")

        # 2. Key Picks
        lines.append("## 🏆 買家精選情報推薦\n")

        # Pick 1: Best Value
        if valid_items:
            best_val = valid_items[0]
            bv_price = get_effective_price(best_val)
            lines.append(f"### 🥇 【性價比首選】{best_val.title}")
            lines.append(f"- **真實到手價**：**`¥ {bv_price:.2f}`** {'(已深入詳情頁驗證 SKU)' if best_val.real_price else '(外層標價)'}")
            lines.append(f"- **店鋪資訊**：{best_val.shop_name or '優選店鋪'} | **發貨地**：{best_val.location or '未知'}")
            lines.append(f"- **銷量**：{best_val.sales_count or '未標明'}")
            lines.append(f"- **直達購買**：[點擊前往淘寶下單]({best_val.detail_url})\n")

        # Pick 2: Top Reputable Shop
        reputable_items = [it for it in valid_items if it.shop_name and any(k in (it.shop_name or '') for k in ['年', '旗舰', '官方', '金牌'])]
        if reputable_items:
            top_shop = reputable_items[0]
            ts_price = get_effective_price(top_shop)
            lines.append(f"### 🛡️ 【最穩信譽老店推薦】{top_shop.title}")
            lines.append(f"- **真實到手價**：**`¥ {ts_price:.2f}`**")
            lines.append(f"- **老店認證**：**{top_shop.shop_name}** | **發貨地**：{top_shop.location or '未知'}")
            lines.append(f"- **直達購買**：[點擊前往店鋪下單]({top_shop.detail_url})\n")

        # 3. Full Comparison Table
        lines.append("## 📋 候選良品全景比價清單\n")
        lines.append("| 評分 | 商品名稱 | 標價 | 真實SKU價 | 銷量 | 店鋪信譽 | 發貨地 | 直達鏈接 |")
        lines.append("| :---: | :--- | :---: | :---: | :---: | :--- | :---: | :---: |")

        for it in valid_items[:30]:
            p_str = f"¥{it.price:.2f}"
            real_p_str = f"**¥{it.real_price:.2f}**" if it.real_price else f"¥{it.price:.2f}"
            sku_tag = f" ({it.real_sku})" if it.real_sku else ""
            shop_str = it.shop_name or "-"
            loc_str = it.location or "-"
            sales_str = it.sales_count or "-"
            score_icon = "🟢" if it.relevance_score >= 80 else "🟡"
            clean_title = it.title.replace("|", " ")[:32]
            lines.append(f"| {score_icon} {it.relevance_score} | {clean_title} | {p_str} | {real_p_str}{sku_tag} | {sales_str} | {shop_str} | {loc_str} | [前往商品]({it.detail_url}) |")

        # 4. Filtered Blacklist
        if bait_items:
            lines.append("\n## ⚠️ 系統已自動攔截淘汰的無效引流項目 (避坑存檔)\n")
            lines.append("| 淘汰商品標題 | 標價 | 淘汰理由 |")
            lines.append("| :--- | :---: | :--- |")
            for b in bait_items[:15]:
                b_title = b.title.replace("|", " ")[:35]
                b_reason = b.rejection_reason or "疑似配件/定金/異常假價"
                lines.append(f"| {b_title} | ¥{b.price:.2f} | {b_reason} |")

        content = "\n".join(lines)
        with open(target_path, "w", encoding="utf-8") as f:
            f.write(content)

        logger.info(f"Generated Executive Buyer Report: {target_path}")
        return target_path

