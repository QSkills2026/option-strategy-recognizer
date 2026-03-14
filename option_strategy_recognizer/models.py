"""Broker-agnostic data models for option strategy recognition."""
from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class PositionRecord:
    """One position lot from any broker.

    Fields follow Interactive Brokers Flex XML conventions but are broker-agnostic.
    Write a small adapter to convert your broker's format to this dataclass.
    """
    symbol: str
    asset_category: str       # "STK" | "OPT"
    put_call: str             # "P" | "C" | "" (empty for stocks)
    strike: float
    expiry: str               # "YYYYMMDD" or "" (empty for stocks)
    multiplier: float         # options contract multiplier (usually 100)
    position: float           # number of contracts/shares; negative = short
    cost_basis_price: float
    mark_price: float
    unrealized_pnl: float
    delta: float
    gamma: float
    theta: float
    vega: float
    underlying_symbol: str = ""   # underlying ticker for OPT positions
    currency: str = "USD"


@dataclass
class StrategyGroup:
    """One recognized options strategy for a single underlying."""
    underlying: str
    strategy_type: str   # e.g. "Iron Condor", "Bull Put Spread", "Naked Put"
    intent: str          # "income" | "hedge" | "directional" | "speculation" | "mixed" | "unknown"
    legs: List[PositionRecord] = field(default_factory=list)
    stock_leg: Optional[PositionRecord] = None
    modifiers: List[PositionRecord] = field(default_factory=list)
    net_delta: float = 0.0
    net_theta: float = 0.0
    net_vega: float = 0.0
    net_gamma: float = 0.0
    max_profit: Optional[float] = None        # None = unlimited
    max_loss: Optional[float] = None          # None = unlimited (naked positions)
    max_loss_downside: Optional[float] = None # put-side floor when max_loss=None (stock → $0)
    breakevens: List[float] = field(default_factory=list)
    expiry: str = ""     # primary leg expiry "YYYYMMDD"
    dte: int = 0         # days to expiry (computed)
    net_pnl: float = 0.0
    net_credit: float = 0.0   # >0 = received premium, <0 = paid premium
    currency: str = "USD"
