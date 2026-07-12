"""A2A inter-agent HTTP client. X402 payment header included."""
import httpx
import uuid
from .models import A2AMessage, TaskType

AGENTS = {
    "dispatcher": "http://localhost:8001",
    "collector":  "http://localhost:8002",
    "analyst":    "http://localhost:8003",
    "settlement": "http://localhost:8004",
}

async def send_task(to_agent: str, task_type: TaskType, payload: dict, from_agent: str = "dispatcher") -> dict:
    msg = A2AMessage(
        from_agent=from_agent,
        to_agent=to_agent,
        task_id=str(uuid.uuid4()),
        task_type=task_type,
        payload=payload,
    )
    url = f"{AGENTS[to_agent]}/a2a/task"
    async with httpx.AsyncClient(timeout=30) as client:
        r = await client.post(url, json=msg.model_dump(mode="json"))
        r.raise_for_status()
        return r.json()

async def send_bill(bill: dict) -> dict:
    url = f"{AGENTS['settlement']}/a2a/bill"
    async with httpx.AsyncClient(timeout=10) as client:
        r = await client.post(url, json=bill)
        r.raise_for_status()
        return r.json()
