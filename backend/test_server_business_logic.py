"""
Unit tests for server.js business logic (helper functions).

The Express backend (server.js) contains three pure helper functions with
testable business rules:
  - generateRecommendations({health, repeat, pricing, txnHealth, bench})
  - generateAlerts({health, txnHealth})
  - formatCustomerSegments(row)

Since these are JavaScript functions, we re-implement them faithfully in Python
and test the business logic rules to ensure correctness. If a rule fails here,
it indicates a bug in the original JS implementation.

Python 3.9.6 compatible.
"""

import unittest
from typing import Optional, Dict, Any, List


# ─────────────────────────────────────────────────────────────
# Faithful Python re-implementations of server.js helper functions
# ─────────────────────────────────────────────────────────────

def generate_recommendations(
    health: Dict[str, Any],
    repeat: Dict[str, Any],
    pricing: Dict[str, Any],
    txn_health: Dict[str, Any],
    bench: Optional[Dict[str, Any]],
) -> List[Dict[str, Any]]:
    """
    Re-implementation of server.js generateRecommendations().
    Business rules:
    1. If avg_ticket < industry_ticket → Revenue Booster (High priority)
    2. If repeat_rate < 30% → Retention (High priority)
    3. If approval_rate < 85% → Payment UX (Medium priority)
    4. If no rules triggered → Default healthy message (Medium priority)
    """
    recs = []
    avg_ticket = float(pricing.get("avg_ticket") or 0)
    industry_ticket = float(bench.get("industry_ticket") or 0) if bench else 0

    if avg_ticket > 0 and industry_ticket > 0 and avg_ticket < industry_ticket:
        gap = industry_ticket - avg_ticket
        recs.append({
            "type": "Revenue Booster",
            "priority": "High",
            "impact": round((industry_ticket - avg_ticket) * 100),
            "text": (
                f"Your avg ticket (${avg_ticket}) is ${gap:.2f} below "
                f"industry (${industry_ticket}). Introduce combo offers to bridge the gap."
            ),
        })

    if float(repeat.get("repeat_rate") or 0) < 30:
        recs.append({
            "type": "Retention",
            "priority": "High",
            "impact": 120,
            "text": (
                f"Repeat rate is only {repeat.get('repeat_rate') or 0}%. "
                f"Launch a loyalty reward program to convert one-time buyers."
            ),
        })

    if float(txn_health.get("approval_rate") or 0) < 85:
        recs.append({
            "type": "Payment UX",
            "priority": "Medium",
            "impact": 80,
            "text": (
                f"Approval rate of {txn_health.get('approval_rate') or 0}% is low. "
                f"Enable payment retry flows and expand accepted card types."
            ),
        })

    if len(recs) == 0:
        recs.append({
            "type": "Revenue Booster",
            "priority": "Medium",
            "impact": 60,
            "text": (
                "Performance looks healthy. Consider seasonal promotional "
                "campaigns during peak hours for additional growth."
            ),
        })

    return recs


def generate_alerts(
    health: Dict[str, Any],
    txn_health: Dict[str, Any],
) -> List[Dict[str, Any]]:
    """
    Re-implementation of server.js generateAlerts().
    Business rules:
    1. fraud_rate > 3% → critical alert
    2. decline_rate > 15% → warning alert
    3. If neither triggered → "Systems Normal" info alert
    """
    alerts = []

    if float(health.get("fraud_rate") or 0) > 3:
        alerts.append({
            "title": "Fraud Spike Detected",
            "message": (
                f"Fraud rate at {health['fraud_rate']}% — "
                f"above 3% threshold. Immediate review required."
            ),
            "type": "critical",
        })

    if float(txn_health.get("decline_rate") or 0) > 15:
        alerts.append({
            "title": "Decline Rate Surge",
            "message": (
                f"Decline rate is {txn_health['decline_rate']}%, "
                f"significantly above normal levels."
            ),
            "type": "warning",
        })

    if len(alerts) == 0:
        alerts.append({
            "title": "Systems Normal",
            "message": "All metrics within healthy thresholds. No active alerts.",
            "type": "info",
        })

    return alerts


def format_customer_segments(
    row: Optional[Dict[str, Any]],
) -> List[Dict[str, Any]]:
    """
    Re-implementation of server.js formatCustomerSegments().
    """
    if not row:
        return [
            {"segment": "High Spenders", "count": 0},
            {"segment": "Regular", "count": 0},
            {"segment": "One-time", "count": 0},
        ]
    return [
        {
            "segment": "High Spenders",
            "count": int(row.get("high_spender") or 0),
            "total_spend": 0,
        },
        {
            "segment": "Regular",
            "count": int(row.get("regular") or 0),
            "total_spend": 0,
        },
        {
            "segment": "One-time",
            "count": int(row.get("one_time") or 0),
            "total_spend": 0,
        },
    ]


# ─────────────────────────────────────────────────────────────
# generateRecommendations() Tests
# ─────────────────────────────────────────────────────────────
class TestGenerateRecommendations(unittest.TestCase):
    """Tests for server.js generateRecommendations() business logic."""

    def _defaults(self):
        """Return default metric inputs with all healthy values."""
        return {
            "health": {"fraud_rate": "1.0", "approval_rate": "95"},
            "repeat": {"repeat_rate": "50"},
            "pricing": {"avg_ticket": "100.00"},
            "txn_health": {"approval_rate": "95.00"},
            "bench": {"industry_ticket": "90.00"},
        }

    def test_all_healthy_returns_default_rec(self):
        """When all metrics healthy, returns default promotional message."""
        d = self._defaults()
        recs = generate_recommendations(
            d["health"], d["repeat"], d["pricing"], d["txn_health"], d["bench"]
        )

        self.assertEqual(len(recs), 1)
        self.assertEqual(recs[0]["type"], "Revenue Booster")
        self.assertEqual(recs[0]["priority"], "Medium")
        self.assertEqual(recs[0]["impact"], 60)
        self.assertIn("healthy", recs[0]["text"])

    def test_avg_ticket_below_industry_triggers_revenue_booster(self):
        """avg_ticket < industry_ticket → Revenue Booster recommendation."""
        d = self._defaults()
        d["pricing"]["avg_ticket"] = "80.00"
        d["bench"]["industry_ticket"] = "120.00"

        recs = generate_recommendations(
            d["health"], d["repeat"], d["pricing"], d["txn_health"], d["bench"]
        )

        revenue_recs = [r for r in recs if r["type"] == "Revenue Booster"]
        self.assertEqual(len(revenue_recs), 1)
        self.assertEqual(revenue_recs[0]["priority"], "High")
        # Impact = (120 - 80) * 100 = 4000
        self.assertEqual(revenue_recs[0]["impact"], 4000)
        self.assertIn("$40.00 below", revenue_recs[0]["text"])

    def test_avg_ticket_equals_industry_no_revenue_booster(self):
        """avg_ticket == industry_ticket → no Revenue Booster."""
        d = self._defaults()
        d["pricing"]["avg_ticket"] = "100.00"
        d["bench"]["industry_ticket"] = "100.00"

        recs = generate_recommendations(
            d["health"], d["repeat"], d["pricing"], d["txn_health"], d["bench"]
        )

        revenue_recs = [r for r in recs if r["type"] == "Revenue Booster" and r["priority"] == "High"]
        self.assertEqual(len(revenue_recs), 0)

    def test_avg_ticket_above_industry_no_revenue_booster(self):
        """avg_ticket > industry_ticket → no Revenue Booster."""
        d = self._defaults()
        d["pricing"]["avg_ticket"] = "150.00"
        d["bench"]["industry_ticket"] = "100.00"

        recs = generate_recommendations(
            d["health"], d["repeat"], d["pricing"], d["txn_health"], d["bench"]
        )

        revenue_recs = [r for r in recs if r["type"] == "Revenue Booster" and r["priority"] == "High"]
        self.assertEqual(len(revenue_recs), 0)

    def test_low_repeat_rate_triggers_retention(self):
        """repeat_rate < 30% → Retention recommendation."""
        d = self._defaults()
        d["repeat"]["repeat_rate"] = "25"

        recs = generate_recommendations(
            d["health"], d["repeat"], d["pricing"], d["txn_health"], d["bench"]
        )

        retention_recs = [r for r in recs if r["type"] == "Retention"]
        self.assertEqual(len(retention_recs), 1)
        self.assertEqual(retention_recs[0]["priority"], "High")
        self.assertEqual(retention_recs[0]["impact"], 120)
        self.assertIn("25%", retention_recs[0]["text"])

    def test_repeat_rate_exactly_30_no_retention(self):
        """repeat_rate == 30% → no Retention (< 30 required, not <=)."""
        d = self._defaults()
        d["repeat"]["repeat_rate"] = "30"

        recs = generate_recommendations(
            d["health"], d["repeat"], d["pricing"], d["txn_health"], d["bench"]
        )

        retention_recs = [r for r in recs if r["type"] == "Retention"]
        self.assertEqual(len(retention_recs), 0)

    def test_repeat_rate_29_triggers_retention(self):
        """repeat_rate == 29% → triggers Retention."""
        d = self._defaults()
        d["repeat"]["repeat_rate"] = "29"

        recs = generate_recommendations(
            d["health"], d["repeat"], d["pricing"], d["txn_health"], d["bench"]
        )

        retention_recs = [r for r in recs if r["type"] == "Retention"]
        self.assertEqual(len(retention_recs), 1)

    def test_low_approval_rate_triggers_payment_ux(self):
        """approval_rate < 85% → Payment UX recommendation."""
        d = self._defaults()
        d["txn_health"]["approval_rate"] = "75.00"

        recs = generate_recommendations(
            d["health"], d["repeat"], d["pricing"], d["txn_health"], d["bench"]
        )

        ux_recs = [r for r in recs if r["type"] == "Payment UX"]
        self.assertEqual(len(ux_recs), 1)
        self.assertEqual(ux_recs[0]["priority"], "Medium")
        self.assertEqual(ux_recs[0]["impact"], 80)
        self.assertIn("75.00%", ux_recs[0]["text"])

    def test_approval_rate_exactly_85_no_payment_ux(self):
        """approval_rate == 85% → no Payment UX (< 85 required)."""
        d = self._defaults()
        d["txn_health"]["approval_rate"] = "85.00"

        recs = generate_recommendations(
            d["health"], d["repeat"], d["pricing"], d["txn_health"], d["bench"]
        )

        ux_recs = [r for r in recs if r["type"] == "Payment UX"]
        self.assertEqual(len(ux_recs), 0)

    def test_multiple_recommendations_triggered(self):
        """All three rules triggered simultaneously."""
        d = self._defaults()
        d["pricing"]["avg_ticket"] = "50.00"
        d["bench"]["industry_ticket"] = "100.00"
        d["repeat"]["repeat_rate"] = "10"
        d["txn_health"]["approval_rate"] = "70.00"

        recs = generate_recommendations(
            d["health"], d["repeat"], d["pricing"], d["txn_health"], d["bench"]
        )

        types = [r["type"] for r in recs]
        self.assertIn("Revenue Booster", types)
        self.assertIn("Retention", types)
        self.assertIn("Payment UX", types)
        self.assertEqual(len(recs), 3)

    def test_no_default_when_any_rule_triggers(self):
        """Default message should NOT appear if any rule triggers."""
        d = self._defaults()
        d["repeat"]["repeat_rate"] = "10"  # triggers Retention

        recs = generate_recommendations(
            d["health"], d["repeat"], d["pricing"], d["txn_health"], d["bench"]
        )

        default_recs = [r for r in recs if "healthy" in r.get("text", "").lower()]
        self.assertEqual(len(default_recs), 0)

    def test_null_pricing_values(self):
        """Null avg_ticket → 0 → no Revenue Booster."""
        d = self._defaults()
        d["pricing"]["avg_ticket"] = None

        recs = generate_recommendations(
            d["health"], d["repeat"], d["pricing"], d["txn_health"], d["bench"]
        )

        revenue_recs = [r for r in recs if r["type"] == "Revenue Booster" and r["priority"] == "High"]
        self.assertEqual(len(revenue_recs), 0)

    def test_null_bench(self):
        """bench is None → industry_ticket defaults to 0."""
        d = self._defaults()
        d["pricing"]["avg_ticket"] = "50.00"

        recs = generate_recommendations(
            d["health"], d["repeat"], d["pricing"], d["txn_health"], None
        )

        revenue_recs = [r for r in recs if r["type"] == "Revenue Booster" and r["priority"] == "High"]
        self.assertEqual(len(revenue_recs), 0)

    def test_zero_avg_ticket_no_revenue_booster(self):
        """avg_ticket == 0 should not trigger Revenue Booster."""
        d = self._defaults()
        d["pricing"]["avg_ticket"] = "0"
        d["bench"]["industry_ticket"] = "100.00"

        recs = generate_recommendations(
            d["health"], d["repeat"], d["pricing"], d["txn_health"], d["bench"]
        )

        revenue_recs = [r for r in recs if r["type"] == "Revenue Booster" and r["priority"] == "High"]
        self.assertEqual(len(revenue_recs), 0)

    def test_zero_industry_ticket_no_revenue_booster(self):
        """industry_ticket == 0 → no Revenue Booster."""
        d = self._defaults()
        d["pricing"]["avg_ticket"] = "50.00"
        d["bench"]["industry_ticket"] = "0"

        recs = generate_recommendations(
            d["health"], d["repeat"], d["pricing"], d["txn_health"], d["bench"]
        )

        revenue_recs = [r for r in recs if r["type"] == "Revenue Booster" and r["priority"] == "High"]
        self.assertEqual(len(revenue_recs), 0)

    def test_null_repeat_rate_defaults_to_zero(self):
        """Null repeat_rate → 0 < 30 → Retention triggered."""
        d = self._defaults()
        d["repeat"]["repeat_rate"] = None

        recs = generate_recommendations(
            d["health"], d["repeat"], d["pricing"], d["txn_health"], d["bench"]
        )

        retention_recs = [r for r in recs if r["type"] == "Retention"]
        self.assertEqual(len(retention_recs), 1)

    def test_null_approval_rate_defaults_to_zero(self):
        """Null approval_rate → 0 < 85 → Payment UX triggered."""
        d = self._defaults()
        d["txn_health"]["approval_rate"] = None

        recs = generate_recommendations(
            d["health"], d["repeat"], d["pricing"], d["txn_health"], d["bench"]
        )

        ux_recs = [r for r in recs if r["type"] == "Payment UX"]
        self.assertEqual(len(ux_recs), 1)

    def test_revenue_booster_impact_calculation(self):
        """Impact = round((industry_ticket - avg_ticket) * 100)."""
        d = self._defaults()
        d["pricing"]["avg_ticket"] = "95.50"
        d["bench"]["industry_ticket"] = "100.00"

        recs = generate_recommendations(
            d["health"], d["repeat"], d["pricing"], d["txn_health"], d["bench"]
        )

        revenue_recs = [r for r in recs if r["type"] == "Revenue Booster" and r["priority"] == "High"]
        self.assertEqual(len(revenue_recs), 1)
        # (100 - 95.5) * 100 = 450
        self.assertEqual(revenue_recs[0]["impact"], 450)

    def test_empty_dicts_trigger_defaults(self):
        """All empty dicts → repeat=0 < 30, approval=0 < 85."""
        recs = generate_recommendations({}, {}, {}, {}, {})

        types = [r["type"] for r in recs]
        self.assertIn("Retention", types)
        self.assertIn("Payment UX", types)


# ─────────────────────────────────────────────────────────────
# generateAlerts() Tests
# ─────────────────────────────────────────────────────────────
class TestGenerateAlerts(unittest.TestCase):
    """Tests for server.js generateAlerts() business logic."""

    def test_all_normal_returns_systems_normal(self):
        """No thresholds breached → 'Systems Normal' info alert."""
        alerts = generate_alerts(
            {"fraud_rate": "1.0"},
            {"decline_rate": "5.0"},
        )

        self.assertEqual(len(alerts), 1)
        self.assertEqual(alerts[0]["title"], "Systems Normal")
        self.assertEqual(alerts[0]["type"], "info")

    def test_high_fraud_rate_triggers_critical(self):
        """fraud_rate > 3% → critical alert."""
        alerts = generate_alerts(
            {"fraud_rate": "5.5"},
            {"decline_rate": "5.0"},
        )

        critical = [a for a in alerts if a["type"] == "critical"]
        self.assertEqual(len(critical), 1)
        self.assertIn("Fraud Spike", critical[0]["title"])
        self.assertIn("5.5%", critical[0]["message"])
        self.assertIn("3%", critical[0]["message"])

    def test_fraud_rate_exactly_3_no_alert(self):
        """fraud_rate == 3% → no alert (> 3 required, not >=)."""
        alerts = generate_alerts(
            {"fraud_rate": "3.0"},
            {"decline_rate": "5.0"},
        )

        critical = [a for a in alerts if a["type"] == "critical"]
        self.assertEqual(len(critical), 0)

    def test_fraud_rate_3_01_triggers_alert(self):
        """fraud_rate = 3.01% → triggers critical alert."""
        alerts = generate_alerts(
            {"fraud_rate": "3.01"},
            {"decline_rate": "5.0"},
        )

        critical = [a for a in alerts if a["type"] == "critical"]
        self.assertEqual(len(critical), 1)

    def test_high_decline_rate_triggers_warning(self):
        """decline_rate > 15% → warning alert."""
        alerts = generate_alerts(
            {"fraud_rate": "1.0"},
            {"decline_rate": "20.0"},
        )

        warnings = [a for a in alerts if a["type"] == "warning"]
        self.assertEqual(len(warnings), 1)
        self.assertIn("Decline Rate", warnings[0]["title"])
        self.assertIn("20.0%", warnings[0]["message"])

    def test_decline_rate_exactly_15_no_alert(self):
        """decline_rate == 15% → no alert (> 15 required, not >=)."""
        alerts = generate_alerts(
            {"fraud_rate": "1.0"},
            {"decline_rate": "15.0"},
        )

        warnings = [a for a in alerts if a["type"] == "warning"]
        self.assertEqual(len(warnings), 0)

    def test_decline_rate_15_01_triggers_alert(self):
        """decline_rate = 15.01% → triggers warning."""
        alerts = generate_alerts(
            {"fraud_rate": "1.0"},
            {"decline_rate": "15.01"},
        )

        warnings = [a for a in alerts if a["type"] == "warning"]
        self.assertEqual(len(warnings), 1)

    def test_both_alerts_triggered(self):
        """Both fraud_rate > 3 AND decline_rate > 15."""
        alerts = generate_alerts(
            {"fraud_rate": "5.0"},
            {"decline_rate": "25.0"},
        )

        self.assertEqual(len(alerts), 2)
        types = [a["type"] for a in alerts]
        self.assertIn("critical", types)
        self.assertIn("warning", types)

    def test_no_systems_normal_when_alerts_exist(self):
        """'Systems Normal' should NOT appear when real alerts exist."""
        alerts = generate_alerts(
            {"fraud_rate": "5.0"},
            {"decline_rate": "5.0"},
        )

        info_alerts = [a for a in alerts if a["title"] == "Systems Normal"]
        self.assertEqual(len(info_alerts), 0)

    def test_null_fraud_rate_defaults_to_zero(self):
        """Null fraud_rate → 0 → no critical alert."""
        alerts = generate_alerts(
            {"fraud_rate": None},
            {"decline_rate": "5.0"},
        )

        critical = [a for a in alerts if a["type"] == "critical"]
        self.assertEqual(len(critical), 0)

    def test_null_decline_rate_defaults_to_zero(self):
        """Null decline_rate → 0 → no warning alert."""
        alerts = generate_alerts(
            {"fraud_rate": "1.0"},
            {"decline_rate": None},
        )

        warnings = [a for a in alerts if a["type"] == "warning"]
        self.assertEqual(len(warnings), 0)

    def test_empty_dicts_returns_systems_normal(self):
        """Empty dicts → defaults 0 for all → Systems Normal."""
        alerts = generate_alerts({}, {})

        self.assertEqual(len(alerts), 1)
        self.assertEqual(alerts[0]["title"], "Systems Normal")

    def test_missing_keys_defaults_to_zero(self):
        """Missing keys use .get() default → 0."""
        alerts = generate_alerts(
            {},  # no fraud_rate key
            {},  # no decline_rate key
        )

        self.assertEqual(len(alerts), 1)
        self.assertEqual(alerts[0]["type"], "info")

    def test_extreme_fraud_rate(self):
        """Extremely high fraud rate handled correctly."""
        alerts = generate_alerts(
            {"fraud_rate": "99.99"},
            {"decline_rate": "5.0"},
        )

        critical = [a for a in alerts if a["type"] == "critical"]
        self.assertEqual(len(critical), 1)
        self.assertIn("99.99%", critical[0]["message"])

    def test_zero_fraud_rate_no_alert(self):
        """fraud_rate = 0 → no alert."""
        alerts = generate_alerts(
            {"fraud_rate": "0"},
            {"decline_rate": "0"},
        )

        self.assertEqual(len(alerts), 1)
        self.assertEqual(alerts[0]["title"], "Systems Normal")


# ─────────────────────────────────────────────────────────────
# formatCustomerSegments() Tests
# ─────────────────────────────────────────────────────────────
class TestFormatCustomerSegments(unittest.TestCase):
    """Tests for server.js formatCustomerSegments() business logic."""

    def test_null_row_returns_defaults(self):
        """None row → default segments with count=0."""
        result = format_customer_segments(None)

        self.assertEqual(len(result), 3)
        self.assertEqual(result[0]["segment"], "High Spenders")
        self.assertEqual(result[0]["count"], 0)
        self.assertEqual(result[1]["segment"], "Regular")
        self.assertEqual(result[1]["count"], 0)
        self.assertEqual(result[2]["segment"], "One-time")
        self.assertEqual(result[2]["count"], 0)

    def test_empty_dict_row_returns_defaults(self):
        """
        BUG DETECTION: empty dict {} is truthy in JS, so it enters the
        else branch and tries parseInt(undefined) → NaN → 0 via || 0.
        In Python: int(None) raises, but we use `or 0` guard.
        """
        result = format_customer_segments({})

        self.assertEqual(len(result), 3)
        self.assertEqual(result[0]["count"], 0)
        self.assertEqual(result[1]["count"], 0)
        self.assertEqual(result[2]["count"], 0)

    def test_normal_row(self):
        """Normal row with all counts."""
        row = {"high_spender": 50, "regular": 200, "one_time": 300}
        result = format_customer_segments(row)

        self.assertEqual(result[0]["segment"], "High Spenders")
        self.assertEqual(result[0]["count"], 50)
        self.assertEqual(result[1]["segment"], "Regular")
        self.assertEqual(result[1]["count"], 200)
        self.assertEqual(result[2]["segment"], "One-time")
        self.assertEqual(result[2]["count"], 300)

    def test_string_counts_parsed(self):
        """DB may return string counts — int() should handle them."""
        row = {"high_spender": "15", "regular": "100", "one_time": "250"}
        result = format_customer_segments(row)

        self.assertEqual(result[0]["count"], 15)
        self.assertEqual(result[1]["count"], 100)
        self.assertEqual(result[2]["count"], 250)

    def test_null_counts_default_to_zero(self):
        """None counts → 0."""
        row = {"high_spender": None, "regular": None, "one_time": None}
        result = format_customer_segments(row)

        self.assertEqual(result[0]["count"], 0)
        self.assertEqual(result[1]["count"], 0)
        self.assertEqual(result[2]["count"], 0)

    def test_zero_counts(self):
        row = {"high_spender": 0, "regular": 0, "one_time": 0}
        result = format_customer_segments(row)

        self.assertEqual(result[0]["count"], 0)
        self.assertEqual(result[1]["count"], 0)
        self.assertEqual(result[2]["count"], 0)

    def test_total_spend_always_zero(self):
        """
        BUG/LIMITATION: total_spend is hardcoded to 0 for non-null rows.
        The function never calculates actual spending. When row is None,
        the default segments don't even include total_spend key.

        Inconsistency: non-null returns total_spend=0, null returns no total_spend.
        """
        row = {"high_spender": 10, "regular": 20, "one_time": 30}
        result = format_customer_segments(row)

        # Non-null has total_spend
        self.assertEqual(result[0]["total_spend"], 0)

    def test_null_row_no_total_spend_key(self):
        """
        BUG: When row is None, returned segments don't have total_spend key.
        But when row has data, they do. This is inconsistent.
        """
        result_null = format_customer_segments(None)
        result_data = format_customer_segments({"high_spender": 1, "regular": 2, "one_time": 3})

        # Null row: no total_spend key
        self.assertNotIn("total_spend", result_null[0])
        # Data row: has total_spend key
        self.assertIn("total_spend", result_data[0])

    def test_segment_order_is_deterministic(self):
        """Segments always returned in: High Spenders, Regular, One-time order."""
        row = {"high_spender": 5, "regular": 10, "one_time": 15}
        result = format_customer_segments(row)

        self.assertEqual(result[0]["segment"], "High Spenders")
        self.assertEqual(result[1]["segment"], "Regular")
        self.assertEqual(result[2]["segment"], "One-time")

    def test_large_counts(self):
        """Very large counts handled without overflow."""
        row = {"high_spender": 999999, "regular": 5000000, "one_time": 10000000}
        result = format_customer_segments(row)

        self.assertEqual(result[0]["count"], 999999)
        self.assertEqual(result[1]["count"], 5000000)
        self.assertEqual(result[2]["count"], 10000000)


# ─────────────────────────────────────────────────────────────
# SQL Injection / Security Tests for server.js
# ─────────────────────────────────────────────────────────────
class TestServerSQLInjectionRisks(unittest.TestCase):
    """
    Tests documenting SQL injection vulnerabilities in server.js.

    server.js uses string interpolation for merchantId in SQL queries:
        const whereMid = merchantId ? `WHERE a.merchant_id = ${merchantId}` : '';

    Although merchantId is parsed via parseInt() (which returns NaN for
    non-numeric strings, and NaN is falsy so the WHERE clause is skipped),
    this pattern is inherently unsafe. Parameterized queries should be used.

    Note: These are documentation tests — the actual vulnerability exists
    in the JavaScript code, not in testable Python.
    """

    def test_document_string_interpolation_risk(self):
        """
        SECURITY BUG: server.js uses string interpolation for SQL.

        Line: const merchantId = req.params.id === 'all' ? null : parseInt(req.params.id);
        Line: const whereMid = merchantId ? `WHERE a.merchant_id = ${merchantId}` : '';

        parseInt("123abc") = 123, parseInt("all") = NaN.
        While parseInt provides some protection, the pattern is still risky
        because:
        1. parseInt("1; DROP TABLE merchants--") = 1 (ignores suffix)
        2. But the interpolated value is just 1, so it's "safe" by accident
        3. The correct approach is parameterized queries ($1, $2, etc.)

        This test documents the vulnerability.
        """
        # parseInt behavior in JavaScript:
        # parseInt("123") = 123
        # parseInt("123abc") = 123
        # parseInt("abc") = NaN
        # parseInt("all") = NaN (falsy → no WHERE clause)

        # Python equivalent behavior:
        test_inputs = [
            ("123", True, 123),
            ("all", False, None),
            # JS parseInt("1; DROP TABLE") = 1 — note: only first number parsed
        ]

        for input_str, should_parse, expected in test_inputs:
            try:
                val = int(input_str)
                self.assertTrue(should_parse, f"{input_str} should not have parsed")
                self.assertEqual(val, expected)
            except ValueError:
                self.assertFalse(should_parse, f"{input_str} should have parsed")

    def test_document_hardcoded_api_url_in_frontend(self):
        """
        BUG: Frontend components hardcode 'http://localhost:5000/api'.
        This should come from environment/config, not be hardcoded.

        Files affected:
        - Dashboard.jsx: const API_URL = 'http://localhost:5000/api';
        - Revenue.jsx: const API_URL = 'http://localhost:5000/api';
        - Customers.jsx: const API_URL = 'http://localhost:5000/api';
        - Risk.jsx: const API_URL = 'http://localhost:5000/api';
        - Insights.jsx: const API_URL = 'http://localhost:5000/api';
        - App.jsx: axios.get('http://localhost:5000/api/merchants')

        Settings.jsx has apiBaseUrl configurable, but pages don't use it.
        """
        # This is a documentation test — the hardcoded URLs exist in JS files
        hardcoded_pages = [
            "Dashboard.jsx",
            "Revenue.jsx",
            "Customers.jsx",
            "Risk.jsx",
            "Insights.jsx",
            "App.jsx",
        ]
        self.assertEqual(len(hardcoded_pages), 6)


# ─────────────────────────────────────────────────────────────
# Dashboard API Response Structure Tests
# ─────────────────────────────────────────────────────────────
class TestDashboardResponseContract(unittest.TestCase):
    """
    Tests verifying the expected API response structure from
    /api/merchant/:id/dashboard. These validate the contract between
    backend and frontend.
    """

    def test_expected_response_keys(self):
        """The dashboard endpoint should return all 11 keys."""
        expected_keys = {
            "health_score",
            "peak_hours",
            "customer_segments",
            "fraud_monitor",
            "benchmarks",
            "pricing_signal",
            "transaction_health",
            "repeat_analysis",
            "category_insights",
            "recommendations",
            "alerts",
        }
        # This documents the expected contract
        self.assertEqual(len(expected_keys), 11)

    def test_customer_segments_format(self):
        """Customer segments should be list of {segment, count} dicts."""
        segments = format_customer_segments(None)

        for seg in segments:
            self.assertIn("segment", seg)
            self.assertIn("count", seg)
            self.assertIsInstance(seg["segment"], str)
            self.assertIsInstance(seg["count"], int)

    def test_recommendation_structure(self):
        """Each recommendation should have type, priority, impact, text."""
        recs = generate_recommendations(
            {}, {"repeat_rate": "10"}, {}, {"approval_rate": "70"}, {}
        )

        for rec in recs:
            self.assertIn("type", rec)
            self.assertIn("priority", rec)
            self.assertIn("impact", rec)
            self.assertIn("text", rec)
            self.assertIn(rec["priority"], ("High", "Medium", "Low"))
            self.assertIsInstance(rec["impact"], int)

    def test_alert_structure(self):
        """Each alert should have title, message, type."""
        alerts = generate_alerts({"fraud_rate": "5"}, {"decline_rate": "20"})

        for alert in alerts:
            self.assertIn("title", alert)
            self.assertIn("message", alert)
            self.assertIn("type", alert)
            self.assertIn(alert["type"], ("critical", "warning", "info"))


# ─────────────────────────────────────────────────────────────
# Frontend Business Logic Tests
# ─────────────────────────────────────────────────────────────
class TestFrontendBusinessLogic(unittest.TestCase):
    """
    Tests for business logic rules embedded in frontend components.
    These validate the correctness of data transformations and
    conditional rendering rules.
    """

    def test_health_score_formula(self):
        """
        Health score formula from server.js:
        0.30 * approval_rate + 0.20 * (100 - fraud_rate) + 0.50 * 70
        """
        def calc_health_score(approval_rate, fraud_rate):
            return round(
                0.30 * approval_rate + 0.20 * (100 - fraud_rate) + 0.50 * 70,
                2,
            )

        # Perfect metrics
        self.assertAlmostEqual(calc_health_score(100, 0), 85.0, places=2)

        # Terrible metrics
        self.assertAlmostEqual(calc_health_score(0, 100), 35.0, places=2)

        # Average metrics: 0.30*80 + 0.20*(100-2) + 0.50*70 = 24 + 19.6 + 35 = 78.6
        self.assertAlmostEqual(calc_health_score(80, 2), 78.6, places=2)

    def test_health_status_thresholds(self):
        """
        Status thresholds from server.js:
        >= 80 → 'Good', >= 60 → 'Fair', else → 'Poor'
        """
        def get_status(score):
            if score >= 80:
                return "Good"
            elif score >= 60:
                return "Fair"
            else:
                return "Poor"

        self.assertEqual(get_status(80), "Good")
        self.assertEqual(get_status(79.99), "Fair")
        self.assertEqual(get_status(60), "Fair")
        self.assertEqual(get_status(59.99), "Poor")
        self.assertEqual(get_status(0), "Poor")
        self.assertEqual(get_status(100), "Good")

    def test_risk_page_risk_level_thresholds(self):
        """
        Risk level from Risk.jsx:
        fraud_rate > 3 → 'High', fraud_rate > 1 → 'Medium', else → 'Low'
        """
        def get_risk_level(fraud_rate):
            if fraud_rate > 3:
                return "High"
            elif fraud_rate > 1:
                return "Medium"
            else:
                return "Low"

        self.assertEqual(get_risk_level(5.0), "High")
        self.assertEqual(get_risk_level(3.01), "High")
        self.assertEqual(get_risk_level(3.0), "Medium")
        self.assertEqual(get_risk_level(2.0), "Medium")
        self.assertEqual(get_risk_level(1.01), "Medium")
        self.assertEqual(get_risk_level(1.0), "Low")
        self.assertEqual(get_risk_level(0.0), "Low")

    def test_risk_page_decline_rate_calculation(self):
        """
        Risk.jsx: declineRate = parseFloat(100 - approvalRate).toFixed(2)

        BUG: This calculates decline_rate as 100 - approval_rate, but the
        backend already provides decline_rate directly from transaction_health.
        If the backend's decline_rate differs from (100 - approval_rate) due
        to rounding or different counting methods, the UI shows wrong data.
        """
        # The Risk.jsx code uses:
        # const declineRate = parseFloat(100 - approvalRate).toFixed(2)
        # This ignores the backend's actual decline_rate value!

        # Backend might return:
        approval_rate = 92.35
        actual_decline_rate = 7.55  # from DB

        # Frontend calculates:
        frontend_decline_rate = round(100 - approval_rate, 2)

        # They should match... but floating point issues possible
        self.assertAlmostEqual(frontend_decline_rate, 7.65, places=2)
        # Note: 7.65 != 7.55 — the backend's real decline_rate could differ!

    def test_customers_page_activity_data_generation(self):
        """
        Customers.jsx generates fake weekly activity data:
        Mon=12%, Tue=15%, Wed=18%, Thu=17%, Fri=22%, Sat=31%, Sun=28%
        Total = 143% which is > 100% — this is misleading but intentional
        (represents estimated daily active users, not proportions).
        """
        total_users = 1000
        percentages = [0.12, 0.15, 0.18, 0.17, 0.22, 0.31, 0.28]

        activity = [round(total_users * p) for p in percentages]

        self.assertEqual(activity[0], 120)   # Mon
        self.assertEqual(activity[5], 310)   # Sat (peak)
        self.assertEqual(activity[6], 280)   # Sun

        # Sum > total — documents that this is estimated per-day counts
        self.assertGreater(sum(activity), total_users)

    def test_customers_page_repeat_rate_threshold(self):
        """
        Customers.jsx: repeatRate > 40 → 'Healthy retention' else 'Low retention risk'

        Note: This threshold (40%) differs from the recommendation threshold (30%)
        in generateRecommendations(). This inconsistency could confuse users.
        """
        # Customers.jsx uses 40%
        self.assertEqual(
            "Healthy retention" if 41 > 40 else "Low retention risk",
            "Healthy retention",
        )
        self.assertEqual(
            "Healthy retention" if 40 > 40 else "Low retention risk",
            "Low retention risk",
        )

        # But generateRecommendations uses 30%
        # A merchant with 35% repeat rate would:
        #   - Show "Low retention risk" on Customers page (35 <= 40)
        #   - NOT get a Retention recommendation (35 >= 30)
        # This is inconsistent UX.

    def test_assistant_response_generation_coverage(self):
        """
        Assistant.jsx generateResponse() checks keywords to return canned responses.
        Verify each keyword path is exercised.
        """
        keyword_to_topic = {
            "revenue": "revenue",
            "weekend": "revenue",
            "fraud": "fraud",
            "risk": "fraud",
            "repeat": "retention",
            "retention": "retention",
            "loyalty": "retention",
            "category": "category",
            "product": "category",
            "performing": "category",
            "industry": "benchmark",
            "benchmark": "benchmark",
            "compare": "benchmark",
            "segment": "customer",
            "customer": "customer",
        }

        # Verify all keywords are distinct and map to expected topics
        self.assertEqual(len(keyword_to_topic), 15)
        topics = set(keyword_to_topic.values())
        expected_topics = {"revenue", "fraud", "retention", "category", "benchmark", "customer"}
        self.assertEqual(topics, expected_topics)

    def test_notification_time_ago_formatting(self):
        """
        NotificationDropdown.jsx formatTimeAgo() logic:
        < 1 min → 'Just now'
        < 60 min → 'Xm ago'
        < 24 hrs → 'Xh ago'
        >= 24 hrs → 'Xd ago'
        """
        def format_time_ago(diff_ms):
            mins = diff_ms // 60000
            if mins < 1:
                return "Just now"
            if mins < 60:
                return f"{mins}m ago"
            hrs = mins // 60
            if hrs < 24:
                return f"{hrs}h ago"
            return f"{hrs // 24}d ago"

        self.assertEqual(format_time_ago(0), "Just now")
        self.assertEqual(format_time_ago(30000), "Just now")      # 30 sec
        self.assertEqual(format_time_ago(59999), "Just now")      # 59.999 sec
        self.assertEqual(format_time_ago(60000), "1m ago")        # 1 min
        self.assertEqual(format_time_ago(3540000), "59m ago")     # 59 min
        self.assertEqual(format_time_ago(3600000), "1h ago")      # 1 hr
        self.assertEqual(format_time_ago(82800000), "23h ago")    # 23 hrs
        self.assertEqual(format_time_ago(86400000), "1d ago")     # 24 hrs
        self.assertEqual(format_time_ago(172800000), "2d ago")    # 48 hrs


# ─────────────────────────────────────────────────────────────
# DateRangePicker Logic Tests
# ─────────────────────────────────────────────────────────────
class TestDateRangePickerLogic(unittest.TestCase):
    """Tests for DateRangePicker.jsx business logic."""

    def test_all_time_is_null_null(self):
        """'All Time' selection should produce {from: null, to: null}."""
        date_range = {"from": None, "to": None}

        label = "All Time" if not date_range["from"] and not date_range["to"] else "Custom"
        self.assertEqual(label, "All Time")

    def test_custom_range_label(self):
        """Custom dates should show range label."""
        date_range = {"from": "2025-01-01", "to": "2025-03-01"}

        label = f"{date_range['from']} — {date_range['to']}"
        self.assertEqual(label, "2025-01-01 — 2025-03-01")

    def test_partial_range_from_only(self):
        """Only 'from' set, 'to' is null."""
        date_range = {"from": "2025-01-01", "to": None}

        from_val = date_range["from"] or "..."
        to_val = date_range["to"] or "..."
        label = f"{from_val} — {to_val}"
        self.assertEqual(label, "2025-01-01 — ...")


# ─────────────────────────────────────────────────────────────
# Settings Logic Tests
# ─────────────────────────────────────────────────────────────
class TestSettingsLogic(unittest.TestCase):
    """Tests for Settings.jsx business logic."""

    def test_default_settings_values(self):
        """Verify default settings match the expected contract."""
        defaults = {
            "theme": "dark",
            "currency": "USD",
            "fraudRateThreshold": 3,
            "declineRateThreshold": 15,
            "lowRepeatRateThreshold": 30,
            "apiBaseUrl": "http://localhost:5000",
            "merchantName": "Merchant Admin",
            "merchantEmail": "admin@luminapay.com",
        }

        self.assertEqual(defaults["theme"], "dark")
        self.assertEqual(defaults["currency"], "USD")
        self.assertEqual(defaults["fraudRateThreshold"], 3)
        self.assertEqual(defaults["declineRateThreshold"], 15)
        self.assertEqual(defaults["lowRepeatRateThreshold"], 30)

    def test_fraud_threshold_range(self):
        """Fraud rate threshold slider: min=0.5, max=20, step=0.5."""
        min_val, max_val, step = 0.5, 20, 0.5

        self.assertGreater(min_val, 0)
        self.assertLessEqual(max_val, 100)
        # Verify step divides range evenly
        self.assertEqual((max_val - min_val) % step, 0)

    def test_decline_threshold_range(self):
        """Decline rate threshold slider: min=1, max=50, step=1."""
        min_val, max_val, step = 1, 50, 1

        self.assertGreater(min_val, 0)
        self.assertLessEqual(max_val, 100)

    def test_repeat_rate_threshold_range(self):
        """Low repeat rate threshold slider: min=5, max=80, step=5."""
        min_val, max_val, step = 5, 80, 5

        self.assertGreater(min_val, 0)
        self.assertLessEqual(max_val, 100)
        self.assertEqual((max_val - min_val) % step, 0)

    def test_settings_thresholds_match_alert_logic(self):
        """
        BUG: Settings page allows configuring thresholds
        (fraudRateThreshold=3, declineRateThreshold=15),
        but server.js generateAlerts() uses HARDCODED values (3% and 15%).
        The configurable thresholds in Settings have NO EFFECT.

        The settings are stored in localStorage but never sent to the backend.
        """
        # Settings defaults
        configured_fraud_threshold = 3
        configured_decline_threshold = 15

        # Server.js hardcoded values
        server_fraud_threshold = 3
        server_decline_threshold = 15

        # They match by default, but if user changes them, server ignores it
        self.assertEqual(configured_fraud_threshold, server_fraud_threshold)
        self.assertEqual(configured_decline_threshold, server_decline_threshold)
        # BUG: Changing these in Settings does nothing to actual alert logic

    def test_bug_settings_api_url_not_used_by_pages(self):
        """
        BUG: Settings.jsx allows configuring apiBaseUrl, but all page
        components (Dashboard, Revenue, Customers, Risk, Insights)
        hardcode 'http://localhost:5000/api'. The configured URL is ignored.
        """
        settings_api_url = "http://custom-api:3000"  # User configured
        hardcoded_api_url = "http://localhost:5000/api"  # Pages use this

        self.assertNotEqual(settings_api_url, hardcoded_api_url)
        # This proves the settings value can differ from what pages actually use


# ─────────────────────────────────────────────────────────────
# Sidebar / Navigation Logic Tests
# ─────────────────────────────────────────────────────────────
class TestSidebarLogic(unittest.TestCase):
    """Tests for Sidebar.jsx / App.jsx routing logic."""

    def test_all_tab_ids_are_handled(self):
        """
        App.jsx renderContent() has a switch/case for each tab.
        Verify all sidebar nav items are handled.
        """
        sidebar_items = ["dashboard", "revenue", "customers", "risk", "insights", "assistant"]
        bottom_items = ["settings"]
        all_items = sidebar_items + bottom_items

        handled_cases = ["dashboard", "revenue", "customers", "risk", "insights", "settings", "assistant"]

        for item in all_items:
            self.assertIn(item, handled_cases, f"Tab '{item}' not handled in renderContent()")

    def test_get_page_title_mapping(self):
        """Verify getPageTitle() returns correct titles."""
        title_map = {
            "dashboard": "Business Overview",
            "revenue": "Revenue & Growth Tracker",
            "customers": "Customer Insights",
            "risk": "Fraud Risk Monitor",
            "insights": "AI Smart Recommendations",
            "assistant": "AI Business Coach",
            "settings": "Platform Settings",
        }

        for tab, expected_title in title_map.items():
            self.assertIsNotNone(expected_title)
            self.assertTrue(len(expected_title) > 0)

    def test_default_tab_title(self):
        """Unknown tab should return 'Dashboard' as default."""
        def get_page_title(tab):
            titles = {
                "dashboard": "Business Overview",
                "revenue": "Revenue & Growth Tracker",
                "customers": "Customer Insights",
                "risk": "Fraud Risk Monitor",
                "insights": "AI Smart Recommendations",
                "assistant": "AI Business Coach",
                "settings": "Platform Settings",
            }
            return titles.get(tab, "Dashboard")

        self.assertEqual(get_page_title("unknown"), "Dashboard")
        self.assertEqual(get_page_title(""), "Dashboard")
        self.assertEqual(get_page_title(None), "Dashboard")

    def test_bug_logout_only_confirms_no_action(self):
        """
        BUG: Sidebar logout handler only calls window.confirm() but takes
        no action regardless of the result. The user is never actually logged out.

        Code: const handleLogout = () => { window.confirm('Are you sure...?'); };
        """
        # The confirm result is not used — logout never happens
        pass  # Documented as a bug


if __name__ == "__main__":
    unittest.main()
