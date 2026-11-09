# Spot DCA paper decision engine

This module is intentionally **paper-only**. It has no exchange credentials, network access, MCP tools, or order-submission functions. It evaluates hypothetical entries and returns an explicit rejection reason.

Run tests: `python -m unittest discover -s tests -v`.

## Input requirements

Supply a **calibrated** probability of reaching the profit target before the stop or expiry. `evidence_validated` must be set only after independent walk-forward validation; the code does not itself validate predictions. A fixed 87% input is **not** proof of an 87% win rate.

Supply a fresh timestamp, independently verified available MEXC spot balance, minimum order notional, and an all-in estimate of fees and slippage. This version does **not** ingest market data, verify those flags, execute DCA safety orders, train models, or connect to WunderTrading.

The mathematical score is `stake * (p * gain_fraction - (1-p) * loss_fraction - roundtrip_cost_fraction)`. This is an illustrative two-outcome model; gaps, partial fills, and fat-tailed losses may invalidate its assumptions. Do not use this score alone to authorize real orders.

## Integration boundary

A future scanner should populate Candidate from verified sources; a future ledger should provide realized profit, daily loss, and open-position counts. The production execution gateway must independently enforce the full contract in `docs/trading/execution-safety-contract.md`, including authorization, lease/fencing, durable idempotency, order-book depth, live balance reconciliation, and manual approval. **Never connect the Decision.eligible flag directly to a live order API.**

Default stake limit is 30% of verified free quote balance; a $20 account implies at most $6, which may be below the exchange minimum. No profit is assured.
