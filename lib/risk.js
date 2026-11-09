// Deterministic, fail-closed spot opportunity evaluator. No order placement.
export function evaluateSpotOpportunity(input) {
  const reject = (reason) => ({ decision: "SKIP", reason, mode: "PAPER" });
  if (!input || typeof input !== "object") return reject("INVALID_INPUT");
  const { exchange, marketType, symbol, quoteBalance, allocation, minNotional,
    bid, ask, feeRate, slippageRate, observedAt, now, confidence, maxAgeMs = 15000 } = input;
  if (exchange !== "MEXC" || marketType !== "spot" || !["BTC/USDT", "ETH/USDT"].includes(symbol))
    return reject("UNVERIFIED_MARKET");
  const values = [quoteBalance, allocation, minNotional, bid, ask, feeRate, slippageRate, observedAt, now, confidence, maxAgeMs];
  if (values.some(v => typeof v !== "number" || !Number.isFinite(v))) return reject("INVALID_NUMERIC_DATA");
  if (quoteBalance <= 0 || allocation <= 0 || minNotional <= 0 || bid <= 0 || ask <= 0 ||
      feeRate < 0 || slippageRate < 0 || confidence < 0 || confidence > 1 || maxAgeMs <= 0)
    return reject("INVALID_LIMITS");
  if (now < observedAt || now - observedAt > maxAgeMs) return reject("STALE_MARKET_DATA");
  if (allocation > Math.min(6, quoteBalance * 0.3)) return reject("ALLOCATION_LIMIT");
  if (allocation < minNotional) return reject("BELOW_MIN_NOTIONAL");
  if (confidence < 0.87) return reject("LOW_CONFIDENCE");
  if (ask < bid) return reject("CROSSED_MARKET_REQUIRES_REVIEW");
  const friction = (ask - bid) / ask + 2 * feeRate + 2 * slippageRate;
  if (friction >= 0.02) return reject("COSTS_EXCEED_TARGET");
  return { decision: "PAPER_CANDIDATE", mode: "PAPER", symbol, exchange,
    allocation, estimatedRoundTripCostUsdt: Number((allocation * friction).toFixed(8)),
    confidence, note: "Hypothetical only; confidence is not calibrated or verified." };
}
