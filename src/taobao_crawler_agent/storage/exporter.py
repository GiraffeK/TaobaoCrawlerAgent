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
