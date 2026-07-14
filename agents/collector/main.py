"""Collector Agent - Crawls crypto news via HTTP + simple XML parsing."""
import asyncio, uuid, re
from datetime import datetime
from xml.etree import ElementTree as ET
from fastapi import FastAPI
import httpx

from ..models import A2AMessage

app = FastAPI(title="ASP Collector Agent")

RSS_FEEDS = {
    "coindesk":      "https://www.coindesk.com/arc/outboundfeeds/rss/",
    "cointelegraph": "https://cointelegraph.com/rss",
    "decrypt":       "https://decrypt.co/feed",
}

COINS = ["BTC", "ETH", "SOL", "XRP", "DOGE", "AVAX", "LINK", "ADA", "DOT", "MATIC"]

MOCK_WHALE_TXS = [
    {"from": "0xdead...beef", "to": "0x1234...5678", "token": "ETH", "amount": 1200, "usd": 3_840_000},
    {"from": "0xaaaa...bbbb", "to": "0xcccc...dddd", "token": "USDT", "amount": 5_000_000, "usd": 5_000_000},
    {"from": "0x9999...0000", "to": "0x1111...2222", "token": "OKB", "amount": 50_000, "usd": 2_250_000},
]

def _strip_html(text: str) -> str:
    return re.sub(r'<[^>]+>', '', text)[:300]

async def fetch_rss(name: str, url: str) -> list[dict]:
    try:
        async with httpx.AsyncClient(timeout=10, follow_redirects=True) as client:
            r = await client.get(url)
            root = ET.fromstring(r.text)
            items = []
            for item in root.iter("item"):
                title = (item.findtext("title") or "")[:200]
                desc = _strip_html(item.findtext("description") or "")
                link = item.findtext("link") or ""
                pub = item.findtext("pubDate") or ""
                items.append({"title": title, "summary": desc, "link": link, "source": name, "published": pub})
                if len(items) >= 8:
                    break
            return items
    except Exception as e:
        return [{"title": f"[{name} error]", "summary": str(e)[:200], "link": "", "source": name, "published": ""}]

async def collect_news() -> list[dict]:
    tasks = [fetch_rss(n, u) for n, u in RSS_FEEDS.items()]
    results = await asyncio.gather(*tasks)
    return [item for batch in results for item in batch]

@app.post("/a2a/task")
async def handle_task(msg: A2AMessage):
    if msg.task_type.value == "collect":
        news = await collect_news()
        # Agent self-pricing: base + per-item surcharge
        base_price = 80_000_000_000_000     # 0.00008 ETH base
        per_item = 5_000_000_000_000         # 0.000005 ETH per news item
        total_price = base_price + len(news) * per_item

        return {
            "status": "completed",
            "task_id": msg.task_id,
            "data": {
                "news_items": news,
                "whale_transactions": MOCK_WHALE_TXS,
                "coins_mentioned": COINS,
                "collected_at": datetime.utcnow().isoformat(),
            },
            "bill": {
                "bill_id": str(uuid.uuid4()),
                "from_agent": "collector",
                "to_agent": "settlement",
                "amount_wei": total_price,
                "service_type": "data_collection",
                "task_id": msg.task_id,
                "price_breakdown": f"base={base_price/1e18:.6f} + {len(news)} items x {per_item/1e18:.9f}",
            }
        }
    return {"status": "unknown_task"}

@app.get("/health")
async def health():
    return {"status": "ok", "agent": "collector", "sources": list(RSS_FEEDS.keys())}
