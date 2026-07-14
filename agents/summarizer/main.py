"""Summarizer Agent - Aggregates data from other agents into a final report."""
import uuid
from datetime import datetime
from fastapi import FastAPI

from ..models import A2AMessage

app = FastAPI(title="ASP Summarizer Agent")

@app.post("/a2a/task")
async def handle_task(msg: A2AMessage):
    """Takes raw analysis data and produces a structured summary."""
    data = msg.payload
    coins = data.get("coin_sentiments", [])
    alerts = data.get("risk_alerts", [])
    recs = data.get("recommendations", [])
    index = data.get("sentiment_index", 0)

    # Build structured summary
    summary = {
        "overall": "看涨" if index > 0.15 else ("看跌" if index < -0.15 else "中性"),
        "index": index,
        "top_movers": [c for c in coins if abs(c.get("sentiment_score", 0)) > 0.1][:3],
        "risk_count": len(alerts),
        "high_risk_coins": [c["coin"] for c in coins if c.get("risk_flags")],
        "actionable": [r for r in recs if r.get("action", "").startswith("📈") or r.get("action", "").startswith("⚠️")],
        "generated_at": datetime.utcnow().isoformat(),
    }

    return {
        "status": "completed",
        "task_id": msg.task_id,
        "data": {"summary": summary, "full_data": data},
        "bill": {
            "bill_id": str(uuid.uuid4()),
            "from_agent": "summarizer",
            "to_agent": "settlement",
            "amount_wei": 50_000_000_000_000,  # 0.00005 ETH
            "service_type": "summarization",
            "task_id": msg.task_id,
        }
    }

@app.get("/health")
async def health():
    return {"status": "ok", "agent": "summarizer"}
