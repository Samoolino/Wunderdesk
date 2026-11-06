# WunderTrading API and MCP capability map

This document records capabilities visible in the current official WunderTrading documentation. It is not proof that a particular connected user profile or exchange key is enabled. Runtime discovery and paper tests remain mandatory.

## Official interfaces

- REST API documentation: https://wundertrading.com/docs/rest-api/
- MCP documentation: https://wundertrading.com/docs/mcp/
- MCP connection guide: https://wundertrading.com/docs/mcp/connections
- Supported exchanges: https://wundertrading.com/en/supported-exchanges

The current MCP connection guide documents the MCP endpoint:
https://mcp.wundertrading.com/mcp

The REST API uses HMAC authentication headers. API and secret values are displayed only once when created. The documentation states up to 10 HMAC API keys per account. IP-whitelisted keys are non-expiring; keys created without whitelisted IPs expire after three months.

## Verified REST capabilities

| Capability | Endpoint | Permission | What it establishes |
|---|---|---|---|
| Read connected profiles | GET /open_api/api_profiles | api_profile:read | Profile code, exchange, status, demo flag and balances |
| Read exchange markets | GET /open_api/markets | None | Supported market symbols and ticker ask/bid/last |
| Read live strategies | GET /open_api/strategies/live | strategy:read | Current strategy states |
| Find strategy | GET /open_api/strategies/:id | strategy:read | Query by strategy ID or clientId |
| Create strategy | POST /open_api/strategies/trade | strategy:write | Create a WunderTrading strategy |
| Cancel strategy | DELETE /open_api/strategies/:id/cancel | strategy:write | Cancel eligible strategies |
| Strategy/order history | History endpoints | strategy:read | Historical strategy and order information |

The profile endpoint returns asset balances with free, used and total values, plus collateral values where applicable. Treat status=active as connected, not as sufficient proof of trading eligibility. Require the exact asset, quote currency, free balance and intended market to pass risk checks.

The markets endpoint returns ticker ask, bid and last prices, market symbol/currencies and market type. The documented schema does not expose full Level-2 order-book depth. Therefore:
- Use the WunderTrading market endpoint for discovery and ticker cross-checking.
- Use exchange-native public WebSocket/REST order-book feeds or another verified depth provider for executable depth.
- Verify timestamps, sequence numbers, symbol mapping and data freshness.
- Never calculate a depth-aware net profit from last price alone.

## Strategy creation boundary

The documented New Trade request includes:
- clientId: caller-supplied unique strategy identifier (32-64 allowed characters).
- exchangeCode: one exchange code.
- pairCode: one market identifier.
- profilesCodes: one or more related active profile codes.
- side, orderType, amount and strategy risk/order settings.

This endpoint creates a WunderTrading strategy. Its documented request shape has one exchangeCode and one pairCode. It does not establish atomic cross-exchange buy/sell execution across two different venues. Do not treat a successful strategy-creation response as proof that both arbitrage legs have executed.

Use a separate two-leg coordinator if the chosen arbitrage requires a buy on Venue A and a sell on Venue B. Each leg needs its own intent, order ID, fill tracking, fee accounting and recovery policy.

The API supports clientId, but do not assume duplicate requests are idempotent until duplicate-clientId behaviour is verified in paper mode and documented. Persist a local intent before calling the endpoint; after timeout, query by clientId and reconcile before retry.

## MCP capabilities

The official MCP documentation lists tools for:
- Supported exchanges and exchange families.
- Exchange markets.
- API profiles.
- Create/edit/delete API profiles.
- Place strategy trade.
- Get strategy and live strategies.
- Edit trade strategy.
- Cancel strategy.
- Close strategy market.
- Place market entry and swing strategies.
- Export strategy and order history.

These are useful platform primitives. The custom Wunder Desk MCP must wrap write-capable tools with the local risk/approval gate. Do not expose an unrestricted direct trading MCP tool to the autonomous strategy agent.

## Venue scope requested

Initial connected venues to discover:
- Binance
- MEXC
- Gate
- Phemex
- WOO X
- KuCoin
- Bitget

WunderTrading's public supported-exchange page lists these venues. That does not prove every market type, strategy feature, API operation, account profile or two-leg workflow is supported for every venue. At runtime:
1. Read supported exchanges and exchange families.
2. Read market list for the exact exchange codes.
3. Read connected API profiles and their statuses/balances.
4. Match the intended symbol, market type and profile.
5. Verify strategy/order operation support per venue and market type.
6. Record the result in a capability matrix with tested_at and documentation version.
7. Keep any unverified profile in READ_ONLY or PAPER_ONLY.

## Permissions policy

Initial:
- api_profile:read
- strategy:read
- no strategy:write in the paper-only credential

After paper tests:
- Add strategy:write only to a dedicated execution key stored in AWS Secrets Manager.
- Keep withdrawal permissions disabled on all exchange keys.
- Do not grant profile creation/deletion or other administrative scopes unless a separate operator workflow requires them.
- Do not store the API key or secret in this repository, Vercel client-side variables, Redis, logs or chat history.

## Rate limits and resilience

Read RateLimit-Limit, RateLimit-Remaining and RateLimit-Reset response headers. Respect endpoint weights and apply bounded exponential backoff with jitter on 429 and transient 5xx responses. Do not retry a write blindly after a timeout. Query strategy/order state by clientId or provider ID first.

## Acceptance tests

- Profile discovery returns every intended connected profile and status.
- Free balances are correctly mapped by asset and collateral type.
- Market discovery identifies exact exchange codes and symbol formats.
- Order-book depth is sourced separately and time-aligned with ticker data.
- A strategy can be created in paper mode and read back by clientId.
- Duplicate clientId behaviour is tested.
- Cancel, close, market-enter and status transitions are tested only in paper mode first.
- All requested venues are marked LIVE_ELIGIBLE only after their individual capability matrix passes.
