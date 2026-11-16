"""
Unit test for CoreQuantEngine SLA: Execution latency must be < 500ms (< 0.5s).
"""

from src.engine.core_quant import CoreQuantEngine


def test_core_quant_engine_performance_sla():
    engine = CoreQuantEngine()
    result = engine.run_full_quant_audit(
        symbol="BTCUSDT",
        current_price=95000.0,
        market_cap=1880000000000.0,
        realized_cap=750000000000.0,
        std_market_cap=300000000000.0,
        sma_200d=68000.0,
        sma_200w=48000.0,
        sma_111d=72000.0,
        sma_350d=65000.0,
        open_interest_usd=12000000000.0,
        oi_24h_ago=10500000000.0,
        funding_rate_8h=0.0008,
        long_short_ratio=2.5,
        bids=[[95000.0, 10.0], [94900.0, 20.0]],
        asks=[[95100.0, 40.0], [95200.0, 50.0]],
        high_24h=96500.0,
        low_24h=93500.0,
        inflow_24h_usd=850000000.0,
        outflow_24h_usd=1200000000.0,
        mean_netflow_30d=0.0,
        std_netflow_30d=250000000.0,
        tether_mint_7d_usd=1500000000.0,
        whale_transfers_count=8,
        daily_etf_inflow_usd=250000000.0,
        ibit_inflow_usd=180000000.0,
        fbtc_inflow_usd=70000000.0,
        cumulative_5d_etf_usd=890000000.0,
        avg_5d_spot_vol_usd=25000000000.0,
        circulating_supply=19800000.0,
        total_supply=21000000.0,
        fdv_usd=1995000000000.0,
    )

    assert result["symbol"] == "BTCUSDT"
    assert result["sla_passed"] is True
    # Verify execution latency is well under 500ms
    assert result["execution_latency_ms"] < 500.0
    assert result["spot_valuation"] is not None
    assert result["futures_risk"] is not None
    assert result["whale_flow"] is not None
    assert result["etf_flow"] is not None
    assert result["token_vesting"] is not None
