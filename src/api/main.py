"""
FastAPI Core Engine Service for CryptoIntel-Engine.
Exposes REST and WebSocket endpoints for real-time quant metrics, multi-agent Socratic audits,
and Circular 200/2014/TT-BTC accounting & impairment valuations.
"""

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from datetime import UTC, datetime
from typing import Any

from fastapi import FastAPI, HTTPException, Query, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from src.agents.graph import run_crypto_audit
from src.engine.accounting_tt200 import (
    CryptoTransaction,
    InventoryCostMethod,
    TransactionType,
    TT200AccountCode,
    TT200AccountingEngine,
)
from src.engine.core_quant import CoreQuantEngine, get_symbol_market_profile
from src.llmops.cache import audit_cache
from src.llmops.langfuse_tracer import llmops_tracer

# Initialize shared accounting ledger for Circular 200 demonstration
accounting_ledger = TT200AccountingEngine(
    costing_method=InventoryCostMethod.FIFO,
    initial_cash_usd=1_000_000.0,
)

# Seed with standard initial demo positions under TT 200
accounting_ledger.record_transaction(
    CryptoTransaction(
        tx_id="tx_seed_btc_cold",
        timestamp=datetime.now(UTC),
        symbol="BTCUSDT",
        account=TT200AccountCode.TK_228,
        action=TransactionType.BUY,
        quantity=5.0,
        price_usd=62000.0,
        fee_usd=15.0,
        notes="Strategic Accumulation Lot 1 in Cold Storage",
    )
)
accounting_ledger.record_transaction(
    CryptoTransaction(
        tx_id="tx_seed_eth_trading",
        timestamp=datetime.now(UTC),
        symbol="ETHUSDT",
        account=TT200AccountCode.TK_121,
        action=TransactionType.BUY,
        quantity=30.0,
        price_usd=3500.0,
        fee_usd=25.0,
        notes="Swing trading inventory",
    )
)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan manager to initialize and teardown services."""
    await audit_cache.initialize()
    yield


app = FastAPI(
    title="CryptoIntel-Engine Core API",
    description="Dual-Engine Crypto Intelligence: Deterministic Quant & Multi-Agent Socratic Risk Auditing",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class AuditRequest(BaseModel):
    """Request payload for running a multi-agent risk audit."""

    symbol: str = Field(default="BTCUSDT", description="Asset ticker (e.g. BTCUSDT, ETHUSDT)")
    execution_mode: str = Field(default="DUAL_AUDIT", description="DUAL_AUDIT, MODE_SPOT, or MODE_FUTURES")
    proposed_action: str | None = Field(default="BUY_SPOT_DCA", description="Proposed trade action")
    proposed_entry: float | None = Field(default=None, description="Planned entry price in USD")
    time_horizon_days: int = Field(default=30, ge=1, le=365)


class TransactionRequest(BaseModel):
    """Request payload to record an accounting transaction under TT 200."""

    symbol: str
    account: TT200AccountCode
    action: TransactionType
    quantity: float = Field(..., gt=0.0)
    price_usd: float = Field(..., ge=0.0)
    fee_usd: float = Field(default=0.0, ge=0.0)
    notes: str = ""


@app.get("/health", tags=["System"])
async def health_check() -> dict[str, Any]:
    """Health check endpoint reporting engine status and cache state."""
    return {
        "status": "healthy",
        "service": "CryptoIntel-Engine Core API",
        "version": "0.1.0",
        "timestamp": datetime.now(UTC).isoformat(),
        "cache": audit_cache.get_stats(),
        "langfuse_enabled": llmops_tracer.is_enabled,
    }


@app.get("/api/v1/metrics/realtime/{symbol}", tags=["Quantitative Engine"])
async def get_realtime_metrics(symbol: str) -> dict[str, Any]:
    """
    Retrieve deterministic quantitative evaluation (< 0.5s SLA) for a given symbol.
    Pure arithmetic calculation with zero LLM hallucination.
    """
    clean_symbol = symbol.upper().replace("USDT", "") + "USDT"
    profile = get_symbol_market_profile(clean_symbol)

    engine = CoreQuantEngine()
    current_px = profile["current_price"]
    audit_data = engine.run_full_quant_audit(
        symbol=clean_symbol,
        current_price=current_px,
        high_24h=current_px * 1.02,
        low_24h=current_px * 0.98,
        market_cap=profile["market_cap"],
        realized_cap=profile["realized_cap"],
        std_market_cap=profile["std_market_cap"],
        sma_200d=profile["sma_200d"],
        sma_200w=profile["sma_200w"],
        sma_111d=profile["sma_111d"],
        sma_350d=profile["sma_350d"],
        open_interest_usd=profile["open_interest_usd"],
        oi_24h_ago=profile["oi_24h_ago"],
        circulating_supply=profile["circulating_supply"],
        total_supply=profile["total_supply"],
        fdv_usd=profile["fdv_usd"],
    )

    return {
        "symbol": clean_symbol,
        "execution_latency_ms": audit_data["execution_latency_ms"],
        "sla_passed": audit_data["sla_passed"],
        "spot": audit_data["spot"].model_dump(),
        "futures": audit_data["futures"].model_dump(),
        "whale": audit_data["whale"].model_dump(),
        "etf": audit_data["etf"].model_dump(),
        "vesting": audit_data["vesting"].model_dump(),
    }


@app.post("/api/v1/analyze", tags=["Multi-Agent Audit"])
async def analyze_crypto_setup(req: AuditRequest) -> dict[str, Any]:
    """
    Run full multi-agent Socratic audit on a proposed trade setup.
    Synthesizes Specialist Dossiers, 3 Fatal Questions, and Anti-FOMO Verdict.
    """
    clean_symbol = req.symbol.upper().replace("USDT", "") + "USDT"
    profile = get_symbol_market_profile(clean_symbol)

    engine = CoreQuantEngine()
    current_px = profile["current_price"]
    quant_data = engine.run_full_quant_audit(
        symbol=clean_symbol,
        current_price=current_px,
        high_24h=current_px * 1.02,
        low_24h=current_px * 0.98,
        market_cap=profile["market_cap"],
        realized_cap=profile["realized_cap"],
        std_market_cap=profile["std_market_cap"],
        sma_200d=profile["sma_200d"],
        sma_200w=profile["sma_200w"],
        sma_111d=profile["sma_111d"],
        sma_350d=profile["sma_350d"],
        open_interest_usd=profile["open_interest_usd"],
        oi_24h_ago=profile["oi_24h_ago"],
        circulating_supply=profile["circulating_supply"],
        total_supply=profile["total_supply"],
        fdv_usd=profile["fdv_usd"],
    )

    spot_dict = quant_data["spot"].model_dump()
    futures_dict = quant_data["futures"].model_dump()
    whale_dict = quant_data["whale"].model_dump()
    etf_dict = quant_data["etf"].model_dump()
    vesting_dict = quant_data["vesting"].model_dump()

    whale_dict["exchange_netflow_24h_usd"] = whale_dict.get("netflow_24h_usd", 0.0)
    etf_dict["netflow_24h_usd"] = etf_dict.get("daily_net_inflow_usd", 0.0)
    vesting_dict["unlock_percent_of_circulating"] = vesting_dict.get(
        "next_unlock_pct_of_circulating", 0.0
    )

    audit_state = await run_crypto_audit(
        symbol=clean_symbol,
        execution_mode=req.execution_mode,
        spot_valuation_data=spot_dict,
        futures_squeeze_data=futures_dict,
        whale_flow_data=whale_dict,
        etf_flow_data=etf_dict,
        token_vesting_data=vesting_dict,
        proposed_action=req.proposed_action,
        proposed_entry=req.proposed_entry,
        time_horizon_days=req.time_horizon_days,
    )

    return {
        "symbol": clean_symbol,
        "execution_mode": req.execution_mode,
        "anti_fomo_verdict": audit_state["anti_fomo_verdict"],
        "fomo_index": audit_state["fomo_index"],
        "fatal_socratic_questions": audit_state["fatal_socratic_questions"],
        "worst_case_invalidation_price": audit_state["worst_case_invalidation_price"],
        "thesis_refutations": audit_state["thesis_refutations"],
        "investment_memo": audit_state["investment_memo"],
        "telegram_alert": audit_state["telegram_alert_payload"],
        "errors": audit_state["errors"],
        "trace_id": audit_state["trace_id"],
    }


@app.get("/api/v1/accounting/portfolio/tt200", tags=["Circular 200 Accounting"])
async def get_tt200_portfolio_balance_sheet(
    btc_price: float = Query(default=95000.0, description="Current Mark Price for BTC"),
    eth_price: float = Query(default=3400.0, description="Current Mark Price for ETH"),
    sol_price: float = Query(default=185.0, description="Current Mark Price for SOL"),
) -> dict[str, Any]:
    """
    Generate audited portfolio balance sheet and impairment provisions under Circular 200/2014/TT-BTC.
    Separates Realized Income (TK 515/635) from Unrealized Revaluation (TK 412).
    """
    mark_prices = {
        "BTCUSDT": btc_price,
        "ETHUSDT": eth_price,
        "SOLUSDT": sol_price,
    }
    balance_sheet = accounting_ledger.evaluate_portfolio(mark_prices)
    return balance_sheet.model_dump()


@app.post("/api/v1/accounting/transaction", tags=["Circular 200 Accounting"])
async def record_tt200_transaction(req: TransactionRequest) -> dict[str, Any]:
    """
    Post a new crypto transaction into the Circular 200 ledger.
    Supports FIFO and Moving Average inventory costing methods.
    """
    tx_id = f"tx_{int(datetime.now(UTC).timestamp())}_{req.symbol.lower()}"
    tx = CryptoTransaction(
        tx_id=tx_id,
        timestamp=datetime.now(UTC),
        symbol=req.symbol.upper().replace("USDT", "") + "USDT",
        account=req.account,
        action=req.action,
        quantity=req.quantity,
        price_usd=req.price_usd,
        fee_usd=req.fee_usd,
        notes=req.notes,
    )
    try:
        result = accounting_ledger.record_transaction(tx)
        return {"status": "recorded", "details": result}
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        ) from e


@app.get("/api/v1/cache/stats", tags=["LLMOps & System"])
async def get_cache_stats() -> dict[str, Any]:
    """Return cache hit/miss statistics and Redis status."""
    return audit_cache.get_stats()


@app.get("/api/v1/llmops/traces", tags=["LLMOps & System"])
async def get_llmops_traces(limit: int = Query(default=10, ge=1, le=50)) -> list[dict[str, Any]]:
    """Return recent LLMOps audit traces and latency telemetry."""
    return llmops_tracer.get_recent_traces(limit=limit)
