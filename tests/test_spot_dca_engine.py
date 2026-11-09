import unittest
from dataclasses import replace
from datetime import datetime, timezone, timedelta
from decimal import Decimal as D
from spot_dca.engine import Candidate, Policy, evaluate

NOW = datetime(2026, 11, 9, tzinfo=timezone.utc)

def valid():
    return Candidate(probability=D("0.87"), gain_fraction=D("0.02"),
        loss_fraction=D("0.01"), roundtrip_cost_fraction=D("0.002"),
        stake=D("6"), free_quote=D("20"), min_notional=D("5"),
        timestamp=NOW, evidence_validated=True, balance_verified=True,
        market_rules_verified=True)

class PaperEngineTests(unittest.TestCase):
    def test_positive_expected_value(self):
        result = evaluate(valid(), now=NOW)
        self.assertTrue(result.eligible)
        self.assertEqual(result.expected_net, D("0.0846"))

    def test_no_unverified_probability(self):
        self.assertEqual(evaluate(replace(valid(), evidence_validated=False), now=NOW).reason, "uncalibrated_probability")

    def test_no_stale_snapshot(self):
        self.assertEqual(evaluate(replace(valid(), timestamp=NOW-timedelta(seconds=11)), now=NOW).reason, "stale_market_data")

    def test_no_excess_allocation(self):
        self.assertEqual(evaluate(replace(valid(), stake=D("7")), now=NOW).reason, "allocation_limit")

    def test_no_below_minimum(self):
        self.assertEqual(evaluate(replace(valid(), min_notional=D("10")), now=NOW).reason, "below_min_notional")

    def test_no_negative_edge(self):
        self.assertEqual(evaluate(replace(valid(), roundtrip_cost_fraction=D("0.03")), now=NOW).reason, "insufficient_expected_edge")

    def test_no_unverified_balance(self):
        self.assertEqual(evaluate(replace(valid(), balance_verified=False), now=NOW).reason, "unverified_account_or_market")

    def test_no_trade_after_target(self):
        self.assertEqual(evaluate(replace(valid(), realized_net_profit=D("5")), now=NOW).reason, "profit_target_reached")

    def test_no_trade_after_daily_loss(self):
        self.assertEqual(evaluate(replace(valid(), daily_realized_loss=D("1")), now=NOW).reason, "daily_loss_limit")

    def test_no_trade_when_position_open(self):
        self.assertEqual(evaluate(replace(valid(), open_positions=1), now=NOW).reason, "position_limit")

    def test_no_derivatives(self):
        self.assertEqual(evaluate(replace(valid(), market_type="futures"), now=NOW).reason, "unsupported_market")

if __name__ == "__main__":
    unittest.main()
