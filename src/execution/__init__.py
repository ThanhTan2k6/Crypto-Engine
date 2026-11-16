"""
Automated Quantitative Execution and Trading Bot Package for CryptoIntel-Engine.
"""

from src.execution.backtest_engine import BacktestResult, BacktestTrade, HistoricalBacktester
from src.execution.bot_coordinator import TradingBotCoordinator, trading_bot_coordinator
from src.execution.order_executor import BinanceLiveExecutor, PaperTradingEngine
from src.execution.risk_manager import PositionSizer, SocraticRiskFilter
from src.execution.schemas import (
    BotMode,
    BotPerformanceStats,
    BotStatus,
    OrderRequest,
    SignalDirection,
    StrategyType,
    TradeRecord,
    TradeSignal,
)
from src.execution.strategy_engine import QuantitativeStrategyEngine

__all__ = [
    "BacktestResult",
    "BacktestTrade",
    "BinanceLiveExecutor",
    "BotMode",
    "BotPerformanceStats",
    "BotStatus",
    "HistoricalBacktester",
    "OrderRequest",
    "PaperTradingEngine",
    "PositionSizer",
    "QuantitativeStrategyEngine",
    "SignalDirection",
    "SocraticRiskFilter",
    "StrategyType",
    "TradeRecord",
    "TradeSignal",
    "TradingBotCoordinator",
    "trading_bot_coordinator",
]
