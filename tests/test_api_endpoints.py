"""
Integration Tests for FastAPI Core Engine Service.
Verifies REST endpoints for real-time quant metrics, multi-agent audits, and TT200 accounting.
"""

from fastapi.testclient import TestClient

from src.api.main import app

client = TestClient(app)


def test_api_health_check():
    """Verify /health endpoint returns healthy status and metadata."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["version"] == "0.1.0"
    assert "cache" in data


def test_api_get_realtime_metrics():
    """Verify /api/v1/metrics/realtime/{symbol} returns complete quant schemas."""
    response = client.get("/api/v1/metrics/realtime/BTC")
    assert response.status_code == 200
    data = response.json()
    assert data["symbol"] == "BTCUSDT"
    assert data["sla_passed"] is True
    assert "spot" in data
    assert "futures" in data
    assert "whale" in data
    assert "etf" in data
    assert "vesting" in data


def test_api_analyze_crypto_setup():
    """Verify POST /api/v1/analyze runs the full multi-agent audit."""
    payload = {
        "symbol": "BTCUSDT",
        "execution_mode": "DUAL_AUDIT",
        "proposed_action": "BUY_SPOT_DCA",
        "proposed_entry": 95000.0,
        "time_horizon_days": 30,
    }
    response = client.post("/api/v1/analyze", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["symbol"] == "BTCUSDT"
    assert data["anti_fomo_verdict"] in [
        "SCALE_IN_SPOT",
        "PROCEED_WITH_CAUTION",
        "REJECT_SETUP_TOO_RISKY",
    ]
    assert len(data["fatal_socratic_questions"]) == 3
    assert 0.0 <= data["fomo_index"] <= 100.0


def test_api_tt200_portfolio_balance_sheet():
    """Verify GET /api/v1/accounting/portfolio/tt200 returns Circular 200 balance sheet."""
    response = client.get("/api/v1/accounting/portfolio/tt200?btc_price=95000.0&eth_price=3400.0")
    assert response.status_code == 200
    data = response.json()
    assert data["cash_balance_usd"] > 0.0
    assert "total_book_value_usd" in data
    assert "total_market_value_usd" in data
    assert "total_impairment_provision_usd" in data
    assert len(data["positions"]) >= 2


def test_api_record_tt200_transaction():
    """Verify POST /api/v1/accounting/transaction records a new trade voucher."""
    tx_payload = {
        "symbol": "SOLUSDT",
        "account": "TK_121",
        "action": "BUY",
        "quantity": 10.0,
        "price_usd": 180.0,
        "fee_usd": 2.0,
        "notes": "FastAPI integration test buy",
    }
    response = client.post("/api/v1/accounting/transaction", json=tx_payload)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "recorded"
    assert data["details"]["action"] == "BUY"


def test_api_cache_stats_and_traces():
    """Verify cache stats and LLMOps trace retrieval endpoints."""
    stats_res = client.get("/api/v1/cache/stats")
    assert stats_res.status_code == 200
    stats = stats_res.json()
    assert "hits" in stats
    assert "misses" in stats

    traces_res = client.get("/api/v1/llmops/traces?limit=5")
    assert traces_res.status_code == 200
    traces = traces_res.json()
    assert isinstance(traces, list)


def test_api_bot_control_and_status():
    """Verify automated trading bot control and status endpoints."""
    # Start bot in PAPER_TRADING mode
    ctrl_res = client.post(
        "/api/v1/bot/control",
        json={"action": "START", "mode": "PAPER_TRADING"},
    )
    assert ctrl_res.status_code == 200
    ctrl_data = ctrl_res.json()
    assert ctrl_data["status"] == "RUNNING"
    assert ctrl_data["mode"] == "PAPER_TRADING"

    # Check status
    stat_res = client.get("/api/v1/bot/status")
    assert stat_res.status_code == 200
    stat_data = stat_res.json()
    assert stat_data["status"] == "RUNNING"
    assert "performance" in stat_data
    assert "active_positions" in stat_data

    # Stop bot
    stop_res = client.post("/api/v1/bot/control", json={"action": "STOP"})
    assert stop_res.status_code == 200
    assert stop_res.json()["status"] == "STOPPED"
