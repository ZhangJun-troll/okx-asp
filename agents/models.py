"""Shared data models for all agents."""
from pydantic import BaseModel
from typing import Optional
from enum import Enum
from datetime import datetime

class TaskType(str, Enum):
    COLLECT = "collect"
    ANALYZE = "analyze"
    SETTLE = "settle"

class A2AMessage(BaseModel):
    """Agent-to-Agent message envelope."""
    from_agent: str
    to_agent: str
    task_id: str
    task_type: TaskType
    payload: dict
    timestamp: datetime = datetime.utcnow()

class ServiceBill(BaseModel):
    """A2A billing record."""
    bill_id: str
    from_agent: str
    to_agent: str
    amount_wei: int
    service_type: str
    task_id: str

class SentimentResult(BaseModel):
    coin: str
    sentiment_score: float  # -1 to 1
    label: str              # bullish / bearish / neutral
    risk_flags: list[str] = []
    source_count: int = 0

class MarketBrief(BaseModel):
    task_id: str
    user_address: str
    summary: str
    sentiment_index: float
    top_coins: list[SentimentResult]
    risk_alerts: list[str]
    generated_at: datetime = datetime.utcnow()

class OrderRequest(BaseModel):
    user_address: str
    tier: str               # free / basic / premium
    query: str              # user query, e.g. "BTC,ETH market analysis"
    tx_hash: Optional[str] = None
