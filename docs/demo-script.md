# OKX-ASP Demo Video Script
**Duration:** 4 minutes | **Language:** English

---

## Scene 1: Opening (0:00 - 0:30)

**[Screen: OKX-ASP landing page with agent cluster visualization]**

**Narrator:** "What if AI agents could trade intelligence with each other, settling payments autonomously on the blockchain? Welcome to OKX-ASP — the Agentic Service Provider built on X-Layer. Four specialized AI agents form an autonomous economy: collecting crypto data, analyzing market sentiment, and settling micropayments between themselves — all without human intervention."

---

## Scene 2: Architecture Overview (0:30 - 1:15)

**[Screen: Architecture diagram — 4 agents with arrows showing data flow]**

**Narrator:** "Our system runs four agents as independent microservices. The Dispatcher orchestrates workflows. The Collector crawls news from CoinDesk, CoinTelegraph, and Decrypt in real-time. The Analyst scores sentiment from -1 to +1 for each cryptocurrency. And the Settlement Agent processes X402 micropayments between agents on X-Layer."

**[Show: Terminal with agent health checks — all 4 green]**

**Narrator:** "Each agent runs on its own port, communicates via REST APIs, and charges for its services through on-chain settlement."

---

## Scene 3: Live Demo — Submit Order (1:15 - 2:15)

**[Screen: Demo UI — submit order form]**

**Narrator:** "Let's submit a market analysis request. I'll select the Basic plan, enter BTC, ETH, and SOL as the coins to analyze, and hit Submit."

**[Click Submit button. Show agents transitioning to "Processing" status]**

**Narrator:** "Watch the agent cluster. The Collector is now fetching real-time news from three RSS feeds. The Analyst is scoring sentiment for each coin. And the Settlement Agent is processing micropayment bills."

**[Wait for results to appear]**

---

## Scene 4: Results (2:15 - 3:15)

**[Screen: Completed results — sentiment index, coin chips, risk alerts, market brief]**

**Narrator:** "Results are in. The Market Sentiment Index shows 0.033 — neutral territory. ETH is bullish at plus-33 percent based on our keyword analysis. We detected 3 risk alerts: two whale transactions totaling over 8 million dollars, and a real exploit story — Bonzo Lend lost 9 million dollars on Hedera."

**[Scroll to Market Brief]**

**Narrator:** "The AI-generated brief summarizes everything in one view: sentiment index, top movers, and risk flags."

---

## Scene 5: On-Chain Settlement (3:15 - 3:45)

**[Screen: A2A Settlement Ledger table]**

**Narrator:** "Now look at the settlement ledger. Two A2A transactions were recorded: the Collector charged 0.0001 ETH for data collection, and the Analyst charged 0.0002 ETH for sentiment analysis. Both settled through our X402 protocol, recorded with block numbers for full auditability."

**[Show: Smart contract code snippet]**

**Narrator:** "All of this is governed by our ASPCore smart contract on X-Layer — subscriptions, escrow, agent payments, and dispute arbitration in 350 lines of Solidity."

---

## Scene 6: Closing (3:45 - 4:00)

**[Screen: OKX-ASP logo + GitHub link]**

**Narrator:** "OKX-ASP is fully open source under MIT license. Four agents, one autonomous economy, built on X-Layer. Check out our GitHub and join the Agent Economy."

**[Text overlay: github.com/[team]/okx-asp | #OKXAI]**
