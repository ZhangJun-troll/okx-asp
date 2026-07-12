// SPDX-License-Identifier: MIT
pragma solidity ^0.8.19;

import "@openzeppelin/contracts/access/Ownable.sol";
import "@openzeppelin/contracts/security/ReentrancyGuard.sol";

/// @title ASPCore - Agentic Service Provider Core Contract
/// @notice Deployed on X-Layer (OKX L2). Handles subscriptions, escrow, A2A payments, arbitration.
contract ASPCore is Ownable, ReentrancyGuard {
    enum Tier { FREE, BASIC, PREMIUM }
    enum OrderStatus { Pending, Active, Completed, Disputed, Refunded }

    struct Subscription {
        Tier tier;
        uint256 expiresAt;
        uint256 reportCredits;
    }

    struct AgentService {
        address agentAddr;
        string agentType;       // "collector", "analyst", "settlement"
        uint256 pricePerTask;   // in wei (X402 micropayment)
        uint256 tasksCompleted;
        uint256 totalEarned;
        bool active;
    }

    struct ServiceOrder {
        address user;
        string requestHash;     // IPFS hash of request params
        uint256 escrowAmount;
        OrderStatus status;
        uint256 createdAt;
        address assignedAgents[3]; // dispatcher assigns up to 3 sub-agents
    }

    struct Dispute {
        uint256 orderId;
        address initiator;
        string reason;
        bool resolved;
        bool refundApproved;
    }

    // --- State ---
    mapping(address => Subscription) public subscriptions;
    mapping(uint256 => ServiceOrder) public orders;
    mapping(uint256 => Dispute) public disputes;
    mapping(address => AgentService) public agents;

    uint256 public orderCounter;
    uint256 public disputeCounter;

    uint256 public constant BASIC_PRICE = 0.005 ether;
    uint256 public constant PREMIUM_PRICE = 0.02 ether;
    uint256 public constant PLATFORM_FEE_BPS = 200; // 2%

    // --- Events ---
    event Subscribed(address user, Tier tier, uint256 expiresAt);
    event OrderCreated(uint256 orderId, address user, uint256 amount);
    event OrderCompleted(uint256 orderId);
    event A2APayment(address from, address to, uint256 amount, string serviceType);
    event DisputeRaised(uint256 disputeId, uint256 orderId);
    event DisputeResolved(uint256 disputeId, bool refundApproved);
    event AgentRegistered(address agent, string agentType, uint256 price);

    constructor() Ownable(msg.sender) {}

    // --- User: Subscribe ---
    function subscribe(Tier tier) external payable {
        require(tier != Tier::FREE, "Free tier needs no payment");
        uint256 price = tier == Tier::BASIC ? BASIC_PRICE : PREMIUM_PRICE;
        require(msg.value >= price, "Insufficient payment");

        uint256 duration = 30 days;
        subscriptions[msg.sender] = Subscription({
            tier: tier,
            expiresAt: block.timestamp + duration,
            reportCredits: tier == Tier::PREMIUM ? 30 : 5
        });

        emit Subscribed(msg.sender, tier, block.timestamp + duration);
    }

    // --- User: Create Order (深度报告/单次付费) ---
    function createOrder(string calldata requestHash) external payable nonReentrant {
        require(msg.value > 0, "Payment required");
        uint256 orderId = orderCounter++;

        orders[orderId] = ServiceOrder({
            user: msg.sender,
            requestHash: requestHash,
            escrowAmount: msg.value,
            status: OrderStatus::Pending,
            createdAt: block.timestamp,
            assignedAgents: [address(0), address(0), address(0)]
        });

        emit OrderCreated(orderId, msg.sender, msg.value);
    }

    // --- Agent: Register (A2A identity) ---
    function registerAgent(string calldata agentType, uint256 pricePerTask) external {
        agents[msg.sender] = AgentService({
            agentAddr: msg.sender,
            agentType: agentType,
            pricePerTask: pricePerTask,
            tasksCompleted: 0,
            totalEarned: 0,
            active: true
        });
        emit AgentRegistered(msg.sender, agentType, pricePerTask);
    }

    // --- Dispatcher: Assign agents to order ---
    function assignAgents(uint256 orderId, address[3] calldata agentAddrs) external {
        ServiceOrder storage order = orders[orderId];
        require(order.status == OrderStatus::Pending, "Not pending");
        // ponytail: only dispatcher role checked in production, skip for demo
        order.assignedAgents = agentAddrs;
        order.status = OrderStatus::Active;
    }

    // --- Settlement Agent: Pay sub-agent (A2A X402 micropayment) ---
    function settleA2A(uint256 orderId, address agentAddr) external nonReentrant {
        ServiceOrder storage order = orders[orderId];
        require(order.status == OrderStatus::Active, "Not active");

        AgentService storage agent = agents[agentAddr];
        require(agent.active, "Agent not active");

        uint256 fee = (agent.pricePerTask * PLATFORM_FEE_BPS) / 10000;
        uint256 payout = agent.pricePerTask - fee;

        (bool ok, ) = agentAddr.call{value: payout}("");
        require(ok, "Transfer failed");

        agent.tasksCompleted++;
        agent.totalEarned += payout;
        order.escrowAmount -= agent.pricePerTask;

        emit A2APayment(address(this), agentAddr, payout, agent.agentType);
    }

    // --- Settlement: Complete order, release remaining escrow ---
    function completeOrder(uint256 orderId) external nonReentrant {
        ServiceOrder storage order = orders[orderId];
        require(order.status == OrderStatus::Active, "Not active");
        require(order.escrowAmount > 0, "Nothing to refund");

        (bool ok, ) = order.user.call{value: order.escrowAmount}("");
        require(ok, "Refund failed");

        order.escrowAmount = 0;
        order.status = OrderStatus::Completed;
        emit OrderCompleted(orderId);
    }

    // --- Dispute ---
    function raiseDispute(uint256 orderId, string calldata reason) external {
        ServiceOrder storage order = orders[orderId];
        require(order.user == msg.sender, "Not order owner");

        uint256 disputeId = disputeCounter++;
        disputes[disputeId] = Dispute({
            orderId: orderId,
            initiator: msg.sender,
            reason: reason,
            resolved: false,
            refundApproved: false
        });
        order.status = OrderStatus::Disputed;
        emit DisputeRaised(disputeId, orderId);
    }

    function resolveDispute(uint256 disputeId, bool approveRefund) external onlyOwner {
        Dispute storage d = disputes[disputeId];
        require(!d.resolved, "Already resolved");
        d.resolved = true;
        d.refundApproved = approveRefund;

        ServiceOrder storage order = orders[d.orderId];
        if (approveRefund && order.escrowAmount > 0) {
            (bool ok, ) = d.initiator.call{value: order.escrowAmount}("");
            require(ok, "Refund failed");
            order.escrowAmount = 0;
            order.status = OrderStatus::Refunded;
        }
        emit DisputeResolved(disputeId, approveRefund);
    }

    // --- Queries ---
    function getOrder(uint256 orderId) external view returns (ServiceOrder memory) {
        return orders[orderId];
    }

    function getSubscription(address user) external view returns (Subscription memory) {
        return subscriptions[user];
    }

    function isSubscribed(address user) external view returns (bool) {
        Subscription memory sub = subscriptions[user];
        return sub.tier != Tier::FREE && block.timestamp < sub.expiresAt;
    }
}
