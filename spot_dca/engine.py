"""Pure, deterministic spot DCA signal evaluation. No order submission capability."""
from dataclasses import dataclass
from decimal import Decimal
from datetime import datetime, timezone

D = Decimal

@dataclass(frozen=True)
class Policy:
    min_probability: Decimal = D("0.87")
    max_allocation_fraction: Decimal = D("0.30")
    min_net_edge_fraction: Decimal = D("0.002")
    max_snapshot_age_seconds: int = 10
    target_net_profit: Decimal = D("5")
    max_daily_loss: Decimal = D("1")
    max_positions: int = 1

@dataclass(frozen=True)
class Candidate:
    probability: Decimal
    gain_fraction: Decimal
    loss_fraction: Decimal
    roundtrip_cost_fraction: Decimal
    stake: Decimal
    free_quote: Decimal
    min_notional: Decimal
    timestamp: datetime
    realized_net_profit: Decimal = D("0")
    daily_realized_loss: Decimal = D("0")
    open_positions: int = 0
    market_type: str = "spot"
    venue: str = "MEXC"
    symbol: str = "BTC/USDT"
    evidence_validated: bool = False
    balance_verified: bool = False
    market_rules_verified: bool = False

@dataclass(frozen=True)
class Decision:
    eligible: bool
    reason: str
    expected_net: Decimal = D("0")

def evaluate(candidate: Candidate, policy: Policy = Policy(), now: datetime | None = None) -> Decision:
    """Evaluate a hypothetical entry; never submits an order."""
    now = now or datetime.now(timezone.utc)
    if now.tzinfo is None or candidate.timestamp.tzinfo is None:
        return Decision(False, "timezone_required")
    if candidate.market_type != "spot" or candidate.venue != "MEXC":
        return Decision(False, "unsupported_market")
    if not candidate.evidence_validated:
        return Decision(False, "uncalibrated_probability")
    if not candidate.balance_verified or not candidate.market_rules_verified:
        return Decision(False, "unverified_account_or_market")
    if candidate.timestamp > now or (now - candidate.timestamp).total_seconds() > policy.max_snapshot_age_seconds:
        return Decision(False, "stale_market_data")
    values = (candidate.probability, candidate.gain_fraction, candidate.loss_fraction,
              candidate.roundtrip_cost_fraction, candidate.stake, candidate.free_quote,
              candidate.min_notional, candidate.realized_net_profit, candidate.daily_realized_loss)
    if not all(x.is_finite() for x in values):
        return Decision(False, "invalid_numeric_input")
    if not D("0") <= candidate.probability <= D("1") or any(
        x < 0 for x in (candidate.gain_fraction, candidate.loss_fraction,
                        candidate.roundtrip_cost_fraction, candidate.stake,
                        candidate.free_quote, candidate.min_notional)):
        return Decision(False, "invalid_numeric_input")
    if candidate.realized_net_profit >= policy.target_net_profit:
        return Decision(False, "profit_target_reached")
    if candidate.daily_realized_loss >= policy.max_daily_loss:
        return Decision(False, "daily_loss_limit")
    if candidate.open_positions < 0 or candidate.open_positions >= policy.max_positions:
        return Decision(False, "position_limit")
    if candidate.stake <= 0 or candidate.stake < candidate.min_notional:
        return Decision(False, "below_min_notional")
    if candidate.stake > candidate.free_quote * policy.max_allocation_fraction:
        return Decision(False, "allocation_limit")
    if candidate.probability < policy.min_probability:
        return Decision(False, "confidence_below_threshold")
    edge = (candidate.probability * candidate.gain_fraction
            - (D("1") - candidate.probability) * candidate.loss_fraction
            - candidate.roundtrip_cost_fraction)
    expected_net = candidate.stake * edge
    if edge < policy.min_net_edge_fraction:
        return Decision(False, "insufficient_expected_edge", expected_net)
    return Decision(True, "paper_candidate_only", expected_net)
