"""Dispatcher Agent - Orchestrator. Receives user requests, dispatches to sub-agents, generates briefs."""
import uuid
from datetime import datetime
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import os

from ..models import OrderRequest, A2AMessage, TaskType
from .. import a2a_client

app = FastAPI(title="ASP Dispatcher Agent")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

DEMO_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "demo")

@app.get("/")
async def root():
    return FileResponse(os.path.join(DEMO_DIR, "index.html"))

# --- Order store ---
orders = {}

@app.post("/api/order")
async def create_order(req: OrderRequest):
    """Main entry point. User submits analysis request."""
    order_id = str(uuid.uuid4())
    orders[order_id] = {
        "id": order_id,
        "user": req.user_address,
        "tier": req.tier,
        "query": req.query,
        "status": "processing",
        "started_at": datetime.utcnow().isoformat(),
    }

    # Step 1: Dispatch to Collector
    collector_result = await a2a_client.send_task(
        to_agent="collector",
        task_type=TaskType.COLLECT,
        payload={"query": req.query, "coins": req.query.split(",")},
        from_agent="dispatcher",
    )

    # Step 2: Forward collected data to Analyst
    analyst_result = await a2a_client.send_task(
        to_agent="analyst",
        task_type=TaskType.ANALYZE,
        payload=collector_result.get("data", {}),
        from_agent="dispatcher",
    )

    # Step 3: Submit A2A bills to Settlement
    for bill in [collector_result.get("bill"), analyst_result.get("bill")]:
        if bill:
            await a2a_client.send_bill(bill)

    # Step 4: Generate market brief
    analysis = analyst_result.get("data", {})
    brief = generate_brief(req, analysis)

    orders[order_id]["status"] = "completed"
    orders[order_id]["brief"] = brief
    orders[order_id]["raw_analysis"] = analysis

    return {
        "order_id": order_id,
        "status": "completed",
        "brief": brief,
        "analysis": analysis,
        "collector_items": len(collector_result.get("data", {}).get("news_items", [])),
    }

def generate_brief(req: OrderRequest, analysis: dict) -> dict:
    """Generate formatted market brief from analysis data."""
    coins = analysis.get("coin_sentiments", [])
    top_bullish = [c for c in coins if c.get("label") == "bullish"][:3]
    top_bearish = [c for c in coins if c.get("label") == "bearish"][:3]
    index = analysis.get("sentiment_index", 0)
    zh = getattr(req, 'lang', 'en') == 'zh'
    alerts = analysis.get("risk_alerts", [])

    summary_parts = []
    if zh:
        label = '看漲' if index > 0.15 else ('看跌' if index < -0.15 else '中性')
        summary_parts.append(f"📊 市場情緒指數: {index:.2f} ({label})")
        if top_bullish:
            coins_str = ", ".join(f"{c['coin']}({c['sentiment_score']:+.2f})" for c in top_bullish)
            summary_parts.append(f"🟢 看漲: {coins_str}")
        if top_bearish:
            coins_str = ", ".join(f"{c['coin']}({c['sentiment_score']:+.2f})" for c in top_bearish)
            summary_parts.append(f"🔴 看跌: {coins_str}")
        if alerts:
            summary_parts.append(f"⚠️ 偵測到 {len(alerts)} 條風險預警")
        if req.tier == "free":
            summary_parts.append("⬆️ 升級至基礎版/高級版取得完整風險報告與資金流向分析")
    else:
        summary_parts.append(f"📊 Market Sentiment Index: {index:.2f} ({'Bullish' if index > 0.15 else 'Bearish' if index < -0.15 else 'Neutral'})")
        if top_bullish:
            coins_str = ", ".join(f"{c['coin']}({c['sentiment_score']:+.2f})" for c in top_bullish)
            summary_parts.append(f"🟢 Bullish: {coins_str}")
        if top_bearish:
            coins_str = ", ".join(f"{c['coin']}({c['sentiment_score']:+.2f})" for c in top_bearish)
            summary_parts.append(f"🔴 Bearish: {coins_str}")
        if alerts:
            summary_parts.append(f"⚠️ {len(alerts)} risk alert(s) detected")
        if req.tier == "free":
            summary_parts.append("⬆️ Upgrade to Basic/Premium for full risk report & fund flow analysis")

    return {
        "type": req.tier,
        "query": req.query,
        "summary": "\n".join(summary_parts),
        "sentiment_index": index,
        "top_bullish": top_bullish,
        "top_bearish": top_bearish,
        "risk_alerts": alerts,
        "generated_at": datetime.utcnow().isoformat(),
    }

@app.get("/api/orders")
async def list_orders():
    return {"orders": list(orders.values())[-20:]}

@app.get("/health")
async def health():
    return {"status": "ok", "agent": "dispatcher", "orders_processed": len(orders)}

@app.get("/ledger")
async def proxy_ledger():
    """Proxy to settlement agent's ledger endpoint."""
    import httpx
    async with httpx.AsyncClient(timeout=5) as client:
        r = await client.get("http://localhost:8004/ledger")
        return r.json()
