"""Settlement Agent - X402 micropayment gateway + escrow simulation."""
import uuid
from datetime import datetime
from fastapi import FastAPI
from pydantic import BaseModel

from ..models import A2AMessage, ServiceBill

app = FastAPI(title="ASP Settlement Agent")

# --- In-memory ledger (ponytail: real version uses ASPCore.sol) ---
ledger = {
    "balances": {},       # agent_addr -> balance_wei
    "transactions": [],   # list of all A2A tx records
    "escrow": {},         # order_id -> {user, amount, status}
    "subscriptions": {},  # user_addr -> {tier, expires}
}

PLAN_PRICES = {
    "free":    0,
    "basic":   5_000_000_000_000_000,   # 0.005 ETH
    "premium": 20_000_000_000_000_000,   # 0.02 ETH
}

class EscrowRequest(BaseModel):
    user_address: str
    order_id: str
    amount_wei: int
    plan: str

class DisputeRequest(BaseModel):
    order_id: str
    reason: str

def record_tx(from_addr: str, to_addr: str, amount: int, tx_type: str, task_id: str = ""):
    tx = {
        "tx_id": str(uuid.uuid4()),
        "from": from_addr,
        "to": to_addr,
        "amount_wei": amount,
        "amount_eth": amount / 1e18,
        "type": tx_type,
        "task_id": task_id,
        "timestamp": datetime.utcnow().isoformat(),
        "block": len(ledger["transactions"]) + 1000001,  # mock block number
    }
    ledger["transactions"].append(tx)
    ledger["balances"][to_addr] = ledger["balances"].get(to_addr, 0) + amount
    return tx

@app.post("/a2a/bill")
async def process_bill(bill: ServiceBill):
    """Process A2A service bill. Debit escrow, credit agent."""
    tx = record_tx(
        from_addr="escrow",
        to_addr=bill.to_agent,
        amount=bill.amount_wei,
        tx_type=f"a2a_{bill.service_type}",
        task_id=bill.task_id,
    )
    return {"status": "settled", "tx": tx}

@app.post("/escrow/create")
async def create_escrow(req: EscrowRequest):
    """User deposits funds into escrow for an order."""
    ledger["escrow"][req.order_id] = {
        "user": req.user_address,
        "amount": req.amount_wei,
        "status": "locked",
        "created": datetime.utcnow().isoformat(),
    }
    # Record as on-chain tx
    tx = record_tx(req.user_address, "escrow", req.amount_wei, "deposit", req.order_id)
    return {"status": "escrowed", "order_id": req.order_id, "tx_hash": tx["tx_id"]}

@app.post("/escrow/release/{order_id}")
async def release_escrow(order_id: str):
    """Release escrow to agents after service delivery confirmed."""
    escrow = ledger["escrow"].get(order_id)
    if not escrow:
        return {"error": "order not found"}
    escrow["status"] = "released"
    return {"status": "released", "order_id": order_id}

@app.post("/subscribe")
async def subscribe(user_address: str, plan: str):
    """Process subscription payment."""
    price = PLAN_PRICES.get(plan, 0)
    if price == 0:
        return {"status": "ok", "tier": "free"}
    ledger["subscriptions"][user_address] = {
        "tier": plan,
        "expires": "2026-08-12T00:00:00Z",
        "credits": 30 if plan == "premium" else 5,
    }
    tx = record_tx(user_address, "platform", price, "subscription")
    return {"status": "subscribed", "tier": plan, "tx_hash": tx["tx_id"]}

@app.post("/dispute")
async def raise_dispute(req: DisputeRequest):
    """File a dispute for an order."""
    escrow = ledger["escrow"].get(req.order_id)
    if not escrow:
        return {"error": "order not found"}
    escrow["status"] = "disputed"
    escrow["dispute_reason"] = req.reason
    # ponytail: arbitration rules are in ASPCore.sol, this is the API facade
    return {"status": "dispute_filed", "order_id": req.order_id, "reason": req.reason}

@app.get("/ledger")
async def get_ledger():
    """Full ledger export (block explorer view)."""
    return {
        "total_transactions": len(ledger["transactions"]),
        "total_volume_wei": sum(tx["amount_wei"] for tx in ledger["transactions"]),
        "balances": ledger["balances"],
        "recent_txs": ledger["transactions"][-20:],
        "escrows": ledger["escrow"],
    }

@app.get("/health")
async def health():
    return {"status": "ok", "agent": "settlement", "tx_count": len(ledger["transactions"])}
