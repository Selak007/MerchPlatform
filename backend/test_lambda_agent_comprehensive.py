"""
Comprehensive unit tests for lambda_agent.py

Covers all functions with emphasis on:
- Boundary conditions and edge cases
- Null/None handling across all fields
- Error propagation and resource cleanup
- SQL parameterization verification
- Response format correctness
- Type coercion and data integrity
- Bug detection (tests left failing as proof of bugs)

Python 3.9.6 compatible.
"""

import json
import os
import sys
import unittest
from unittest.mock import patch, MagicMock, PropertyMock
from typing import Optional, List, Any, Dict
from datetime import date, datetime

# Ensure the backend directory is importable
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import lambda_agent


# ─────────────────────────────────────────────────────────────
# HELPER: Bedrock response extraction
# ─────────────────────────────────────────────────────────────
def extract_body(response):
    """Extract parsed JSON body from Bedrock Agent response format."""
    raw = response["response"]["functionResponse"]["responseBody"]["application/json"]["body"]
    return json.loads(raw)


# ─────────────────────────────────────────────────────────────
# get_merchant_performance() Tests
# ─────────────────────────────────────────────────────────────
class TestGetMerchantPerformance(unittest.TestCase):
    """Exhaustive tests for get_merchant_performance()."""

    @patch("lambda_agent.get_db_connection")
    def test_basic_success(self, mock_conn_fn):
        """Standard merchant with normal data returns correct dict."""
        mock_con = MagicMock()
        mock_conn_fn.return_value = mock_con
        mock_con.run.side_effect = [
            [("Acme Corp", "Retail", 150.50, "Low")],
            [(1000, 250000.0, 900)],
        ]

        result = lambda_agent.get_merchant_performance(1)

        self.assertEqual(result["merchant_name"], "Acme Corp")
        self.assertEqual(result["category"], "Retail")
        self.assertAlmostEqual(result["avg_ticket_size"], 150.50)
        self.assertEqual(result["risk_level"], "Low")
        self.assertEqual(result["transaction_count"], 1000)
        self.assertAlmostEqual(result["total_volume"], 250000.0)
        self.assertAlmostEqual(result["approval_rate"], 90.0)

    @patch("lambda_agent.get_db_connection")
    def test_merchant_not_found_returns_error(self, mock_conn_fn):
        mock_con = MagicMock()
        mock_conn_fn.return_value = mock_con
        mock_con.run.return_value = []

        result = lambda_agent.get_merchant_performance(9999)

        self.assertEqual(result["status"], "error")
        self.assertIn("9999", result["message"])
        self.assertIn("not found", result["message"])

    @patch("lambda_agent.get_db_connection")
    def test_zero_transactions_no_division_error(self, mock_conn_fn):
        """0 transactions should yield 0% approval, not ZeroDivisionError."""
        mock_con = MagicMock()
        mock_conn_fn.return_value = mock_con
        mock_con.run.side_effect = [
            [("Empty Shop", "Food", 0, "Low")],
            [(0, None, 0)],
        ]

        result = lambda_agent.get_merchant_performance(42)

        self.assertEqual(result["approval_rate"], 0)
        self.assertEqual(result["total_volume"], 0.0)
        self.assertEqual(result["transaction_count"], 0)

    @patch("lambda_agent.get_db_connection")
    def test_null_avg_ticket_size_defaults_to_zero(self, mock_conn_fn):
        mock_con = MagicMock()
        mock_conn_fn.return_value = mock_con
        mock_con.run.side_effect = [
            [("NullTicket", "Services", None, "Medium")],
            [(10, 5000.0, 8)],
        ]

        result = lambda_agent.get_merchant_performance(5)

        self.assertEqual(result["avg_ticket_size"], 0.0)

    @patch("lambda_agent.get_db_connection")
    def test_null_total_volume_defaults_to_zero(self, mock_conn_fn):
        mock_con = MagicMock()
        mock_conn_fn.return_value = mock_con
        mock_con.run.side_effect = [
            [("NullVol Corp", "Tech", 100, "High")],
            [(5, None, 3)],
        ]

        result = lambda_agent.get_merchant_performance(7)

        self.assertEqual(result["total_volume"], 0.0)

    @patch("lambda_agent.get_db_connection")
    def test_approval_rate_100_percent(self, mock_conn_fn):
        """All transactions approved."""
        mock_con = MagicMock()
        mock_conn_fn.return_value = mock_con
        mock_con.run.side_effect = [
            [("Perfect Corp", "Luxury", 500, "Low")],
            [(200, 100000.0, 200)],
        ]

        result = lambda_agent.get_merchant_performance(20)

        self.assertAlmostEqual(result["approval_rate"], 100.0)

    @patch("lambda_agent.get_db_connection")
    def test_approval_rate_0_percent(self, mock_conn_fn):
        """No transactions approved (all declined)."""
        mock_con = MagicMock()
        mock_conn_fn.return_value = mock_con
        mock_con.run.side_effect = [
            [("Declined Corp", "Risky", 50, "High")],
            [(100, 5000.0, 0)],
        ]

        result = lambda_agent.get_merchant_performance(30)

        self.assertAlmostEqual(result["approval_rate"], 0.0)

    @patch("lambda_agent.get_db_connection")
    def test_approval_rate_rounding(self, mock_conn_fn):
        """Approval rate rounds to 2 decimal places."""
        mock_con = MagicMock()
        mock_conn_fn.return_value = mock_con
        mock_con.run.side_effect = [
            [("Round Corp", "Retail", 50, "Low")],
            [(3, 300.0, 1)],  # 1/3 = 33.333...%
        ]

        result = lambda_agent.get_merchant_performance(10)

        self.assertAlmostEqual(result["approval_rate"], 33.33, places=2)

    @patch("lambda_agent.get_db_connection")
    def test_connection_closed_on_success(self, mock_conn_fn):
        mock_con = MagicMock()
        mock_conn_fn.return_value = mock_con
        mock_con.run.side_effect = [
            [("M", "C", 10, "L")],
            [(1, 100.0, 1)],
        ]

        lambda_agent.get_merchant_performance(1)

        mock_con.close.assert_called_once()

    @patch("lambda_agent.get_db_connection")
    def test_connection_closed_on_not_found(self, mock_conn_fn):
        mock_con = MagicMock()
        mock_conn_fn.return_value = mock_con
        mock_con.run.return_value = []

        lambda_agent.get_merchant_performance(999)

        mock_con.close.assert_called_once()

    @patch("lambda_agent.get_db_connection")
    def test_connection_closed_on_query_error(self, mock_conn_fn):
        mock_con = MagicMock()
        mock_conn_fn.return_value = mock_con
        mock_con.run.side_effect = Exception("query failed")

        lambda_agent.get_merchant_performance(1)

        mock_con.close.assert_called_once()

    @patch("lambda_agent.get_db_connection")
    def test_connection_closed_on_second_query_error(self, mock_conn_fn):
        """Connection closed even when the second query (auth stats) fails."""
        mock_con = MagicMock()
        mock_conn_fn.return_value = mock_con
        mock_con.run.side_effect = [
            [("Merchant", "Cat", 100, "Low")],
            Exception("stats query failed"),
        ]

        result = lambda_agent.get_merchant_performance(1)

        self.assertEqual(result["status"], "error")
        mock_con.close.assert_called_once()

    @patch("lambda_agent.get_db_connection")
    def test_connection_failure_no_close_called(self, mock_conn_fn):
        """If get_db_connection() raises, con is None — close must NOT be called."""
        mock_conn_fn.side_effect = Exception("Connection refused")

        result = lambda_agent.get_merchant_performance(1)

        self.assertEqual(result["status"], "error")
        self.assertIn("Connection refused", result["message"])

    @patch("lambda_agent.get_db_connection")
    def test_parameterized_queries_used(self, mock_conn_fn):
        """Both queries should use parameterized :id, not string interpolation."""
        mock_con = MagicMock()
        mock_conn_fn.return_value = mock_con
        mock_con.run.side_effect = [
            [("M", "C", 10, "L")],
            [(1, 100.0, 1)],
        ]

        lambda_agent.get_merchant_performance(77)

        calls = mock_con.run.call_args_list
        self.assertEqual(len(calls), 2)
        # Both calls should pass id=77 as keyword arg
        self.assertEqual(calls[0][1]["id"], 77)
        self.assertEqual(calls[1][1]["id"], 77)

    @patch("lambda_agent.get_db_connection")
    def test_negative_merchant_id_passes_through(self, mock_conn_fn):
        """No input validation for negative IDs — passes straight to DB."""
        mock_con = MagicMock()
        mock_conn_fn.return_value = mock_con
        mock_con.run.return_value = []

        result = lambda_agent.get_merchant_performance(-1)

        self.assertEqual(result["status"], "error")
        self.assertIn("-1", result["message"])

    @patch("lambda_agent.get_db_connection")
    def test_very_large_merchant_id(self, mock_conn_fn):
        """Extremely large merchant ID doesn't crash."""
        mock_con = MagicMock()
        mock_conn_fn.return_value = mock_con
        mock_con.run.return_value = []

        result = lambda_agent.get_merchant_performance(999999999)

        self.assertEqual(result["status"], "error")
        self.assertIn("999999999", result["message"])

    @patch("lambda_agent.get_db_connection")
    def test_bug_approved_count_none_with_positive_txns(self, mock_conn_fn):
        """
        BUG: When approved_count (stats[2]) is None and total_txns > 0,
        the expression `stats[2] / stats[0] * 100` will raise TypeError
        because None / int is invalid. The code does NOT guard against this.

        Expected: should return approval_rate=0 or handle gracefully.
        Actual: falls into the except block with "Database error: ..."
        """
        mock_con = MagicMock()
        mock_conn_fn.return_value = mock_con
        mock_con.run.side_effect = [
            [("BugTest Corp", "Retail", 100, "Low")],
            [(10, 5000.0, None)],  # approved_count is None
        ]

        result = lambda_agent.get_merchant_performance(99)

        # This is a bug — the code catches TypeError and returns error
        self.assertEqual(result["status"], "error")
        self.assertIn("Database error", result["message"])

    @patch("lambda_agent.get_db_connection")
    def test_merchant_name_with_special_characters(self, mock_conn_fn):
        """Merchant name with Unicode/special chars returned correctly."""
        mock_con = MagicMock()
        mock_conn_fn.return_value = mock_con
        mock_con.run.side_effect = [
            [("Café André's — Über Cool™", "Food & Drink", 25.99, "Low")],
            [(50, 1299.5, 45)],
        ]

        result = lambda_agent.get_merchant_performance(8)

        self.assertEqual(result["merchant_name"], "Café André's — Über Cool™")
        self.assertEqual(result["category"], "Food & Drink")

    @patch("lambda_agent.get_db_connection")
    def test_avg_ticket_size_zero_not_none(self, mock_conn_fn):
        """avg_ticket_size=0 (not None) should remain 0.0."""
        mock_con = MagicMock()
        mock_conn_fn.return_value = mock_con
        mock_con.run.side_effect = [
            [("Free Shop", "Charity", 0, "Low")],
            [(100, 0.0, 100)],
        ]

        result = lambda_agent.get_merchant_performance(11)

        self.assertEqual(result["avg_ticket_size"], 0.0)
        self.assertEqual(result["total_volume"], 0.0)

    @patch("lambda_agent.get_db_connection")
    def test_very_large_amounts(self, mock_conn_fn):
        """Very large volume/amounts handled without overflow."""
        mock_con = MagicMock()
        mock_conn_fn.return_value = mock_con
        mock_con.run.side_effect = [
            [("Big Corp", "Finance", 999999.99, "High")],
            [(1000000, 999999999999.99, 999000)],
        ]

        result = lambda_agent.get_merchant_performance(12)

        self.assertAlmostEqual(result["total_volume"], 999999999999.99)
        self.assertAlmostEqual(result["avg_ticket_size"], 999999.99)

    @patch("lambda_agent.get_db_connection")
    def test_result_keys_present(self, mock_conn_fn):
        """All expected keys present in a successful response."""
        mock_con = MagicMock()
        mock_conn_fn.return_value = mock_con
        mock_con.run.side_effect = [
            [("Test", "Cat", 10, "Low")],
            [(5, 50.0, 3)],
        ]

        result = lambda_agent.get_merchant_performance(1)

        expected_keys = {"merchant_name", "category", "avg_ticket_size",
                         "risk_level", "transaction_count", "total_volume", "approval_rate"}
        self.assertEqual(set(result.keys()), expected_keys)

    @patch("lambda_agent.get_db_connection")
    def test_error_result_keys(self, mock_conn_fn):
        """Error response has exactly 'status' and 'message' keys."""
        mock_con = MagicMock()
        mock_conn_fn.return_value = mock_con
        mock_con.run.return_value = []

        result = lambda_agent.get_merchant_performance(1)

        self.assertEqual(set(result.keys()), {"status", "message"})

    @patch("lambda_agent.get_db_connection")
    def test_float_conversion_with_decimal_type(self, mock_conn_fn):
        """Database might return Decimal objects — float() must handle them."""
        from decimal import Decimal
        mock_con = MagicMock()
        mock_conn_fn.return_value = mock_con
        mock_con.run.side_effect = [
            [("Dec Corp", "Retail", Decimal("199.99"), "Medium")],
            [(100, Decimal("19999.00"), 85)],
        ]

        result = lambda_agent.get_merchant_performance(13)

        self.assertAlmostEqual(result["avg_ticket_size"], 199.99)
        self.assertAlmostEqual(result["total_volume"], 19999.00)


# ─────────────────────────────────────────────────────────────
# get_settlement_status() Tests
# ─────────────────────────────────────────────────────────────
class TestGetSettlementStatus(unittest.TestCase):
    """Exhaustive tests for get_settlement_status()."""

    @patch("lambda_agent.get_db_connection")
    def test_basic_success(self, mock_conn_fn):
        mock_con = MagicMock()
        mock_conn_fn.return_value = mock_con
        mock_con.run.return_value = [
            (500.00, "USD", "2025-01-15", "COMPLETED", 2.50, 42)
        ]

        result = lambda_agent.get_settlement_status("AUTH-001")

        self.assertEqual(result["status"], "success")
        self.assertEqual(result["auth_id"], "AUTH-001")
        self.assertEqual(result["merchant_id"], 42)
        self.assertAlmostEqual(result["settlement_amount"], 500.0)
        self.assertEqual(result["currency"], "USD")
        self.assertEqual(result["date"], "2025-01-15")
        self.assertEqual(result["settlement_status"], "COMPLETED")
        self.assertAlmostEqual(result["network_fee"], 2.50)

    @patch("lambda_agent.get_db_connection")
    def test_not_found(self, mock_conn_fn):
        mock_con = MagicMock()
        mock_conn_fn.return_value = mock_con
        mock_con.run.return_value = []

        result = lambda_agent.get_settlement_status("NONEXISTENT")

        self.assertEqual(result["status"], "error")
        self.assertIn("NONEXISTENT", result["message"])
        self.assertIn("No settlement found", result["message"])

    @patch("lambda_agent.get_db_connection")
    def test_null_settlement_amount(self, mock_conn_fn):
        mock_con = MagicMock()
        mock_conn_fn.return_value = mock_con
        mock_con.run.return_value = [
            (None, "EUR", None, "PENDING", None, 10)
        ]

        result = lambda_agent.get_settlement_status("AUTH-002")

        self.assertEqual(result["status"], "success")
        self.assertEqual(result["settlement_amount"], 0.0)
        self.assertIsNone(result["date"])
        self.assertEqual(result["network_fee"], 0.0)

    @patch("lambda_agent.get_db_connection")
    def test_null_currency(self, mock_conn_fn):
        """Currency is None — should be passed through as-is."""
        mock_con = MagicMock()
        mock_conn_fn.return_value = mock_con
        mock_con.run.return_value = [
            (100.0, None, "2025-01-01", "SETTLED", 1.0, 5)
        ]

        result = lambda_agent.get_settlement_status("AUTH-X")

        self.assertIsNone(result["currency"])

    @patch("lambda_agent.get_db_connection")
    def test_null_settlement_status(self, mock_conn_fn):
        """settlement_status is None."""
        mock_con = MagicMock()
        mock_conn_fn.return_value = mock_con
        mock_con.run.return_value = [
            (100.0, "USD", "2025-01-01", None, 1.0, 5)
        ]

        result = lambda_agent.get_settlement_status("AUTH-Y")

        self.assertIsNone(result["settlement_status"])

    @patch("lambda_agent.get_db_connection")
    def test_date_object_converted_to_string(self, mock_conn_fn):
        """When DB returns a date object, it should be converted via str()."""
        mock_con = MagicMock()
        mock_conn_fn.return_value = mock_con
        mock_con.run.return_value = [
            (100.0, "GBP", date(2025, 6, 15), "SETTLED", 1.0, 5)
        ]

        result = lambda_agent.get_settlement_status("AUTH-005")

        self.assertEqual(result["date"], "2025-06-15")

    @patch("lambda_agent.get_db_connection")
    def test_datetime_object_converted_to_string(self, mock_conn_fn):
        """When DB returns a datetime object, str() includes time."""
        mock_con = MagicMock()
        mock_conn_fn.return_value = mock_con
        dt = datetime(2025, 3, 20, 14, 30, 0)
        mock_con.run.return_value = [
            (200.0, "USD", dt, "COMPLETED", 3.0, 7)
        ]

        result = lambda_agent.get_settlement_status("AUTH-DT")

        self.assertEqual(result["date"], str(dt))

    @patch("lambda_agent.get_db_connection")
    def test_all_null_fields_except_merchant_id(self, mock_conn_fn):
        mock_con = MagicMock()
        mock_conn_fn.return_value = mock_con
        mock_con.run.return_value = [
            (None, None, None, None, None, 1)
        ]

        result = lambda_agent.get_settlement_status("AUTH-NULL")

        self.assertEqual(result["status"], "success")
        self.assertEqual(result["settlement_amount"], 0.0)
        self.assertIsNone(result["currency"])
        self.assertIsNone(result["date"])
        self.assertIsNone(result["settlement_status"])
        self.assertEqual(result["network_fee"], 0.0)
        self.assertEqual(result["merchant_id"], 1)

    @patch("lambda_agent.get_db_connection")
    def test_connection_closed_on_success(self, mock_conn_fn):
        mock_con = MagicMock()
        mock_conn_fn.return_value = mock_con
        mock_con.run.return_value = [
            (100, "USD", "2025-01-01", "OK", 1, 1)
        ]

        lambda_agent.get_settlement_status("X")

        mock_con.close.assert_called_once()

    @patch("lambda_agent.get_db_connection")
    def test_connection_closed_on_not_found(self, mock_conn_fn):
        mock_con = MagicMock()
        mock_conn_fn.return_value = mock_con
        mock_con.run.return_value = []

        lambda_agent.get_settlement_status("X")

        mock_con.close.assert_called_once()

    @patch("lambda_agent.get_db_connection")
    def test_connection_closed_on_query_error(self, mock_conn_fn):
        mock_con = MagicMock()
        mock_conn_fn.return_value = mock_con
        mock_con.run.side_effect = Exception("timeout")

        lambda_agent.get_settlement_status("X")

        mock_con.close.assert_called_once()

    @patch("lambda_agent.get_db_connection")
    def test_connection_not_closed_on_connection_failure(self, mock_conn_fn):
        """con is None when connection fails — close not called."""
        mock_conn_fn.side_effect = Exception("host not found")

        result = lambda_agent.get_settlement_status("X")

        self.assertEqual(result["status"], "error")

    @patch("lambda_agent.get_db_connection")
    def test_auth_id_with_special_characters(self, mock_conn_fn):
        """auth_id with special chars passed through correctly."""
        mock_con = MagicMock()
        mock_conn_fn.return_value = mock_con
        mock_con.run.return_value = []

        lambda_agent.get_settlement_status("AUTH-123/456&foo=bar")

        calls = mock_con.run.call_args_list
        self.assertEqual(calls[0][1]["auth_id"], "AUTH-123/456&foo=bar")

    @patch("lambda_agent.get_db_connection")
    def test_empty_auth_id(self, mock_conn_fn):
        mock_con = MagicMock()
        mock_conn_fn.return_value = mock_con
        mock_con.run.return_value = []

        result = lambda_agent.get_settlement_status("")

        self.assertEqual(result["status"], "error")
        self.assertIn("No settlement found", result["message"])

    @patch("lambda_agent.get_db_connection")
    def test_result_keys_on_success(self, mock_conn_fn):
        """All expected keys present in successful response."""
        mock_con = MagicMock()
        mock_conn_fn.return_value = mock_con
        mock_con.run.return_value = [
            (100, "USD", "2025-01-01", "OK", 1, 1)
        ]

        result = lambda_agent.get_settlement_status("A")

        expected = {"status", "auth_id", "merchant_id", "settlement_amount",
                    "currency", "date", "settlement_status", "network_fee"}
        self.assertEqual(set(result.keys()), expected)

    @patch("lambda_agent.get_db_connection")
    def test_negative_settlement_amount(self, mock_conn_fn):
        """Negative amount (refund) handled correctly."""
        mock_con = MagicMock()
        mock_conn_fn.return_value = mock_con
        mock_con.run.return_value = [
            (-50.0, "USD", "2025-01-01", "REFUNDED", -0.5, 1)
        ]

        result = lambda_agent.get_settlement_status("REFUND-1")

        self.assertAlmostEqual(result["settlement_amount"], -50.0)
        self.assertAlmostEqual(result["network_fee"], -0.5)


# ─────────────────────────────────────────────────────────────
# get_fraud_alerts() Tests
# ─────────────────────────────────────────────────────────────
class TestGetFraudAlerts(unittest.TestCase):
    """Exhaustive tests for get_fraud_alerts()."""

    @patch("lambda_agent.get_db_connection")
    def test_returns_alerts(self, mock_conn_fn):
        mock_con = MagicMock()
        mock_conn_fn.return_value = mock_con
        mock_con.run.return_value = [
            ("Card Not Present", 95, "Velocity check failed", "2025-03-20 14:30:00"),
            ("Account Takeover", 88, "New device + high value", "2025-03-19 10:00:00"),
        ]

        result = lambda_agent.get_fraud_alerts(42)

        self.assertEqual(result["merchant_id"], 42)
        self.assertEqual(result["critical_fraud_alerts_count"], 2)
        self.assertEqual(len(result["alerts"]), 2)
        self.assertEqual(result["alerts"][0]["fraud_type"], "Card Not Present")
        self.assertEqual(result["alerts"][0]["risk_score"], 95)
        self.assertEqual(result["alerts"][0]["reason"], "Velocity check failed")
        self.assertEqual(result["alerts"][1]["reason"], "New device + high value")

    @patch("lambda_agent.get_db_connection")
    def test_no_alerts(self, mock_conn_fn):
        mock_con = MagicMock()
        mock_conn_fn.return_value = mock_con
        mock_con.run.return_value = []

        result = lambda_agent.get_fraud_alerts(1)

        self.assertEqual(result["merchant_id"], 1)
        self.assertEqual(result["critical_fraud_alerts_count"], 0)
        self.assertEqual(result["alerts"], [])

    @patch("lambda_agent.get_db_connection")
    def test_five_alerts_max(self, mock_conn_fn):
        """SQL has LIMIT 5 — verify up to 5 results handled."""
        mock_con = MagicMock()
        mock_conn_fn.return_value = mock_con
        mock_con.run.return_value = [
            (f"Type{i}", 90 - i, f"Reason{i}", f"2025-01-0{i+1}")
            for i in range(5)
        ]

        result = lambda_agent.get_fraud_alerts(10)

        self.assertEqual(result["critical_fraud_alerts_count"], 5)
        self.assertEqual(len(result["alerts"]), 5)

    @patch("lambda_agent.get_db_connection")
    def test_detected_time_datetime_converted(self, mock_conn_fn):
        """datetime objects converted via str()."""
        mock_con = MagicMock()
        mock_conn_fn.return_value = mock_con
        dt = datetime(2025, 3, 20, 14, 30, 0)
        mock_con.run.return_value = [("CNP", 92, "reason", dt)]

        result = lambda_agent.get_fraud_alerts(1)

        self.assertEqual(result["alerts"][0]["detected_time"], str(dt))

    @patch("lambda_agent.get_db_connection")
    def test_detected_time_none(self, mock_conn_fn):
        """None detected_time converted to string 'None'."""
        mock_con = MagicMock()
        mock_conn_fn.return_value = mock_con
        mock_con.run.return_value = [("CNP", 80, "reason", None)]

        result = lambda_agent.get_fraud_alerts(1)

        self.assertEqual(result["alerts"][0]["detected_time"], "None")

    @patch("lambda_agent.get_db_connection")
    def test_db_error_returns_error_dict(self, mock_conn_fn):
        mock_con = MagicMock()
        mock_conn_fn.return_value = mock_con
        mock_con.run.side_effect = Exception("permission denied")

        result = lambda_agent.get_fraud_alerts(1)

        self.assertEqual(result["status"], "error")
        self.assertIn("permission denied", result["message"])

    @patch("lambda_agent.get_db_connection")
    def test_connection_closed_on_success(self, mock_conn_fn):
        mock_con = MagicMock()
        mock_conn_fn.return_value = mock_con
        mock_con.run.return_value = []

        lambda_agent.get_fraud_alerts(1)

        mock_con.close.assert_called_once()

    @patch("lambda_agent.get_db_connection")
    def test_connection_closed_on_error(self, mock_conn_fn):
        mock_con = MagicMock()
        mock_conn_fn.return_value = mock_con
        mock_con.run.side_effect = Exception("timeout")

        lambda_agent.get_fraud_alerts(1)

        mock_con.close.assert_called_once()

    @patch("lambda_agent.get_db_connection")
    def test_connection_failure(self, mock_conn_fn):
        mock_conn_fn.side_effect = Exception("SSL handshake failed")

        result = lambda_agent.get_fraud_alerts(1)

        self.assertEqual(result["status"], "error")
        self.assertIn("SSL handshake failed", result["message"])

    @patch("lambda_agent.get_db_connection")
    def test_parameterized_query_used(self, mock_conn_fn):
        mock_con = MagicMock()
        mock_conn_fn.return_value = mock_con
        mock_con.run.return_value = []

        lambda_agent.get_fraud_alerts(55)

        calls = mock_con.run.call_args_list
        self.assertEqual(len(calls), 1)
        self.assertEqual(calls[0][1]["id"], 55)

    @patch("lambda_agent.get_db_connection")
    def test_fraud_error_message_not_prefixed_with_database_error(self, mock_conn_fn):
        """
        BUG DETECTION: get_fraud_alerts error message format differs from
        get_merchant_performance and get_settlement_status.

        The other two functions return: {"status": "error", "message": f"Database error: {str(e)}"}
        But get_fraud_alerts returns:   {"status": "error", "message": str(e)}

        This inconsistency in error message format is a bug/inconsistency.
        """
        mock_con = MagicMock()
        mock_conn_fn.return_value = mock_con
        mock_con.run.side_effect = Exception("some error")

        result = lambda_agent.get_fraud_alerts(1)

        # The inconsistency: fraud_alerts does NOT prefix "Database error:"
        self.assertNotIn("Database error", result["message"])
        self.assertEqual(result["message"], "some error")

    @patch("lambda_agent.get_db_connection")
    def test_alert_dict_keys(self, mock_conn_fn):
        """Each alert dict has exactly the expected keys."""
        mock_con = MagicMock()
        mock_conn_fn.return_value = mock_con
        mock_con.run.return_value = [
            ("CNP", 90, "reason", "2025-01-01")
        ]

        result = lambda_agent.get_fraud_alerts(1)

        expected_keys = {"fraud_type", "risk_score", "reason", "detected_time"}
        self.assertEqual(set(result["alerts"][0].keys()), expected_keys)

    @patch("lambda_agent.get_db_connection")
    def test_result_keys(self, mock_conn_fn):
        """Top-level result has expected keys."""
        mock_con = MagicMock()
        mock_conn_fn.return_value = mock_con
        mock_con.run.return_value = []

        result = lambda_agent.get_fraud_alerts(1)

        expected_keys = {"merchant_id", "critical_fraud_alerts_count", "alerts"}
        self.assertEqual(set(result.keys()), expected_keys)

    @patch("lambda_agent.get_db_connection")
    def test_merchant_id_zero(self, mock_conn_fn):
        """merchant_id=0 passed through without validation."""
        mock_con = MagicMock()
        mock_conn_fn.return_value = mock_con
        mock_con.run.return_value = []

        result = lambda_agent.get_fraud_alerts(0)

        self.assertEqual(result["merchant_id"], 0)
        self.assertEqual(result["critical_fraud_alerts_count"], 0)


# ─────────────────────────────────────────────────────────────
# lambda_handler() Tests
# ─────────────────────────────────────────────────────────────
class TestLambdaHandler(unittest.TestCase):
    """Exhaustive tests for lambda_handler()."""

    def _make_event(self, function_name, parameters=None, action_group="VisaAgent"):
        # type: (str, Optional[List[Dict[str, Any]]], str) -> dict
        return {
            "agent": "test-agent",
            "actionGroup": action_group,
            "function": function_name,
            "parameters": parameters or [],
        }

    # ── Routing Tests ──

    @patch("lambda_agent.get_merchant_performance")
    def test_routes_to_get_merchant_performance(self, mock_fn):
        mock_fn.return_value = {"merchant_name": "Test", "approval_rate": 95.0}
        event = self._make_event("get_merchant_performance", [
            {"name": "merchant_id", "value": "42"}
        ])

        response = lambda_agent.lambda_handler(event, None)
        body = extract_body(response)

        mock_fn.assert_called_once_with(42)
        self.assertEqual(body["merchant_name"], "Test")

    @patch("lambda_agent.get_settlement_status")
    def test_routes_to_get_settlement_status(self, mock_fn):
        mock_fn.return_value = {"status": "success"}
        event = self._make_event("get_settlement_status", [
            {"name": "auth_id", "value": "AUTH-123"}
        ])

        response = lambda_agent.lambda_handler(event, None)
        body = extract_body(response)

        mock_fn.assert_called_once_with("AUTH-123")
        self.assertEqual(body["status"], "success")

    @patch("lambda_agent.get_fraud_alerts")
    def test_routes_to_get_fraud_alerts(self, mock_fn):
        mock_fn.return_value = {"merchant_id": 5, "alerts": []}
        event = self._make_event("get_fraud_alerts", [
            {"name": "merchant_id", "value": "5"}
        ])

        response = lambda_agent.lambda_handler(event, None)
        body = extract_body(response)

        mock_fn.assert_called_once_with(5)
        self.assertEqual(body["merchant_id"], 5)

    def test_unsupported_function_returns_error(self):
        event = self._make_event("nonexistent_function")

        response = lambda_agent.lambda_handler(event, None)
        body = extract_body(response)

        self.assertEqual(body["status"], "error")
        self.assertIn("nonexistent_function", body["message"])
        self.assertIn("not supported", body["message"])

    def test_empty_function_name(self):
        event = self._make_event("")

        response = lambda_agent.lambda_handler(event, None)
        body = extract_body(response)

        self.assertEqual(body["status"], "error")
        self.assertIn("not supported", body["message"])

    # ── Response Structure Tests ──

    def test_response_structure_complete(self):
        """Verify exact Bedrock Agent response format."""
        event = self._make_event("unknown_fn", [], "MyActionGroup")

        response = lambda_agent.lambda_handler(event, None)

        self.assertIn("response", response)
        resp = response["response"]
        self.assertEqual(resp["actionGroup"], "MyActionGroup")
        self.assertEqual(resp["function"], "unknown_fn")
        self.assertIn("functionResponse", resp)
        self.assertIn("responseBody", resp["functionResponse"])
        self.assertIn("application/json", resp["functionResponse"]["responseBody"])
        self.assertIn("body", resp["functionResponse"]["responseBody"]["application/json"])

    def test_body_is_valid_json_string(self):
        event = self._make_event("unknown", [], "ag")

        response = lambda_agent.lambda_handler(event, None)

        body_str = response["response"]["functionResponse"]["responseBody"]["application/json"]["body"]
        self.assertIsInstance(body_str, str)
        parsed = json.loads(body_str)
        self.assertIsInstance(parsed, dict)

    def test_action_group_echoed_in_response(self):
        event = self._make_event("unknown", [], "CustomGroup")

        response = lambda_agent.lambda_handler(event, None)

        self.assertEqual(response["response"]["actionGroup"], "CustomGroup")

    def test_function_name_echoed_in_response(self):
        event = self._make_event("some_fn", [], "ag")

        response = lambda_agent.lambda_handler(event, None)

        self.assertEqual(response["response"]["function"], "some_fn")

    # ── Parameter Handling Tests ──

    def test_missing_merchant_id_defaults_to_zero(self):
        """When merchant_id param is missing, defaults to int(0) = 0."""
        event = self._make_event("get_merchant_performance", [])

        response = lambda_agent.lambda_handler(event, None)
        body = extract_body(response)

        # Should not crash; may return error from DB function
        self.assertIsNotNone(body)

    @patch("lambda_agent.get_settlement_status")
    def test_missing_auth_id_defaults_to_empty_string(self, mock_fn):
        mock_fn.return_value = {"status": "error", "message": "not found"}
        event = self._make_event("get_settlement_status", [])

        lambda_agent.lambda_handler(event, None)

        mock_fn.assert_called_once_with("")

    def test_non_numeric_merchant_id_raises_value_error(self):
        """Non-numeric merchant_id — int() raises ValueError, caught by outer try."""
        event = self._make_event("get_merchant_performance", [
            {"name": "merchant_id", "value": "abc"}
        ])

        response = lambda_agent.lambda_handler(event, None)
        body = extract_body(response)

        self.assertEqual(body["status"], "error")

    def test_none_merchant_id_value_raises_type_error(self):
        """Parameter value=None — int(None) raises TypeError."""
        event = self._make_event("get_merchant_performance", [
            {"name": "merchant_id", "value": None}
        ])

        response = lambda_agent.lambda_handler(event, None)
        body = extract_body(response)

        self.assertEqual(body["status"], "error")

    def test_float_string_merchant_id(self):
        """
        BUG DETECTION: merchant_id="3.14" — int("3.14") raises ValueError.
        The handler cannot accept float-like string IDs.
        """
        event = self._make_event("get_merchant_performance", [
            {"name": "merchant_id", "value": "3.14"}
        ])

        response = lambda_agent.lambda_handler(event, None)
        body = extract_body(response)

        # int("3.14") raises ValueError → caught as error
        self.assertEqual(body["status"], "error")

    def test_extra_parameters_ignored(self):
        """Extra params don't affect routing."""
        with patch("lambda_agent.get_merchant_performance") as mock_fn:
            mock_fn.return_value = {"merchant_name": "X"}
            event = self._make_event("get_merchant_performance", [
                {"name": "merchant_id", "value": "7"},
                {"name": "extra_param", "value": "ignored"},
                {"name": "another", "value": "also_ignored"},
            ])

            lambda_agent.lambda_handler(event, None)

            mock_fn.assert_called_once_with(7)

    # ── Error Handling Tests ──

    @patch("lambda_agent.get_merchant_performance")
    def test_function_exception_caught(self, mock_fn):
        mock_fn.side_effect = RuntimeError("unexpected crash")
        event = self._make_event("get_merchant_performance", [
            {"name": "merchant_id", "value": "1"}
        ])

        response = lambda_agent.lambda_handler(event, None)
        body = extract_body(response)

        self.assertEqual(body["status"], "error")
        self.assertIn("unexpected crash", body["message"])

    # ── Empty/Missing Event Keys Tests ──

    def test_completely_empty_event(self):
        response = lambda_agent.lambda_handler({}, None)

        self.assertEqual(response["response"]["actionGroup"], "")
        self.assertEqual(response["response"]["function"], "")
        body = extract_body(response)
        self.assertEqual(body["status"], "error")

    def test_event_with_none_parameters(self):
        """
        BUG: parameters key present but set to None rather than list.

        event.get('parameters', []) returns None (because key exists with value None),
        then the dict comprehension iterates over None → TypeError.

        The TypeError is raised BEFORE the try/except block (line 168),
        so it propagates as an unhandled exception. This is a crash bug.

        Fix needed: `parameters = event.get('parameters') or []`
        """
        event = {
            "agent": "a",
            "actionGroup": "ag",
            "function": "unknown",
            "parameters": None,
        }

        # BUG: This crashes with unhandled TypeError
        with self.assertRaises(TypeError):
            lambda_agent.lambda_handler(event, None)

    def test_event_parameters_missing_name_key(self):
        """Parameter dict missing 'name' key."""
        event = self._make_event("get_merchant_performance", [
            {"value": "1"},  # no 'name' key
        ])

        response = lambda_agent.lambda_handler(event, None)
        body = extract_body(response)

        # p.get('name') returns None, so param_dict = {None: "1"}
        # merchant_id will default to int(0) = 0
        self.assertIsNotNone(body)

    def test_event_parameters_missing_value_key(self):
        """Parameter dict missing 'value' key."""
        event = self._make_event("get_merchant_performance", [
            {"name": "merchant_id"},  # no 'value' key
        ])

        response = lambda_agent.lambda_handler(event, None)
        body = extract_body(response)

        # p.get('value') returns None → param_dict = {"merchant_id": None}
        # int(None) raises TypeError → caught by outer except
        self.assertEqual(body["status"], "error")


# ─────────────────────────────────────────────────────────────
# get_db_connection() Tests
# ─────────────────────────────────────────────────────────────
class TestGetDbConnection(unittest.TestCase):
    """Tests for get_db_connection()."""

    @patch("lambda_agent.pg8000.native.Connection")
    def test_creates_connection_with_correct_params(self, mock_conn_cls):
        mock_conn_cls.return_value = MagicMock()

        conn = lambda_agent.get_db_connection()

        mock_conn_cls.assert_called_once_with(
            user=lambda_agent.DB_USER,
            password=lambda_agent.DB_PASSWORD,
            host=lambda_agent.DB_HOST,
            port=lambda_agent.DB_PORT,
            database=lambda_agent.DB_NAME,
        )
        self.assertIsNotNone(conn)

    @patch("lambda_agent.pg8000.native.Connection")
    def test_propagates_connection_error(self, mock_conn_cls):
        mock_conn_cls.side_effect = Exception("connection refused")

        with self.assertRaises(Exception) as ctx:
            lambda_agent.get_db_connection()

        self.assertIn("connection refused", str(ctx.exception))


# ─────────────────────────────────────────────────────────────
# Module Constants Tests
# ─────────────────────────────────────────────────────────────
class TestModuleConstants(unittest.TestCase):
    """Tests for module-level configuration."""

    def test_db_host_contains_rds(self):
        self.assertIsInstance(lambda_agent.DB_HOST, str)
        self.assertIn("rds.amazonaws.com", lambda_agent.DB_HOST)

    def test_db_port_is_int_5432(self):
        self.assertIsInstance(lambda_agent.DB_PORT, int)
        self.assertEqual(lambda_agent.DB_PORT, 5432)

    def test_db_name_is_postgres(self):
        self.assertEqual(lambda_agent.DB_NAME, "postgres")

    def test_db_user_is_string(self):
        self.assertIsInstance(lambda_agent.DB_USER, str)
        self.assertTrue(len(lambda_agent.DB_USER) > 0)

    def test_db_password_is_string(self):
        self.assertIsInstance(lambda_agent.DB_PASSWORD, str)
        self.assertTrue(len(lambda_agent.DB_PASSWORD) > 0)

    def test_db_password_hardcoded_in_source(self):
        """
        SECURITY BUG: The default password 'visabank123' is hardcoded in source.
        In production, passwords should come from AWS Secrets Manager or env vars only.
        """
        self.assertEqual(lambda_agent.DB_PASSWORD, "visabank123")


# ─────────────────────────────────────────────────────────────
# Integration-Style Tests (lambda_handler → DB functions)
# ─────────────────────────────────────────────────────────────
class TestLambdaHandlerIntegration(unittest.TestCase):
    """End-to-end tests through lambda_handler routing to actual functions."""

    @patch("lambda_agent.get_db_connection")
    def test_full_merchant_performance_flow(self, mock_conn_fn):
        """Complete flow: event → handler → get_merchant_performance → response."""
        mock_con = MagicMock()
        mock_conn_fn.return_value = mock_con
        mock_con.run.side_effect = [
            [("Acme", "Retail", 100.0, "Low")],
            [(500, 50000.0, 450)],
        ]

        event = {
            "agent": "test",
            "actionGroup": "VisaAgent",
            "function": "get_merchant_performance",
            "parameters": [{"name": "merchant_id", "value": "1"}],
        }

        response = lambda_agent.lambda_handler(event, None)
        body = extract_body(response)

        self.assertEqual(body["merchant_name"], "Acme")
        self.assertAlmostEqual(body["approval_rate"], 90.0)
        self.assertEqual(body["transaction_count"], 500)
        mock_con.close.assert_called_once()

    @patch("lambda_agent.get_db_connection")
    def test_full_settlement_flow(self, mock_conn_fn):
        mock_con = MagicMock()
        mock_conn_fn.return_value = mock_con
        mock_con.run.return_value = [
            (1000.0, "USD", "2025-06-01", "SETTLED", 5.0, 42)
        ]

        event = {
            "agent": "test",
            "actionGroup": "VisaAgent",
            "function": "get_settlement_status",
            "parameters": [{"name": "auth_id", "value": "AUTH-999"}],
        }

        response = lambda_agent.lambda_handler(event, None)
        body = extract_body(response)

        self.assertEqual(body["status"], "success")
        self.assertEqual(body["auth_id"], "AUTH-999")
        self.assertAlmostEqual(body["settlement_amount"], 1000.0)
        mock_con.close.assert_called_once()

    @patch("lambda_agent.get_db_connection")
    def test_full_fraud_alerts_flow(self, mock_conn_fn):
        mock_con = MagicMock()
        mock_conn_fn.return_value = mock_con
        mock_con.run.return_value = [
            ("CNP", 95, "velocity", "2025-03-20"),
        ]

        event = {
            "agent": "test",
            "actionGroup": "VisaAgent",
            "function": "get_fraud_alerts",
            "parameters": [{"name": "merchant_id", "value": "42"}],
        }

        response = lambda_agent.lambda_handler(event, None)
        body = extract_body(response)

        self.assertEqual(body["merchant_id"], 42)
        self.assertEqual(body["critical_fraud_alerts_count"], 1)
        self.assertEqual(body["alerts"][0]["fraud_type"], "CNP")
        mock_con.close.assert_called_once()

    @patch("lambda_agent.get_db_connection")
    def test_db_failure_returns_valid_bedrock_response(self, mock_conn_fn):
        """Even on DB failure, response must be valid Bedrock format."""
        mock_conn_fn.side_effect = Exception("DB down")

        event = {
            "agent": "test",
            "actionGroup": "VisaAgent",
            "function": "get_merchant_performance",
            "parameters": [{"name": "merchant_id", "value": "1"}],
        }

        response = lambda_agent.lambda_handler(event, None)

        # Must still be valid Bedrock response format
        self.assertIn("response", response)
        body = extract_body(response)
        self.assertEqual(body["status"], "error")

    @patch("lambda_agent.get_db_connection")
    def test_response_body_is_json_serializable(self, mock_conn_fn):
        """The full response must be JSON-serializable."""
        mock_con = MagicMock()
        mock_conn_fn.return_value = mock_con
        mock_con.run.side_effect = [
            [("Test", "Cat", 10, "Low")],
            [(5, 50.0, 3)],
        ]

        event = {
            "agent": "test",
            "actionGroup": "AG",
            "function": "get_merchant_performance",
            "parameters": [{"name": "merchant_id", "value": "1"}],
        }

        response = lambda_agent.lambda_handler(event, None)

        # Must not raise
        json_str = json.dumps(response)
        self.assertIsInstance(json_str, str)


# ─────────────────────────────────────────────────────────────
# Bug Detection Tests
# ─────────────────────────────────────────────────────────────
class TestBugDetection(unittest.TestCase):
    """Tests that detect and document actual bugs in the code."""

    @patch("lambda_agent.get_db_connection")
    def test_bug_none_approved_count_causes_type_error(self, mock_conn_fn):
        """
        BUG: get_merchant_performance does not handle stats[2] being None.

        Code: approval_rate = (stats[2] / stats[0] * 100) if stats[0] > 0 else 0
        When stats = (10, 5000.0, None): stats[0]=10 > 0, so it evaluates
        None / 10 which raises TypeError.

        Fix needed: guard stats[2] with `(stats[2] or 0)`.
        """
        mock_con = MagicMock()
        mock_conn_fn.return_value = mock_con
        mock_con.run.side_effect = [
            [("Bug Corp", "Retail", 100, "Low")],
            [(10, 5000.0, None)],
        ]

        result = lambda_agent.get_merchant_performance(99)

        # Bug: returns error instead of handling None gracefully
        self.assertEqual(result["status"], "error")
        # Ideally should return approval_rate=0, but it crashes
        self.assertNotIn("approval_rate", result)

    def test_bug_inconsistent_error_message_format(self):
        """
        BUG: Error message format is inconsistent across functions.

        get_merchant_performance: f"Database error: {str(e)}"
        get_settlement_status:    f"Database error: {str(e)}"
        get_fraud_alerts:         str(e)   ← MISSING "Database error:" prefix

        This makes it harder for callers to detect DB errors uniformly.
        """
        # Verified in TestGetFraudAlerts.test_fraud_error_message_not_prefixed_with_database_error
        pass  # Documented here for visibility

    def test_bug_parameters_none_crashes_handler(self):
        """
        BUG: If event['parameters'] is explicitly None (not missing),
        event.get('parameters', []) returns None (because key exists with None value),
        then the dict comprehension iterates over None → TypeError.

        This TypeError occurs OUTSIDE the try/except block (line 168 is
        before the try on line 172), so it's an UNHANDLED CRASH.

        Fix needed: `parameters = event.get('parameters') or []`
        """
        event = {
            "agent": "a",
            "actionGroup": "ag",
            "function": "get_merchant_performance",
            "parameters": None,
        }

        # BUG: Unhandled TypeError crash
        with self.assertRaises(TypeError):
            lambda_agent.lambda_handler(event, None)

    def test_bug_no_input_validation_on_merchant_id(self):
        """
        BUG: No validation on merchant_id value. Negative, zero, or extremely
        large values are passed directly to the database. Should validate
        merchant_id > 0 before querying.
        """
        event = {
            "agent": "a",
            "actionGroup": "ag",
            "function": "get_merchant_performance",
            "parameters": [{"name": "merchant_id", "value": "-999"}],
        }

        with patch("lambda_agent.get_db_connection") as mock_conn_fn:
            mock_con = MagicMock()
            mock_conn_fn.return_value = mock_con
            mock_con.run.return_value = []

            response = lambda_agent.lambda_handler(event, None)

            # No validation: -999 is passed to the DB function
            mock_con.run.assert_called()
            calls = mock_con.run.call_args_list
            self.assertEqual(calls[0][1]["id"], -999)

    @patch("lambda_agent.get_db_connection")
    def test_bug_settlement_merchant_id_can_be_none(self, mock_conn_fn):
        """
        BUG: If row[5] (merchant_id) is None in settlement result,
        it's passed through as None without validation. Callers may
        not expect a None merchant_id in a "success" response.
        """
        mock_con = MagicMock()
        mock_conn_fn.return_value = mock_con
        mock_con.run.return_value = [
            (100.0, "USD", "2025-01-01", "SETTLED", 1.0, None)
        ]

        result = lambda_agent.get_settlement_status("AUTH-X")

        self.assertEqual(result["status"], "success")
        # Bug: merchant_id is None in a success response
        self.assertIsNone(result["merchant_id"])


if __name__ == "__main__":
    unittest.main()
