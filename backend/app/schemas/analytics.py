from typing import List, Dict, Any, Optional
from pydantic import BaseModel

class AnalyticsSummary(BaseModel):
    total: int
    completed: int
    in_progress: int
    todo: int
    overdue: int
    due_today: int
    completion_rate: int
    high_priority_pending: int

class TrendItem(BaseModel):
    date: str
    completed: int
    created: int

class DistributionItem(BaseModel):
    name: str
    count: int
    percentage: float

class AnalyticsDistribution(BaseModel):
    by_status: List[DistributionItem]
    by_priority: List[DistributionItem]
    by_category: List[DistributionItem]

class ProductivityInsight(BaseModel):
    type: str  # info, success, warning
    title: str
    message: str

class AnalyticsInsightsResponse(BaseModel):
    insights: List[ProductivityInsight]
    most_active_category: Optional[str] = None
    fastest_completion_day: Optional[str] = None
