"""
Deterministic Quant Engine: Mode Spot (Cycle Valuation & Accumulation).
STRICT INVARIANT: PURE PYTHON / NUMPY / PANDAS ONLY. ZERO LLM IMPORTS ALLOWED.
Calculates MVRV Z-Score, 200W-MA, Mayer Multiple, Pi Cycle, Algorithmic DCA & Take-Profit Zones.
"""

from datetime import UTC, datetime

from src.ingestion.schemas import CycleRegime, SpotCycleValuationSchema


class SpotCycleEngine:
    """Deterministic valuation engine for long-term spot cycle tops, bottoms, and accumulation."""

    @staticmethod
    def calculate_mvrv_zscore(
        market_cap: float, realized_cap: float, std_market_cap: float
    ) -> float:
        """
        Calculate MVRV Z-Score: (Market Cap - Realized Cap) / StdDev(Market Cap).
        """
        if std_market_cap <= 0.0:
            return 0.0
        return float((market_cap - realized_cap) / std_market_cap)

    @staticmethod
    def calculate_mayer_multiple(current_price: float, sma_200d: float) -> float:
        """
        Calculate Mayer Multiple: Current Price / 200-Day Simple Moving Average.
        """
        if sma_200d <= 0.0:
            return 1.0
        return float(current_price / sma_200d)

    @staticmethod
    def calculate_200w_ma_ratio(current_price: float, sma_200w: float) -> float:
        """
        Calculate ratio of Current Price relative to the 200-Week Moving Average baseline.
        """
        if sma_200w <= 0.0:
            return 1.0
        return float(current_price / sma_200w)

    @staticmethod
    def evaluate_pi_cycle_top(sma_111d: float, sma_350d: float) -> bool:
        """
        Pi Cycle Top Indicator: True when (111-day SMA * 2.0) crosses above 350-day SMA.
        """
        return bool((sma_111d * 2.0) >= sma_350d)

    @staticmethod
    def classify_cycle_regime(mvrv_zscore: float, mayer_multiple: float) -> CycleRegime:
        """
        Classify macro cycle into 5 distinct phases based on on-chain valuation.
        """
        if mvrv_zscore >= 5.0:
            return CycleRegime.CYCLE_TOP_EUPHORIA
        elif mvrv_zscore >= 3.5 or mayer_multiple >= 2.4:
            return CycleRegime.LATE_BULL_OVERHEATED
        elif mvrv_zscore >= 1.5:
            return CycleRegime.MID_BULL_EXPANSION
        elif mvrv_zscore >= 0.1:
            return CycleRegime.EARLY_ACCUMULATION
        else:
            return CycleRegime.CYCLE_BOTTOM_CAPITULATION

    @staticmethod
    def calculate_dca_zones(
        current_price: float, realized_price: float, sma_200w: float
    ) -> tuple[float, float, float]:
        """
        Calculate 3 algorithmic DCA accumulation levels:
        - Zone 1 (Conservative): Current Price * 0.92 (8% pull-back)
        - Zone 2 (Moderate): max(Realized Price, Current Price * 0.85)
        - Zone 3 (Aggressive / Capitulation Floor): 200W-MA
        """
        zone_1 = round(current_price * 0.92, 2)
        zone_2 = round(max(realized_price, current_price * 0.85), 2)
        zone_3 = round(min(sma_200w, current_price * 0.70), 2)
        return zone_1, zone_2, zone_3

    @staticmethod
    def calculate_take_profit_zones(current_price: float) -> tuple[float, float, float]:
        """
        Calculate 3 algorithmic profit-taking targets:
        - TP 1 (Initial De-risk): Current Price * 1.35 (+35%)
        - TP 2 (Mid-Cycle Extension): Current Price * 1.75 (+75%)
        - TP 3 (Cycle Peak Euphoria): Current Price * 2.50 (+150%)
        """
        tp_1 = round(current_price * 1.35, 2)
        tp_2 = round(current_price * 1.75, 2)
        tp_3 = round(current_price * 2.50, 2)
        return tp_1, tp_2, tp_3

    @staticmethod
    def calculate_recommended_spot_multiplier(cycle_regime: CycleRegime) -> float:
        """
        Scale spot allocation tranche size dynamically by cycle regime.
        """
        multipliers = {
            CycleRegime.CYCLE_BOTTOM_CAPITULATION: 2.0,
            CycleRegime.EARLY_ACCUMULATION: 1.5,
            CycleRegime.MID_BULL_EXPANSION: 1.0,
            CycleRegime.LATE_BULL_OVERHEATED: 0.3,
            CycleRegime.CYCLE_TOP_EUPHORIA: 0.0,
        }
        return multipliers.get(cycle_regime, 1.0)

    def evaluate(
        self,
        symbol: str,
        current_price: float,
        market_cap: float,
        realized_cap: float,
        std_market_cap: float,
        sma_200d: float,
        sma_200w: float,
        sma_111d: float,
        sma_350d: float,
        timestamp: datetime | None = None,
    ) -> SpotCycleValuationSchema:
        """Execute full deterministic spot cycle evaluation."""
        ts = timestamp or datetime.now(UTC)
        realized_price = realized_cap / (market_cap / current_price) if market_cap > 0 else current_price * 0.6
        
        mvrv_z = round(self.calculate_mvrv_zscore(market_cap, realized_cap, std_market_cap), 2)
        mayer = round(self.calculate_mayer_multiple(current_price, sma_200d), 2)
        pi_top = self.evaluate_pi_cycle_top(sma_111d, sma_350d)
        regime = self.classify_cycle_regime(mvrv_z, mayer)

        dca_1, dca_2, dca_3 = self.calculate_dca_zones(current_price, realized_price, sma_200w)
        tp_1, tp_2, tp_3 = self.calculate_take_profit_zones(current_price)
        multiplier = self.calculate_recommended_spot_multiplier(regime)

        return SpotCycleValuationSchema(
            symbol=symbol.upper(),
            timestamp=ts,
            current_price=float(current_price),
            mvrv_zscore=float(mvrv_z),
            realized_price=float(round(realized_price, 2)),
            sma_200w=float(round(sma_200w, 2)),
            mayer_multiple=float(mayer),
            pi_cycle_top_triggered=bool(pi_top),
            cycle_regime=regime,
            dca_zone_conservative=float(dca_1),
            dca_zone_moderate=float(dca_2),
            dca_zone_aggressive=float(dca_3),
            take_profit_target_1=float(tp_1),
            take_profit_target_2=float(tp_2),
            take_profit_target_3=float(tp_3),
            recommended_spot_multiplier=float(multiplier),
        )
