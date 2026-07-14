"""Analyst Agent - Sentiment analysis via keyword heuristics (no ML libs needed)."""
import uuid
from datetime import datetime
from fastapi import FastAPI

from ..models import A2AMessage, SentimentResult

app = FastAPI(title="ASP Analyst Agent")

BULLISH = {"bullish", "moon", "pump", "rally", "breakout", "surge", "ath", "buy",
           "accumulate", "undervalued", "halving", "adoption", "optimism", "growth",
           "upside", "recovery", "demand", "institutional", "etf", "approval"}

BEARISH = {"bearish", "dump", "crash", "scam", "rug", "hack", "exploit", "sell",
           "overvalued", "ponzi", "fraud", "vulnerability", "fear", "capitulation",
           "liquidation", "collapse", "ban", "regulation", "lawsuit", "investigation"}

RISK_KW = {"rug", "scam", "hack", "exploit", "ponzi", "fraud", "vulnerability",
            "phishing", "fake", "suspicious", "malicious", "drained", "compromised"}

def score_text(text: str) -> float:
    """Simple keyword sentiment: -1 to +1."""
    words = set(text.lower().split())
    bull = len(words & BULLISH)
    bear = len(words & BEARISH)
    total = bull + bear
    if total == 0:
        return 0.0
    return round((bull - bear) / total, 3)

def analyze_sentiment(texts: list[str], coin: str) -> SentimentResult:
    coin_texts = [t for t in texts if coin.upper() in t.upper() or coin.lower() in t.lower()]
    if not coin_texts:
        return SentimentResult(coin=coin, sentiment_score=0, label="neutral", source_count=0)

    scores = [score_text(t) for t in coin_texts]
    avg = sum(scores) / len(scores)
    label = "bullish" if avg > 0.15 else ("bearish" if avg < -0.15 else "neutral")

    risk_flags = []
    for t in coin_texts:
        lower = t.lower()
        for kw in RISK_KW:
            if kw in lower:
                risk_flags.append(f"⚠️ {coin}: '{kw}' in {t[:80]}")
                break

    return SentimentResult(
        coin=coin, sentiment_score=avg, label=label,
        risk_flags=risk_flags[:5], source_count=len(coin_texts),
    )

def generate_recommendations(results: list[SentimentResult]) -> list[dict]:
    """Generate investment suggestions based on sentiment scores."""
    recs = []
    for r in results:
        if r.sentiment_score > 0.25:
            action = "📈 建议关注" if r.sentiment_score < 0.5 else "📈 强烈建议关注"
            reason = f"{r.coin}情绪看涨({r.sentiment_score:+.2f})，市场共识积极"
            recs.append({"coin": r.coin, "action": action, "reason": reason, "risk": "中"})
        elif r.sentiment_score < -0.25:
            action = "⚠️ 建议谨慎" if r.sentiment_score > -0.5 else "⚠️ 建议回避"
            reason = f"{r.coin}情绪看跌({r.sentiment_score:+.2f})，市场恐慌情绪明显"
            recs.append({"coin": r.coin, "action": action, "reason": reason, "risk": "高"})
        else:
            action = "🔍 建议观望"
            reason = f"{r.coin}情绪中性({r.sentiment_score:+.2f})，暂无明确方向"
            recs.append({"coin": r.coin, "action": action, "reason": reason, "risk": "低"})

    # Flag coins with risk alerts
    for rec in recs:
        for r in results:
            if r.coin == rec["coin"] and r.risk_flags:
                rec["risk"] = "高"
                rec["reason"] += f"（⚠️ 检测到{len(r.risk_flags)}条风险信号）"

    return recs

def detect_anomalies(data: dict) -> list[str]:
    alerts = []
    for tx in data.get("whale_transactions", []):
        if tx["usd"] > 3_000_000:
            alerts.append(f"🐋 Whale: {tx['amount']:,.0f} {tx['token']} (${tx['usd']:,.0f})")
    for item in data.get("news_items", []):
        lower = (item.get("title", "") + " " + item.get("summary", "")).lower()
        for kw in RISK_KW:
            if kw in lower:
                alerts.append(f"🚨 Risk '{kw}': {item['title'][:60]}")
                break
    return alerts[:10]

@app.post("/a2a/task")
async def handle_task(msg: A2AMessage):
    data = msg.payload
    texts = [(i.get("title", "") + " " + i.get("summary", "")) for i in data.get("news_items", [])]
    coins = data.get("coins_mentioned", ["BTC", "ETH"])
    results = [analyze_sentiment(texts, c) for c in coins]
    results.sort(key=lambda r: r.sentiment_score, reverse=True)
    risk_alerts = detect_anomalies(data)
    recommendations = generate_recommendations(results)
    overall = sum(r.sentiment_score for r in results) / len(results) if results else 0

    return {
        "status": "completed",
        "task_id": msg.task_id,
        "data": {
            "sentiment_index": round(overall, 3),
            "coin_sentiments": [r.model_dump() for r in results],
            "risk_alerts": risk_alerts,
            "recommendations": recommendations,
            "analyzed_at": datetime.utcnow().isoformat(),
        },
        "bill": {
            "bill_id": str(uuid.uuid4()),
            "from_agent": "analyst",
            "to_agent": "settlement",
            "amount_wei": 200_000_000_000_000,
            "service_type": "data_analysis",
            "task_id": msg.task_id,
        }
    }

@app.get("/health")
async def health():
    return {"status": "ok", "agent": "analyst"}
