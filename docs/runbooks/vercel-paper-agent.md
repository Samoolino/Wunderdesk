# Vercel paper agent — deployment and security

This first slice is a **control-plane proof of concept**, not a continuous scanner, connected WunderTrading adapter, or live trader.

## Deploy
1. Import `Samoolino/Wunderdesk` into Vercel with the repository root as the project root and framework preset **Other**.
2. Set `WUNDERDESK_CONTROL_TOKEN` as a long random server-only secret in Vercel environment variables (never prefix with `NEXT_PUBLIC_`).
3. Deploy the branch preview, then verify `GET /api/status` reports `liveTradingEnabled: false`.
4. Send `POST /api/evaluate` with `Authorization: Bearer <control token>` and a JSON payload containing MEXC spot quotes, timestamp (milliseconds), balance, exchange minimum, fees, slippage, and a *hypothetical* confidence score.
5. Run `npm test` and `npm run check` in CI before promotion.

## Important limitations
- The caller currently supplies all market inputs; they are **not independently verified**. Do not interpret PAPER_CANDIDATE as permission to trade.
- The confidence threshold of 0.87 is a configurable screening assumption, **not a validated win probability**.
- Do not put WunderTrading HMAC secrets or JSON authentication headers in frontend code, URLs, Git, or chat.
- Vercel functions are request-driven and not a substitute for the persistent AWS worker and durable ledger in the existing architecture.
- No `/api/execute` endpoint is present. No write-capable WunderTrading connection is configured.
- Before any live release: implement and test verified HMAC signing against official docs, authenticated profile/balance reads, venue minimums, market-data freshness and order-book depth, durable intent ledger, approvals, fencing, kill switch, reconciliation, and per-trade risk caps. Use an IP-allowlisted AWS execution worker for write credentials.
- No profit, risk-free operation, or execution guarantee is implied.
