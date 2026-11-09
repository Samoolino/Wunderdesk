import test from "node:test";
import assert from "node:assert/strict";
import { evaluateSpotOpportunity } from "../lib/risk.js";
const base = { exchange:"MEXC", marketType:"spot", symbol:"BTC/USDT",
 quoteBalance:20, allocation:5, minNotional:5, bid:99990, ask:100000,
 feeRate:0.001, slippageRate:0.001, observedAt:100000, now:100500, confidence:0.9 };
test("paper candidate never authorizes a live order", () => {
 const result=evaluateSpotOpportunity(base);
 assert.equal(result.decision,"PAPER_CANDIDATE");
 assert.equal(result.mode,"PAPER");
 assert.equal(result.estimatedRoundTripCostUsdt,0.0205);
});
test("rejects stale quotes",()=>assert.equal(evaluateSpotOpportunity({...base,now:200000}).reason,"STALE_MARKET_DATA"));
test("rejects tiny orders below venue minimum",()=>assert.equal(evaluateSpotOpportunity({...base,minNotional:10}).reason,"BELOW_MIN_NOTIONAL"));
test("rejects excess exposure",()=>assert.equal(evaluateSpotOpportunity({...base,allocation:7}).reason,"ALLOCATION_LIMIT"));
test("rejects unverified confidence",()=>assert.equal(evaluateSpotOpportunity({...base,confidence:0.7}).reason,"LOW_CONFIDENCE"));
test("rejects missing fee inputs",()=>assert.equal(evaluateSpotOpportunity({...base,feeRate:undefined}).reason,"INVALID_NUMERIC_DATA"));
test("rejects unsupported exchange and leverage",()=>assert.equal(evaluateSpotOpportunity({...base,marketType:"futures"}).reason,"UNVERIFIED_MARKET"));
test("rejects crossed markets",()=>assert.equal(evaluateSpotOpportunity({...base,bid:100001}).reason,"CROSSED_MARKET_REQUIRES_REVIEW"));
test("rejects excessive costs",()=>assert.equal(evaluateSpotOpportunity({...base,feeRate:0.02}).reason,"COSTS_EXCEED_TARGET"));
