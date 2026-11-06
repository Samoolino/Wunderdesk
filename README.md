# Wunder Desk V02

Agent-driven, risk-gated trading orchestration for WunderTrading and connected exchanges.

> **Deployment state:** architecture and operational plan only. No live order submission is enabled by this repository baseline. Paper mode is the initial acceptance environment.

## Architecture

- **Vercel:** dashboard, authenticated agent-chat/MCP command surface, operator approvals, status and audit views.
- **AWS Account A:** primary persistent execution worker and fixed outbound Elastic IP.
- **AWS Account B (optional):** independently provisioned warm standby worker and a second fixed outbound Elastic IP.
- **WunderTrading:** exchange profiles, market/account data and strategy/order APIs, subject to verified API scopes and endpoint capabilities.
- **Upstash Redis:** scanner cache, agent command/event streams, heartbeats and operational state.
- **Durable execution ledger / coordinator:** authoritative leader lease, fencing token, idempotency records, order intents, fills and reconciliation. Redis cache state alone must never prove that an order was executed.
- **GitHub:** source of truth, reviewed changes, deployment manifests and runbooks.

## Critical operating rules

1. Start in paper mode. Live mode is a separately gated deployment state.
2. No withdrawal, transfer, or wallet-management capability is permitted.
3. No live order is submitted unless market data is fresh, both required account balances are verified, order-book depth and fees/slippage are included, risk limits pass, and the command is authorized.
4. A cross-exchange arbitrage is a coordinated two-leg workflow. Partial fills, rejected legs, timeouts and uncertain outcomes must be reconciled before retry.
5. Only one worker may hold the execution lease. Failover requires lease expiry, a new fencing token, and reconciliation of all in-flight orders.
6. If the coordinator, ledger, market data, or exchange/WunderTrading API cannot be verified, fail closed: stop new live orders.
7. Do not commit API keys, API secrets, Redis credentials, AWS credentials, .env files, account IDs, or private certificates to Git.

## Deployment sequence

1. Configure WSL2, AWS CLI v2, Terraform and Git.
2. Configure named AWS IAM Identity Center profiles for each account.
3. Deploy Account A in eu-central-1, allocate its Elastic IP, and verify the fixed egress address.
4. Configure a separate standby account only if required; deploy the same immutable image and allocate a distinct Elastic IP.
5. Allowlist both worker egress IPs in the WunderTrading API key. Do not rely on transferring one IP during failover.
6. Configure secrets in AWS Secrets Manager; use EC2 instance roles and temporary AWS credentials.
7. Connect the existing Upstash database for non-critical state and paper testing. Do not use the current Free database as the sole live execution lock/ledger.
8. Implement and test the durable coordinator, execution ledger, fencing, replay protection and failover.
9. Verify WunderTrading API scopes, market-data depth, profile/balance endpoints, strategy creation, order lifecycle, and any required two-leg support.
10. Run paper acceptance tests, then a manually approved, tightly capped live pilot. Automatic live engagement remains disabled until the pilot passes.

## Documentation

- Active/passive AWS failover: docs/architecture/active-passive-failover.md
- WSL2 and AWS CLI runbook: docs/runbooks/wsl2-aws-setup.md
- Live execution safety contract: docs/trading/execution-safety-contract.md

## Current integration observations

The connected Upstash database wunderdeskv02state was reachable during setup (PING returned PONG) and had zero keys. It is on the Free plan in eu-central-1; it is suitable for development/paper testing, not as the sole production execution coordinator.

The GitHub repository was empty when this baseline was prepared. These documents establish the architecture; they do not claim that AWS infrastructure, Vercel environment variables, exchange credentials, or live trading have been configured.
