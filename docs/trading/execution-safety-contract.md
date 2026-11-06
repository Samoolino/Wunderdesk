# Live execution safety contract

## Purpose

The agent may discover, analyse and prepare trading opportunities across connected exchange profiles. It may submit live orders only through a server-side execution gateway after all mandatory checks pass. Chat text is an instruction request, not a bypass of risk controls.

## Command contract

The agent/MCP surface should expose bounded operations such as:

- get_system_status
- list_connected_profiles
- get_profile_balances
- get_market_snapshot
- get_order_book
- scan_opportunities
- evaluate_strategy
- prepare_trade_intent
- request_live_approval
- execute_approved_intent
- get_order_status
- reconcile_execution
- pause_new_orders
- resume_paper_scanning

No tool should expose withdrawal, transfer, arbitrary signed requests, raw API secrets, or an unrestricted generic order endpoint.

## Mandatory pre-trade gates

A live intent is rejected unless all conditions are true:

1. The operator has explicitly enabled live mode and approved the strategy/intent according to the configured approval policy.
2. The connected profile is active and its permissions match the intended market and operation.
3. The correct pair and market type are supported on both venues.
4. Both sides have sufficient free balances, after existing reservations and open orders.
5. Market data timestamps are within the configured freshness window.
6. The buy-side ask and sell-side bid are executable for the intended quantity.
7. Order-book depth supports the quantity without exceeding the slippage limit.
8. Fees, spread, slippage, funding/borrow costs and other applicable charges are included.
9. Minimum order sizes, tick sizes, quantity steps and notional limits pass.
10. Expected net profit meets the configured threshold in the configured quote currency.
11. Exposure, per-venue allocation, daily loss, concurrent trade and drawdown limits pass.
12. No duplicate intent, conflicting position or unresolved previous order exists.
13. The active worker owns a valid lease and current fencing token.
14. The API capability matrix confirms the exact operation is supported for the selected venue/profile.
15. The order gateway and durable execution ledger are available.

Any missing, stale, ambiguous or contradictory input means REJECT, not best-effort execution.

## Profit calculation

For a pre-funded cross-exchange spot arbitrage:

    expected_net_profit =
      executable_sell_proceeds
      - executable_buy_cost
      - buy_fee
      - sell_fee
      - expected_slippage
      - other_applicable_costs

The quantity must be constrained by both order-book depth and available balances. The scanner's displayed last price or percentage spread is not an execution price.

A $20 minimum expected net profit can be a configurable gate, but it is not a guarantee of realised profit. Slippage, latency, partial fills, fees, market movement, venue outages and API uncertainty can still cause losses. The system must have explicit maximum exposure and maximum loss controls.

## Two-leg execution

Cross-exchange arbitrage is not considered complete after creating a strategy object or submitting one leg.

The coordinator must:
1. Persist a unique trade intent before submission.
2. Reserve/validate capital on both venues.
3. Submit the buy and sell legs using supported order parameters.
4. Record provider responses and exchange order IDs.
5. Monitor fills, partial fills, rejects and cancellations.
6. Reconcile actual filled quantities and fees.
7. Hedge, reduce or quarantine residual exposure according to a pre-approved recovery policy.
8. Mark the intent terminal only after both legs and resulting inventory are reconciled.

Do not assume WunderTrading's strategy-creation endpoint atomically executes both sides across two exchanges. Prove the exact behaviour through API documentation and paper tests. If it cannot provide the required two-leg lifecycle, implement a separately controlled coordinator using supported venue APIs, or do not enable that arbitrage strategy.

## Venue capability matrix

Each venue/profile must be individually tested. Do not infer that a connected profile supports every market, endpoint or order type.

Initial venues requested for assessment:
- Binance
- MEXC
- Gate
- Phemex
- WOO X
- KuCoin
- Bitget

For each profile, record:
- profile read and balance read support
- supported market types (spot, futures, perpetual)
- ticker and order-book depth availability
- symbol/pair mapping
- create, query, cancel and close order support
- supported order types and time-in-force
- precision, min quantity and min notional
- fee schedule and fee currency
- rate limits and error semantics
- client order ID / idempotency support
- strategy API support and required scopes
- whether the operation is available through WunderTrading or requires a direct venue adapter

A venue is LIVE_ELIGIBLE only after all capabilities required by a selected strategy are verified and tested.

## Failure policy

- Stale market data: reject intent.
- Insufficient free funds: reject intent.
- Profit below threshold: reject intent.
- Missing order-book depth: reject intent.
- API timeout before confirmed submission: query/reconcile before retry.
- Timeout after possible submission: mark UNKNOWN and reconcile; never blindly retry.
- Partial fill: enter recovery workflow; do not submit a duplicate full-size order.
- Coordinator/ledger unavailable: stop all new live submissions.
- Worker loses lease or fencing token: stop all new live submissions immediately.
- Exchange profile permissions change: disable that profile until revalidated.
- Any unexplained position/order: quarantine strategy and request operator review.

## Initial rollout states

1. PAPER: market scans, balance reads, simulated intents, no live orders.
2. SHADOW: compare proposed decisions with real market data and record hypothetical fills; no live orders.
3. APPROVED_PILOT: manually approved live intents, tightly capped capital and concurrency.
4. LIMITED_AUTOMATION: only after pilot acceptance, with explicit caps and emergency stop.
5. GENERAL_LIVE: requires a separate reviewed release and operational sign-off.

The repository baseline remains PAPER. A production deployment must not switch to a higher state through a chat prompt alone.

## Required acceptance evidence

- Tests for stale data, price movement, fee/slippage thresholds and insufficient balances.
- Tests for duplicate commands and replayed webhook/MCP requests.
- Tests for partial fills, order rejects and ambiguous timeouts.
- Tests for primary-worker loss and standby takeover.
- Tests proving a stale worker cannot submit after lease loss.
- Tests proving both EIPs are allowlisted and can independently perform read-only API calls.
- Audit trail linking agent command, strategy decision, approval, trade intent, provider request, order ID, fills and reconciliation.
