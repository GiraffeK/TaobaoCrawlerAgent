from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field


class ProductItem(BaseModel):
    """Normalized data model for a scraped Taobao product."""
    item_id: Optional[str] = Field(None, description="Product / Item ID")
    title: str = Field(..., description="Product title")
    price: float = Field(0.0, description="Price in RMB")
    original_price: Optional[float] = Field(None, description="Original reference price")
    sales_count: Optional[str] = Field(None, description="Sales / deal volume text (e.g. 1000+ 人付款)")
    shop_name: Optional[str] = Field(None, description="Shop / Seller name")
    shop_url: Optional[str] = Field(None, description="Shop store URL")
    location: Optional[str] = Field(None, description="Shipping origin location")
    detail_url: str = Field(..., description="Product page link")
    image_url: Optional[str] = Field(None, description="Thumbnail / main image URL")
    real_sku: Optional[str] = Field(None, description="Actual SKU name inspected in detail page")
    real_price: Optional[float] = Field(None, description="Actual verified price for the target SKU")
    is_bait: bool = Field(False, description="Flag indicating suspected bait/fake price")
    relevance_score: int = Field(default=100, description="Relevance score (0-100) indicating confidence it is the target product")
    rejection_reason: Optional[str] = Field(None, description="Reason if marked not worthy or bait")
    extra_attributes: Dict[str, Any] = Field(default_factory=dict, description="Additional properties or badges")


class SearchQuery(BaseModel):
    """Search request parameters."""
    keyword: str
    max_pages: int = Field(default=1, ge=1, le=50)
    sort_by: Optional[str] = Field(None, description="Sort order: default, sales, price_asc, price_desc")
    min_price: Optional[float] = None
    max_price: Optional[float] = None
    min_price_floor: Optional[float] = Field(None, description="Minimum price floor to filter out bait accessories")
    deep_sku: bool = Field(default=False, description="Whether to probe true SKU prices in detail page")
    max_sku_inspections: int = Field(default=10, description="Max candidate products to deeply inspect SKU for")


class AgentAnalysisResult(BaseModel):
    """Analysis result returned by the TaobaoCrawlerAgent."""
    query: str
    total_found: int
    top_recommendations: List[ProductItem] = Field(default_factory=list)
    summary: str = Field(..., description="Summary or decision reasoning from agent")
    price_range: Dict[str, float] = Field(default_factory=dict)

