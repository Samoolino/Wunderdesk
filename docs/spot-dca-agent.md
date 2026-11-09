# Spot DCA agent — implementation boundary

This first increment provides a Vercel-deployable read-only research dashboard and a deterministic paper-trade risk gate. It does **not** place orders, scan live markets, estimate calibrated probabilities, or access credentials.

## Next milestones

1. Verify WunderTrading API/MCP permissions and exchange profile capabilities against current docs.
2. Add authenticated market data ingestion and persistent event ledger; never store exchange secrets in the client.
3. Implement historical feature pipeline, walk-forward splits, fees/slippage modeling, probability calibration and drift detection.
4. Add a paper execution simulator, reconciliation, idempotency and audit events.
5. Implement a separate persistent worker with fixed outbound IP and durable fencing as described in README. Vercel remains the dashboard/control plane, not a continuous trading worker.
6. Add authenticated operator approvals, kill switch, loss caps, minimum notional validation and explicit manual live-mode review. No live trading until audited and approved.

Run `npm test` and `npm run build` before merging. Configure Vercel from the GitHub repository; this branch is for preview review only.
