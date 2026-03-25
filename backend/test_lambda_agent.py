"""
Comprehensive unit tests for lambda_agent.py

Tests cover:
- get_merchant_performance: normal, not-found, DB errors, edge cases
- get_settlement_status: normal, not-found, DB errors, edge cases
- get_fraud_alerts: normal, empty results, DB errors
- lambda_handler: routing, parameter extraction, error handling, response format
"""

import json
import os
import sys
import unittest
from unittest.mock import patch, MagicMock, call
from typing import Optional, List, Any, Dict

# Ensure the backend directory is importable
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import lambda_agent


class TestGetMerchantPerformance(unittest.TestCase):
    """Tests for get_merchant_performance()"""

    @patch("lambda_agent.get_db_connection")
    def test_successful_merchant_lookup(self, mock_conn_fn):
        """Normal case: merchant exists with transactions."""
        mock_con = MagicMock()
        mock_conn_fn.return_value = mock_con

        # First call: merchant data
        # Second call: auth stats (total_txns, total_volume, approved_count)
        mock_con.run.side_effect = [
            [("Acme Corp", "Retail", 150.50, "Low")],
            [(1000, 250000.0, 900)]
        ]

        result = lambda_agent.get_merchant_performance(1)

        self.assertEqual(result["merchant_name"], "Acme Corp")
        self.assertEqual(result["category"], "Retail")
        self.assertAlmostEqual(result["avg_ticket_size"], 150.50)
        self.assertEqual(result["risk_level"], "Low")
        self.assertEqual(result["transaction_count"], 1000)
        self.assertAlmostEqual(result["total_volume"], 250000.0)
        self.assertAlmostEqual(result["approval_rate"], 90.0)
        mock_con.close.assert_called_once()

    @patch("lambda_agent.get_db_connection")
    def test_merchant_not_found(self, mock_conn_fn):
        """Merchant ID does not exist in database."""
        mock_con = MagicMock()
        mock_conn_fn.return_value = mock_con
        mock_con.run.side_effect = [
            [],  # No merchant data
        ]

        result = lambda_agent.get_merchant_performance(9999)

        self.assertEqual(result["status"], "error")
        self.assertIn("9999", result["message"])
        self.assertIn("not found", result["message"])
        mock_con.close.assert_called_once()

    @patch("lambda_agent.get_db_connection")
    def test_zero_transactions(self, mock_conn_fn):
        """Merchant exists but has zero transactions — tests division-by-zero guard."""
        mock_con = MagicMock()
        mock_conn_fn.return_value = mock_con
        mock_con.run.side_effect = [
            [("Empty Shop", "Food", 0, "Low")],
            [(0, None, 0)]  # zero txns
        ]

        result = lambda_agent.get_merchant_performance(42)

        self.assertEqual(result["merchant_name"], "Empty Shop")
        self.assertEqual(result["approval_rate"], 0)
        self.assertEqual(result["total_volume"], 0.0)
        self.assertEqual(result["transaction_count"], 0)
        mock_con.close.assert_called_once()

    @patch("lambda_agent.get_db_connection")
    def test_null_avg_ticket_size(self, mock_conn_fn):
        """avg_ticket_size is None in DB."""
        mock_con = MagicMock()
        mock_conn_fn.return_value = mock_con
        mock_con.run.side_effect = [
            [("NullTicket Inc", "Services", None, "Medium")],
            [(10, 5000.0, 8)]
        ]

        result = lambda_agent.get_merchant_performance(5)

        self.assertEqual(result["avg_ticket_size"], 0.0)
        mock_con.close.assert_called_once()

    @patch("lambda_agent.get_db_connection")
    def test_null_total_volume(self, mock_conn_fn):
        """SUM(amount) returns None (e.g. all amounts null)."""
        mock_con = MagicMock()
        mock_conn_fn.return_value = mock_con
        mock_con.run.side_effect = [
            [("NullVol Corp", "Tech", 100, "High")],
            [(5, None, 3)]
        ]

        result = lambda_agent.get_merchant_performance(7)

        self.assertEqual(result["total_volume"], 0.0)
        self.assertAlmostEqual(result["approval_rate"], 60.0)
        mock_con.close.assert_called_once()

    @patch("lambda_agent.get_db_connection")
    def test_db_connection_error(self, mock_conn_fn):
        """Database connection failure."""
        mock_conn_fn.side_effect = Exception("Connection refused")

        result = lambda_agent.get_merchant_performance(1)

        self.assertEqual(result["status"], "error")
        self.assertIn("Connection refused", result["message"])

    @patch("lambda_agent.get_db_connection")
    def test_db_query_error(self, mock_conn_fn):
        """Database query failure after connection succeeds."""
        mock_con = MagicMock()
        mock_conn_fn.return_value = mock_con
        mock_con.run.side_effect = Exception("relation does not exist")

        result = lambda_agent.get_merchant_performance(1)

        self.assertEqual(result["status"], "error")
        self.assertIn("relation does not exist", result["message"])
        mock_con.close.assert_called_once()

    @patch("lambda_agent.get_db_connection")
    def test_approval_rate_rounding(self, mock_conn_fn):
        """Approval rate is properly rounded to 2 decimal places."""
        mock_con = MagicMock()
        mock_conn_fn.return_value = mock_con
        mock_con.run.side_effect = [
            [("Round Corp", "Retail", 50, "Low")],
            [(3, 300.0, 1)]  # 1/3 = 33.333...%
        ]

        result = lambda_agent.get_merchant_performance(10)

        self.assertAlmostEqual(result["approval_rate"], 33.33, places=2)
        mock_con.close.assert_called_once()

    @patch("lambda_agent.get_db_connection")
    def test_100_percent_approval(self, mock_conn_fn):
        """All transactions approved."""
        mock_con = MagicMock()
        mock_conn_fn.return_value = mock_con
        mock_con.run.side_effect = [
            [("Perfect Corp", "Luxury", 500, "Low")],
            [(200, 100000.0, 200)]
        ]

        result = lambda_agent.get_merchant_performance(20)

        self.assertAlmostEqual(result["approval_rate"], 100.0)

    @patch("lambda_agent.get_db_connection")
    def test_connection_closed_even_on_merchant_not_found(self, mock_conn_fn):
        """Ensure connection is closed in the finally block even on early return."""
        mock_con = MagicMock()
        mock_conn_fn.return_value = mock_con
        mock_con.run.return_value = []

        lambda_agent.get_merchant_performance(1)

        mock_con.close.assert_called_once()

    @patch("lambda_agent.get_db_connection")
    def test_approved_count_none_causes_type_error(self, mock_conn_fn):
        """
        BUG DETECTION: If approved_count (stats[2]) is None and total_txns > 0,
        the expression `stats[2] / stats[0] * 100` will raise TypeError
        because None / int is not valid. The code does NOT guard against this.
        """
        mock_con = MagicMock()
        mock_conn_fn.return_value = mock_con
        mock_con.run.side_effect = [
            [("BugTest Corp", "Retail", 100, "Low")],
            [(10, 5000.0, None)]  # approved_count is None
        ]

        # This should ideally handle None gracefully, but the code does:
        #   approval_rate = (stats[2] / stats[0] * 100) if stats[0] > 0 else 0
        # stats[2] is None, stats[0] is 10 > 0, so it tries None / 10 => TypeError
        # The outer except catches it and returns an error dict.
        result = lambda_agent.get_merchant_performance(99)

        # The bug manifests as a database error response instead of handling None gracefully
        self.assertEqual(result["status"], "error")
        self.assertIn("Database error", result["message"])


class TestGetSettlementStatus(unittest.TestCase):
    """Tests for get_settlement_status()"""

    @patch("lambda_agent.get_db_connection")
    def test_successful_settlement_lookup(self, mock_conn_fn):
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
        mock_con.close.assert_called_once()

    @patch("lambda_agent.get_db_connection")
    def test_settlement_not_found(self, mock_conn_fn):
        mock_con = MagicMock()
        mock_conn_fn.return_value = mock_con
        mock_con.run.return_value = []

        result = lambda_agent.get_settlement_status("NONEXISTENT")

        self.assertEqual(result["status"], "error")
        self.assertIn("NONEXISTENT", result["message"])
        mock_con.close.assert_called_once()

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
        mock_con.close.assert_called_once()

    @patch("lambda_agent.get_db_connection")
    def test_db_error(self, mock_conn_fn):
        mock_con = MagicMock()
        mock_conn_fn.return_value = mock_con
        mock_con.run.side_effect = Exception("timeout expired")

        result = lambda_agent.get_settlement_status("AUTH-003")

        self.assertEqual(result["status"], "error")
        self.assertIn("timeout expired", result["message"])
        mock_con.close.assert_called_once()

    @patch("lambda_agent.get_db_connection")
    def test_connection_error(self, mock_conn_fn):
        mock_conn_fn.side_effect = Exception("host not found")

        result = lambda_agent.get_settlement_status("AUTH-004")

        self.assertEqual(result["status"], "error")
        self.assertIn("host not found", result["message"])

    @patch("lambda_agent.get_db_connection")
    def test_settlement_date_conversion(self, mock_conn_fn):
        """Date object is converted to string."""
        from datetime import date
        mock_con = MagicMock()
        mock_conn_fn.return_value = mock_con
        mock_con.run.return_value = [
            (100.0, "GBP", date(2025, 6, 15), "SETTLED", 1.0, 5)
        ]

        result = lambda_agent.get_settlement_status("AUTH-005")

        self.assertEqual(result["date"], "2025-06-15")


class TestGetFraudAlerts(unittest.TestCase):
    """Tests for get_fraud_alerts()"""

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
        self.assertEqual(result["alerts"][1]["reason"], "New device + high value")
        mock_con.close.assert_called_once()

    @patch("lambda_agent.get_db_connection")
    def test_no_alerts(self, mock_conn_fn):
        mock_con = MagicMock()
        mock_conn_fn.return_value = mock_con
        mock_con.run.return_value = []

        result = lambda_agent.get_fraud_alerts(1)

        self.assertEqual(result["merchant_id"], 1)
        self.assertEqual(result["critical_fraud_alerts_count"], 0)
        self.assertEqual(result["alerts"], [])
        mock_con.close.assert_called_once()

    @patch("lambda_agent.get_db_connection")
    def test_db_error(self, mock_conn_fn):
        mock_con = MagicMock()
        mock_conn_fn.return_value = mock_con
        mock_con.run.side_effect = Exception("permission denied")

        result = lambda_agent.get_fraud_alerts(1)

        self.assertEqual(result["status"], "error")
        self.assertIn("permission denied", result["message"])
        mock_con.close.assert_called_once()

    @patch("lambda_agent.get_db_connection")
    def test_exactly_five_alerts_max(self, mock_conn_fn):
        """The SQL uses LIMIT 5, so verify we handle up to 5 results."""
        mock_con = MagicMock()
        mock_conn_fn.return_value = mock_con
        mock_con.run.return_value = [
            ("Type1", 90, "Reason1", "2025-01-01"),
            ("Type2", 85, "Reason2", "2025-01-02"),
            ("Type3", 80, "Reason3", "2025-01-03"),
            ("Type4", 75, "Reason4", "2025-01-04"),
            ("Type5", 71, "Reason5", "2025-01-05"),
        ]

        result = lambda_agent.get_fraud_alerts(10)

        self.assertEqual(result["critical_fraud_alerts_count"], 5)
        self.assertEqual(len(result["alerts"]), 5)

    @patch("lambda_agent.get_db_connection")
    def test_connection_failure(self, mock_conn_fn):
        mock_conn_fn.side_effect = Exception("SSL handshake failed")

        result = lambda_agent.get_fraud_alerts(1)

        self.assertEqual(result["status"], "error")
        self.assertIn("SSL handshake failed", result["message"])


class TestLambdaHandler(unittest.TestCase):
    """Tests for lambda_handler()"""

    def _make_event(self, function_name, parameters=None, action_group="VisaAgent"):
        # type: (str, Optional[List[Dict[str, Any]]], str) -> dict
        return {
            "agent": "test-agent",
            "actionGroup": action_group,
            "function": function_name,
            "parameters": parameters or []
        }

    def _extract_body(self, response):
        """Extract the parsed JSON body from the Bedrock response format."""
        raw = response["response"]["functionResponse"]["responseBody"]["application/json"]["body"]
        return json.loads(raw)

    @patch("lambda_agent.get_merchant_performance")
    def test_route_get_merchant_performance(self, mock_fn):
        mock_fn.return_value = {"merchant_name": "Test", "approval_rate": 95.0}
        event = self._make_event("get_merchant_performance", [
            {"name": "merchant_id", "value": "42"}
        ])

        response = lambda_agent.lambda_handler(event, None)

        mock_fn.assert_called_once_with(42)
        body = self._extract_body(response)
        self.assertEqual(body["merchant_name"], "Test")
        self.assertEqual(response["response"]["function"], "get_merchant_performance")
        self.assertEqual(response["response"]["actionGroup"], "VisaAgent")

    @patch("lambda_agent.get_settlement_status")
    def test_route_get_settlement_status(self, mock_fn):
        mock_fn.return_value = {"status": "success", "settlement_status": "COMPLETED"}
        event = self._make_event("get_settlement_status", [
            {"name": "auth_id", "value": "AUTH-123"}
        ])

        response = lambda_agent.lambda_handler(event, None)

        mock_fn.assert_called_once_with("AUTH-123")
        body = self._extract_body(response)
        self.assertEqual(body["status"], "success")

    @patch("lambda_agent.get_fraud_alerts")
    def test_route_get_fraud_alerts(self, mock_fn):
        mock_fn.return_value = {"merchant_id": 5, "critical_fraud_alerts_count": 0, "alerts": []}
        event = self._make_event("get_fraud_alerts", [
            {"name": "merchant_id", "value": "5"}
        ])

        response = lambda_agent.lambda_handler(event, None)

        mock_fn.assert_called_once_with(5)
        body = self._extract_body(response)
        self.assertEqual(body["critical_fraud_alerts_count"], 0)

    def test_unsupported_function(self):
        event = self._make_event("nonexistent_function")

        response = lambda_agent.lambda_handler(event, None)

        body = self._extract_body(response)
        self.assertEqual(body["status"], "error")
        self.assertIn("nonexistent_function", body["message"])
        self.assertIn("not supported", body["message"])

    def test_empty_function_name(self):
        event = self._make_event("")

        response = lambda_agent.lambda_handler(event, None)

        body = self._extract_body(response)
        self.assertEqual(body["status"], "error")

    def test_missing_parameters_defaults(self):
        """When merchant_id is missing, defaults to int('') which should raise ValueError."""
        event = self._make_event("get_merchant_performance", [])

        response = lambda_agent.lambda_handler(event, None)

        # param_dict.get('merchant_id', 0) returns 0, so int(0) = 0
        # This actually works and calls get_merchant_performance(0)
        body = self._extract_body(response)
        # It will be a DB error or merchant-not-found since merchant_id=0 likely doesn't exist
        # But the handler itself should not crash
        self.assertIsNotNone(body)

    def test_invalid_merchant_id_non_numeric(self):
        """Non-numeric merchant_id should cause ValueError caught by outer try."""
        event = self._make_event("get_merchant_performance", [
            {"name": "merchant_id", "value": "not_a_number"}
        ])

        response = lambda_agent.lambda_handler(event, None)

        body = self._extract_body(response)
        self.assertEqual(body["status"], "error")

    def test_response_structure(self):
        """Verify exact Bedrock Agent response structure."""
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
        # body should be a JSON string
        body_str = resp["functionResponse"]["responseBody"]["application/json"]["body"]
        self.assertIsInstance(body_str, str)
        json.loads(body_str)  # Should not raise

    def test_missing_event_keys_use_defaults(self):
        """Event with missing keys should use defaults from .get()."""
        event = {}  # completely empty

        response = lambda_agent.lambda_handler(event, None)

        self.assertEqual(response["response"]["actionGroup"], "")
        self.assertEqual(response["response"]["function"], "")
        body = self._extract_body(response)
        self.assertEqual(body["status"], "error")

    def test_parameters_none_value(self):
        """Parameter with None value for merchant_id."""
        event = self._make_event("get_merchant_performance", [
            {"name": "merchant_id", "value": None}
        ])

        response = lambda_agent.lambda_handler(event, None)

        body = self._extract_body(response)
        # int(None) raises TypeError, caught by outer try
        self.assertEqual(body["status"], "error")

    @patch("lambda_agent.get_settlement_status")
    def test_settlement_with_empty_auth_id(self, mock_fn):
        """When auth_id parameter is missing, defaults to empty string."""
        mock_fn.return_value = {"status": "error", "message": "No settlement found"}
        event = self._make_event("get_settlement_status", [])

        response = lambda_agent.lambda_handler(event, None)

        mock_fn.assert_called_once_with("")

    def test_parameters_is_empty_list(self):
        """Parameters field is an empty list."""
        event = self._make_event("get_fraud_alerts", [])

        response = lambda_agent.lambda_handler(event, None)

        # merchant_id defaults to int(0) = 0 which is valid
        body = self._extract_body(response)
        self.assertIsNotNone(body)

    @patch("lambda_agent.get_merchant_performance")
    def test_function_exception_caught(self, mock_fn):
        """If the routed function raises, the outer try/except catches it."""
        mock_fn.side_effect = RuntimeError("unexpected crash")
        event = self._make_event("get_merchant_performance", [
            {"name": "merchant_id", "value": "1"}
        ])

        response = lambda_agent.lambda_handler(event, None)

        body = self._extract_body(response)
        self.assertEqual(body["status"], "error")
        self.assertIn("unexpected crash", body["message"])

    def test_param_dict_construction(self):
        """Verify parameter extraction works with multiple params."""
        event = {
            "agent": "a",
            "actionGroup": "ag",
            "function": "get_merchant_performance",
            "parameters": [
                {"name": "merchant_id", "value": "7"},
                {"name": "extra_param", "value": "ignored"}
            ]
        }

        with patch("lambda_agent.get_merchant_performance") as mock_fn:
            mock_fn.return_value = {"merchant_name": "X"}
            lambda_agent.lambda_handler(event, None)
            mock_fn.assert_called_once_with(7)


class TestModuleConstants(unittest.TestCase):
    """Tests for module-level configuration."""

    def test_default_db_host(self):
        self.assertIsInstance(lambda_agent.DB_HOST, str)
        self.assertIn("rds.amazonaws.com", lambda_agent.DB_HOST)

    def test_default_db_port_is_int(self):
        self.assertIsInstance(lambda_agent.DB_PORT, int)
        self.assertEqual(lambda_agent.DB_PORT, 5432)

    def test_default_db_name(self):
        self.assertEqual(lambda_agent.DB_NAME, "postgres")

    @patch.dict(os.environ, {"DB_PORT": "3306"})
    def test_db_port_from_env(self):
        """Verify that DB_PORT reads from environment when set."""
        # Module constants are set at import time, so this tests the pattern
        # rather than live behavior. We verify the int() conversion works.
        self.assertEqual(int(os.environ.get("DB_PORT", 5432)), 3306)


class TestGetDbConnection(unittest.TestCase):
    """Tests for get_db_connection()"""

    @patch("lambda_agent.pg8000.native.Connection")
    def test_creates_connection_with_correct_params(self, mock_conn_cls):
        mock_conn_cls.return_value = MagicMock()

        conn = lambda_agent.get_db_connection()

        mock_conn_cls.assert_called_once_with(
            user=lambda_agent.DB_USER,
            password=lambda_agent.DB_PASSWORD,
            host=lambda_agent.DB_HOST,
            port=lambda_agent.DB_PORT,
            database=lambda_agent.DB_NAME
        )
        self.assertIsNotNone(conn)

    @patch("lambda_agent.pg8000.native.Connection")
    def test_propagates_connection_error(self, mock_conn_cls):
        mock_conn_cls.side_effect = Exception("connection refused")

        with self.assertRaises(Exception) as ctx:
            lambda_agent.get_db_connection()

        self.assertIn("connection refused", str(ctx.exception))


class TestEdgeCasesAndBugs(unittest.TestCase):
    """Edge case and bug-detection tests."""

    @patch("lambda_agent.get_db_connection")
    def test_merchant_performance_close_called_on_query_exception(self, mock_conn_fn):
        """Ensure connection is closed even when second query fails."""
        mock_con = MagicMock()
        mock_conn_fn.return_value = mock_con
        mock_con.run.side_effect = [
            [("Merchant", "Cat", 100, "Low")],
            Exception("query failed")
        ]

        result = lambda_agent.get_merchant_performance(1)

        self.assertEqual(result["status"], "error")
        mock_con.close.assert_called_once()

    @patch("lambda_agent.get_db_connection")
    def test_settlement_status_close_called_on_exception(self, mock_conn_fn):
        mock_con = MagicMock()
        mock_conn_fn.return_value = mock_con
        mock_con.run.side_effect = Exception("broken pipe")

        result = lambda_agent.get_settlement_status("X")

        mock_con.close.assert_called_once()

    @patch("lambda_agent.get_db_connection")
    def test_fraud_alerts_close_called_on_exception(self, mock_conn_fn):
        mock_con = MagicMock()
        mock_conn_fn.return_value = mock_con
        mock_con.run.side_effect = Exception("timeout")

        result = lambda_agent.get_fraud_alerts(1)

        mock_con.close.assert_called_once()

    @patch("lambda_agent.get_db_connection")
    def test_merchant_performance_with_negative_merchant_id(self, mock_conn_fn):
        """Negative merchant_id — no validation, passes through to DB."""
        mock_con = MagicMock()
        mock_conn_fn.return_value = mock_con
        mock_con.run.side_effect = [[], ]

        result = lambda_agent.get_merchant_performance(-1)

        self.assertEqual(result["status"], "error")
        self.assertIn("-1", result["message"])

    @patch("lambda_agent.get_db_connection")
    def test_settlement_with_all_null_fields(self, mock_conn_fn):
        """All settlement fields are None except merchant_id."""
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

    def test_lambda_handler_preserves_action_group_in_response(self):
        """Action group from event is echoed back in response."""
        event = {
            "agent": "a",
            "actionGroup": "CustomGroup",
            "function": "unknown",
            "parameters": []
        }

        response = lambda_agent.lambda_handler(event, None)

        self.assertEqual(response["response"]["actionGroup"], "CustomGroup")

    def test_lambda_handler_body_is_valid_json_string(self):
        """The body field must be a JSON string, not a dict."""
        event = {
            "agent": "a",
            "actionGroup": "ag",
            "function": "unknown",
            "parameters": []
        }

        response = lambda_agent.lambda_handler(event, None)

        body_raw = response["response"]["functionResponse"]["responseBody"]["application/json"]["body"]
        self.assertIsInstance(body_raw, str)
        parsed = json.loads(body_raw)
        self.assertIsInstance(parsed, dict)

    @patch("lambda_agent.get_db_connection")
    def test_fraud_alerts_detected_time_converted_to_string(self, mock_conn_fn):
        """detected_time is converted via str()."""
        from datetime import datetime
        mock_con = MagicMock()
        mock_conn_fn.return_value = mock_con
        dt = datetime(2025, 3, 20, 14, 30, 0)
        mock_con.run.return_value = [
            ("CNP", 92, "reason", dt)
        ]

        result = lambda_agent.get_fraud_alerts(1)

        self.assertEqual(result["alerts"][0]["detected_time"], str(dt))

    @patch("lambda_agent.get_db_connection")
    def test_merchant_performance_queries_use_merchant_id_param(self, mock_conn_fn):
        """Verify parameterized queries are used (not string interpolation)."""
        mock_con = MagicMock()
        mock_conn_fn.return_value = mock_con
        mock_con.run.side_effect = [
            [("M", "C", 10, "L")],
            [(1, 100.0, 1)]
        ]

        lambda_agent.get_merchant_performance(77)

        # Both queries should pass id=77 as a keyword argument
        calls = mock_con.run.call_args_list
        self.assertEqual(len(calls), 2)
        self.assertEqual(calls[0][1]["id"], 77)
        self.assertEqual(calls[1][1]["id"], 77)


if __name__ == "__main__":
    unittest.main()
