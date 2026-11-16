"""
Deterministic Accounting & Asset Valuation Engine under Circular 200/2014/TT-BTC.
STRICT INVARIANT: PURE PYTHON / NUMPY ONLY. ZERO LLM IMPORTS ALLOWED.
Standardizes crypto asset management, FIFO/Moving Average costing,
and Impairment Provisions (TK 2291).
"""

from collections import deque
from datetime import UTC, datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class TT200AccountCode(str, Enum):
    """Vietnamese Accounting System Chart of Accounts under Circular 200."""

    TK_112 = "TK_112"  # Bank Deposits & Liquid Cash Equivalence (USD / Stablecoins)
    TK_121 = "TK_121"  # Trading Securities (Short-term Swing & Position Trades)
    TK_128 = "TK_128"  # Held-to-Maturity Investments (Fixed Staking / Term Lending)
    TK_228 = "TK_228"  # Strategic Long-term Investments (Cold Storage Accumulation)
    TK_2291 = "TK_2291"  # Impairment Provision for Financial Asset Devaluation
    TK_412 = "TK_412"  # Asset Revaluation Difference (Unrealized Paper PnL)
    TK_515 = "TK_515"  # Financial Income (Realized Gains & Funding Fees Earned)
    TK_635 = "TK_635"  # Financial Expenses (Realized Losses & Impairment Charges)


class InventoryCostMethod(str, Enum):
    """Inventory Cost Allocation Method for Crypto Assets."""

    FIFO = "FIFO"
    MOVING_AVERAGE = "MOVING_AVERAGE"


class TransactionType(str, Enum):
    """Trading / Transfer Action Type."""

    BUY = "BUY"
    SELL = "SELL"
    TRANSFER_IN = "TRANSFER_IN"
    TRANSFER_OUT = "TRANSFER_OUT"


class CryptoTransaction(BaseModel):
    """Audit-trail transaction record compliant with TT 200 vouchers."""

    model_config = ConfigDict(strict=True, frozen=True)

    tx_id: str
    timestamp: datetime
    symbol: str
    account: TT200AccountCode
    action: TransactionType
    quantity: float = Field(..., gt=0.0)
    price_usd: float = Field(..., ge=0.0)
    fee_usd: float = Field(default=0.0, ge=0.0)
    notes: str = ""


class PositionLot(BaseModel):
    """Granular lot tracking for First-In-First-Out (FIFO) cost allocation."""

    model_config = ConfigDict(strict=True)

    lot_id: str
    purchase_time: datetime
    quantity_remaining: float
    unit_cost_usd: float


class AssetBookPosition(BaseModel):
    """Audited balance sheet position for a single asset and account."""

    model_config = ConfigDict(strict=True, frozen=True)

    symbol: str
    account: TT200AccountCode
    total_quantity: float
    total_book_value_usd: float
    average_unit_cost_usd: float
    current_mark_price_usd: float
    market_value_usd: float
    unrealized_pnl_usd: float  # Tracked in TK 412
    impairment_provision_required_usd: float  # Target TK 2291 balance
    is_impaired: bool


class TT200PortfolioBalanceSheet(BaseModel):
    """
    Complete Financial Position & Ledger Summary compliant with Circular 200/2014/TT-BTC.
    Separates Realized Income (TK 515/635) from Unrealized Revaluation (TK 412).
    """

    model_config = ConfigDict(strict=True, frozen=True)

    generated_at: datetime
    costing_method: InventoryCostMethod
    cash_balance_usd: float  # TK 112
    trading_assets_book_value_usd: float  # TK 121
    strategic_assets_book_value_usd: float  # TK 228
    total_book_value_usd: float
    total_market_value_usd: float
    cumulative_realized_pnl_usd: float  # Net of TK 515 and TK 635
    unrealized_revaluation_usd: float  # TK 412
    total_impairment_provision_usd: float  # TK 2291
    net_carrying_value_usd: float  # Total Book Value - TK 2291
    net_asset_value_usd: float  # Cash + Market Value of Portfolio
    positions: list[AssetBookPosition]


class TT200AccountingEngine:
    """
    Deterministic Financial Accounting Engine for Crypto Assets.
    Strictly implements inventory costing, book-value calculation, and impairment provisioning.
    """

    def __init__(
        self,
        costing_method: InventoryCostMethod = InventoryCostMethod.FIFO,
        initial_cash_usd: float = 1_000_000.0,
    ) -> None:
        self.costing_method = costing_method
        self.cash_balance_usd: float = float(initial_cash_usd)
        self.cumulative_realized_pnl: float = 0.0
        self.transactions: list[CryptoTransaction] = []

        # FIFO lot storage: key = (symbol, account) -> deque of PositionLot
        self._fifo_lots: dict[tuple[str, TT200AccountCode], deque[PositionLot]] = {}

        # Moving average aggregates: key = (symbol, account) -> {"qty": float, "book_value": float}
        self._moving_avg_totals: dict[tuple[str, TT200AccountCode], dict[str, float]] = {}

    def record_transaction(self, tx: CryptoTransaction) -> dict[str, Any]:
        """
        Record a buy or sell transaction and update ledger balances.
        Returns the transaction impact summary.
        """
        key = (tx.symbol.upper(), tx.account)

        if tx.action in [TransactionType.BUY, TransactionType.TRANSFER_IN]:
            res = self._handle_buy(tx, key)
        elif tx.action in [TransactionType.SELL, TransactionType.TRANSFER_OUT]:
            res = self._handle_sell(tx, key)
        else:
            raise ValueError(f"Unsupported transaction type: {tx.action}")

        self.transactions.append(tx)
        return res

    def _handle_buy(
        self, tx: CryptoTransaction, key: tuple[str, TT200AccountCode]
    ) -> dict[str, Any]:
        total_cost = (tx.quantity * tx.price_usd) + tx.fee_usd
        self.cash_balance_usd -= total_cost

        # Add lot for FIFO
        if key not in self._fifo_lots:
            self._fifo_lots[key] = deque()
        self._fifo_lots[key].append(
            PositionLot(
                lot_id=tx.tx_id,
                purchase_time=tx.timestamp,
                quantity_remaining=tx.quantity,
                unit_cost_usd=(total_cost / tx.quantity),
            )
        )

        # Update Moving Average aggregates
        if key not in self._moving_avg_totals:
            self._moving_avg_totals[key] = {"qty": 0.0, "book_value": 0.0}
        self._moving_avg_totals[key]["qty"] += tx.quantity
        self._moving_avg_totals[key]["book_value"] += total_cost

        return {
            "tx_id": tx.tx_id,
            "action": "BUY",
            "quantity": tx.quantity,
            "total_cost_usd": total_cost,
            "cash_remaining_usd": self.cash_balance_usd,
        }

    def _handle_sell(
        self, tx: CryptoTransaction, key: tuple[str, TT200AccountCode]
    ) -> dict[str, Any]:
        # Pre-validate inventory before mutating cash or ledger state
        if self.costing_method == InventoryCostMethod.FIFO:
            lots = self._fifo_lots.get(key)
            available_qty = sum(lot.quantity_remaining for lot in lots) if lots else 0.0
            if available_qty < tx.quantity - 1e-9:
                raise ValueError(
                    f"Insufficient inventory to sell {tx.quantity} of {key[0]} in account {key[1]}; available: {available_qty}"
                )
            cost_of_goods_sold = self._deplete_fifo(key, tx.quantity)
        else:
            totals = self._moving_avg_totals.get(key)
            available_qty = totals["qty"] if totals else 0.0
            if available_qty < tx.quantity - 1e-9:
                raise ValueError(
                    f"Insufficient inventory to sell {tx.quantity} of {key[0]} in account {key[1]}; available: {available_qty}"
                )
            cost_of_goods_sold = self._deplete_moving_average(key, tx.quantity)

        proceeds = (tx.quantity * tx.price_usd) - tx.fee_usd
        self.cash_balance_usd += proceeds

        realized_pnl = proceeds - cost_of_goods_sold
        self.cumulative_realized_pnl += realized_pnl

        return {
            "tx_id": tx.tx_id,
            "action": "SELL",
            "quantity": tx.quantity,
            "proceeds_usd": proceeds,
            "cost_basis_usd": cost_of_goods_sold,
            "realized_pnl_usd": realized_pnl,
            "cash_remaining_usd": self.cash_balance_usd,
        }

    def _deplete_fifo(self, key: tuple[str, TT200AccountCode], quantity_to_sell: float) -> float:
        lots = self._fifo_lots.get(key)
        if not lots:
            raise ValueError(f"No existing inventory for asset {key[0]} in account {key[1]}")

        remaining_to_deplete = quantity_to_sell
        total_cogs: float = 0.0

        while remaining_to_deplete > 1e-9 and lots:
            current_lot = lots[0]
            if current_lot.quantity_remaining <= remaining_to_deplete:
                depleted = current_lot.quantity_remaining
                total_cogs += depleted * current_lot.unit_cost_usd
                remaining_to_deplete -= depleted
                lots.popleft()
            else:
                depleted = remaining_to_deplete
                total_cogs += depleted * current_lot.unit_cost_usd
                current_lot.quantity_remaining -= depleted
                remaining_to_deplete = 0.0

        if remaining_to_deplete > 1e-9:
            raise ValueError(
                f"Insufficient inventory to sell {quantity_to_sell} of {key[0]}; shortfall: {remaining_to_deplete}"
            )

        # Also sync moving average totals for consistency
        if key in self._moving_avg_totals:
            self._moving_avg_totals[key]["qty"] -= quantity_to_sell
            self._moving_avg_totals[key]["book_value"] -= total_cogs

        return total_cogs

    def _deplete_moving_average(
        self, key: tuple[str, TT200AccountCode], quantity_to_sell: float
    ) -> float:
        totals = self._moving_avg_totals.get(key)
        if not totals or totals["qty"] < quantity_to_sell - 1e-9:
            raise ValueError(f"Insufficient inventory for asset {key[0]} in account {key[1]}")

        unit_cost = totals["book_value"] / totals["qty"] if totals["qty"] > 0 else 0.0
        cogs = quantity_to_sell * unit_cost

        totals["qty"] -= quantity_to_sell
        totals["book_value"] -= cogs

        return cogs

    def evaluate_portfolio(
        self, mark_prices: dict[str, float]
    ) -> TT200PortfolioBalanceSheet:
        """
        Evaluate full portfolio balance sheet under Circular 200.
        Calculates Mark-to-Market value, TK 2291 impairment provisions, and TK 412 unrealized gain/loss.
        """
        positions: list[AssetBookPosition] = []
        trading_book_val: float = 0.0
        strategic_book_val: float = 0.0
        total_market_val: float = 0.0
        total_impairment: float = 0.0

        # Collect unique asset keys
        all_keys = set(self._fifo_lots.keys()) | set(self._moving_avg_totals.keys())

        for symbol, account in sorted(all_keys, key=lambda x: (x[0], x[1].value)):
            qty: float = 0.0
            book_val: float = 0.0

            if self.costing_method == InventoryCostMethod.FIFO:
                lots = self._fifo_lots.get((symbol, account), deque())
                qty = sum(lot.quantity_remaining for lot in lots)
                book_val = sum(lot.quantity_remaining * lot.unit_cost_usd for lot in lots)
            else:
                totals = self._moving_avg_totals.get((symbol, account), {"qty": 0.0, "book_value": 0.0})
                qty = totals["qty"]
                book_val = totals["book_value"]

            if qty <= 1e-9:
                continue

            unit_cost = book_val / qty if qty > 0 else 0.0
            mark_price = mark_prices.get(symbol, unit_cost)
            market_val = qty * mark_price
            unrealized_pnl = market_val - book_val

            # Circular 200 Impairment Rule: max(0, Book Value - Market Value)
            impairment_target = max(0.0, book_val - market_val)
            is_impaired = impairment_target > 0.0

            if account == TT200AccountCode.TK_121:
                trading_book_val += book_val
            elif account == TT200AccountCode.TK_228:
                strategic_book_val += book_val

            total_market_val += market_val
            total_impairment += impairment_target

            positions.append(
                AssetBookPosition(
                    symbol=symbol,
                    account=account,
                    total_quantity=qty,
                    total_book_value_usd=book_val,
                    average_unit_cost_usd=unit_cost,
                    current_mark_price_usd=mark_price,
                    market_value_usd=market_val,
                    unrealized_pnl_usd=unrealized_pnl,
                    impairment_provision_required_usd=impairment_target,
                    is_impaired=is_impaired,
                )
            )

        total_book = sum(p.total_book_value_usd for p in positions)
        net_carrying = total_book - total_impairment
        nav = self.cash_balance_usd + total_market_val

        return TT200PortfolioBalanceSheet(
            generated_at=datetime.now(UTC),
            costing_method=self.costing_method,
            cash_balance_usd=self.cash_balance_usd,
            trading_assets_book_value_usd=trading_book_val,
            strategic_assets_book_value_usd=strategic_book_val,
            total_book_value_usd=total_book,
            total_market_value_usd=total_market_val,
            cumulative_realized_pnl_usd=self.cumulative_realized_pnl,
            unrealized_revaluation_usd=total_market_val - total_book,
            total_impairment_provision_usd=total_impairment,
            net_carrying_value_usd=net_carrying,
            net_asset_value_usd=nav,
            positions=positions,
        )


# Global shared accounting ledger instance under Circular 200/2014/TT-BTC
accounting_ledger = TT200AccountingEngine(
    costing_method=InventoryCostMethod.FIFO,
    initial_cash_usd=1_000_000.0,
)

# Seed standard baseline positions for live evaluation
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
        quantity=40.0,
        price_usd=2800.0,
        fee_usd=25.0,
        notes="Trading Lot 1 on CEX Inventory",
    )
)
