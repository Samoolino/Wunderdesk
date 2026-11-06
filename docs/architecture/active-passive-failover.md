# Active/passive AWS failover

## Decision

Use two independent AWS accounts with two separately allocated Elastic IPs. Account A is active; Account B is a warm standby. Do not plan on transferring the same Elastic IP during an incident.

AWS supports Elastic IP transfers between accounts only in the same Region using a two-account acceptance handshake. The destination account has seven days to accept; an associated address must be disassociated before acceptance. This is useful for planned migration, not a fast automatic failover. Both worker egress IPs should be allowlisted in the WunderTrading API key before production.

## Topology

- Vercel: authenticated command plane, operator approvals, status UI and MCP facade.
- Account A: EC2 primary worker, instance role, Secrets Manager secret, CloudWatch alarms, EIP-A.
- Account B: identical EC2 standby worker, instance role, Secrets Manager secret, CloudWatch alarms, EIP-B.
- Shared coordinator: durable, atomic leader lease and monotonically increasing fencing token, independent of the EC2 worker being failed over.
- Upstash Redis: scanner cache, command/event streams, heartbeats and operational telemetry.
- WunderTrading: centrally managed exchange API profiles and strategy endpoints.

The coordinator must not live exclusively in the account whose worker is being failed over. If using an external coordinator, validate its consistency, durability, availability plan and failure behaviour before live use. The existing Free Upstash database is not approved as the sole live coordinator.

## Worker states

- STANDBY: process is healthy; no live order submission.
- CANDIDATE: primary missed health/lease checks; candidate is reconciling state.
- ACTIVE: owns the current lease and fencing token; can process approved commands.
- DRAINING: stops new orders and finishes/reconciles in-flight work.
- FENCED: lease lost or token superseded; all order submission is disabled.
- QUARANTINED: uncertain order outcome or failed reconciliation; manual review required.

## Failover sequence

1. Health monitor detects primary worker failure using multiple independent signals (EC2 status checks, application heartbeat, coordinator reachability and API connectivity).
2. Primary is marked unhealthy. The system stops dispatching new orders to it.
3. Standby waits for the active lease to expire; it does not infer leadership from a missing heartbeat alone.
4. Standby atomically acquires a new lease and a strictly higher fencing token from the authoritative coordinator.
5. Standby reads the durable execution ledger and queries WunderTrading/exchange order state for every non-terminal intent.
6. Any order with an unknown or partial outcome is reconciled or quarantined. It is never blindly resubmitted.
7. Only after reconciliation does the standby become ACTIVE.
8. The control plane updates the active worker endpoint and emits an audit event.
9. When Account A returns, it starts as STANDBY and cannot trade until explicitly re-elected.

## Single-writer safety

- Every command has a unique command_id and idempotency key.
- Every strategy/order intent has a unique intent_id.
- Every active lease has owner_id, expires_at and monotonically increasing fencing_token.
- Workers must validate the current lease/token immediately before each submission.
- The order gateway rejects stale fencing tokens.
- The execution ledger records intent, submission attempt, provider response, exchange order ID, fills, fees and terminal state.
- If coordinator or ledger access is unavailable, fail closed and stop new live submissions.
- If the external trading API does not support idempotency, reconcile by client order ID/provider order ID and query open/recent orders before retry. Never assume exactly-once delivery.

A fencing token only protects the system if every path to order submission checks it. Do not expose the raw WunderTrading trading credential to a secondary process that can bypass the gateway.

## Credit/billing and capacity triggers

Do not use “AWS credits exhausted” as the only failover signal.

- AWS credits are applied to eligible charges until exhausted or expired.
- If an account is on the AWS Free Plan, AWS requires upgrading to the Paid Plan when Free Tier credits are exhausted or after 184 days, whichever comes first. Do not treat a Free Plan account as an indefinite production host; upgrade and confirm billing before live deployment.
- AWS billing and Budgets data is delayed; AWS says Budgets billing data is updated at least daily. It is not a real-time EC2 health signal.
- Configure budget thresholds and a conservative estimated-cost threshold to start draining Account A before credits run out.
- Also monitor payment method/account health, EC2 status checks, CPU/memory/disk, application heartbeat, worker queue lag and API errors.
- If the primary account is at risk of billing suspension, fail over before the account is suspended. A suspended/closed account may not provide a graceful drain window.
- Keep a payment method and budget alerts in both accounts. Do not rely on promotional credits as uptime guarantees.

## Elastic IP and allowlisting

1. Allocate EIP-A in Account A and EIP-B in Account B in the same workload Region.
2. Configure each worker's outbound route so all WunderTrading REST calls leave through its own EIP.
3. Verify each address using an external IP check from each EC2 instance.
4. Add both addresses to the WunderTrading API key IP allowlist, if the API key UI supports multiple entries.
5. Test each worker's read-only API access independently.
6. Keep both EIPs allocated. Do not release or transfer the standby EIP during routine operation.

If a single IP must be retained for a planned account migration, AWS supports cross-account EIP transfer within the same Region. That process is not the recommended incident failover path.

## Account and role boundaries

- Use IAM Identity Center for human terminal access.
- Use an EC2 instance role in each account for AWS service access.
- Use cross-account IAM roles only for narrowly scoped administration or deployment.
- Do not store long-lived AWS access keys on EC2 or in GitHub.
- Store the WunderTrading API credential in each account's Secrets Manager, encrypted with account-local KMS keys.
- The standby may possess the API credential but must remain unable to submit orders until it owns the current lease and passes reconciliation.

## Acceptance tests

- Kill the primary worker process; standby takes over only after lease expiry.
- Simulate primary network isolation; primary loses permission to submit.
- Restart the primary after failover; it returns as STANDBY.
- Expire or deny the coordinator; both workers stop new orders.
- Simulate a timeout after order submission; standby reconciles before retry.
- Simulate a partial fill; no duplicate full-size order is sent.
- Simulate budget threshold; primary drains before credit exhaustion.
- Confirm both EIPs pass the WunderTrading allowlist independently.
- Verify audit logs show a single active fencing token for each execution interval.
