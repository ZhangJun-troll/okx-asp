# OKX-ASP: Agentic Service Provider on X-Layer

Multi-Agent crypto sentiment intelligence platform built for **OKX-AI-Genesis Hackathon**.

## Architecture

```
User → Dispatcher Agent → Collector Agent → Analyst Agent → Brief
         ↕                    ↕                 ↕
      Settlement Agent ←──── A2A X402 Micropayments ────→ Chain
```

| Agent | Port | Role |
|-------|------|------|
| Dispatcher | 8001 | Orchestrator, receives user orders, coordinates workflow |
| Collector | 8002 | 24/7 data ingestion: news RSS, whale TXs, social media |
| Analyst | 8003 | Sentiment scoring, risk detection, anomaly flagging |
| Settlement | 8004 | X402 micropayments, escrow, dispute arbitration |

## Quick Start

```bash
# 1. Install dependencies
pip install -r requirements.txt
python -m textblob.download_corpora

# 2. Start all agents
python run_agents.py

# 3. Submit a test order
curl -X POST http://localhost:8001/api/order \
  -H "Content-Type: application/json" \
  -d '{"user_address":"0xDemo","tier":"basic","query":"BTC,ETH,SOL"}'

# 4. Check settlement ledger
curl http://localhost:8004/ledger
```

## Smart Contract (X-Layer)

```bash
cd contracts
npm install
npx hardhat verify --network xlayer-mainnet <DEPLOYED_ADDRESS>
```

Contracts: `contracts/ASPCore.sol` — subscriptions, escrow, A2A settlement, dispute arbitration.

## Pricing

| Plan | Price | Features |
|------|-------|----------|
| Free | 0 | Daily sentiment summary (5 coins) |
| Basic | 0.005 ETH/mo | Deep market report, risk alerts, 5 reports |
| Premium | 0.02 ETH/mo | Full analysis, fund flow, unlimited reports |

## OKX Ecosystem Integration

- **X-Layer L2**: All agents settle payments on X-Layer (chain ID 196)
- **X402 Protocol**: HTTP 402 + on-chain micropayment for A2A services
- **OKX Agent Payment Protocol**: Subscription & escrow management
- **OKX DEX API**: Real-time whale transaction monitoring (planned)

## License

MIT
