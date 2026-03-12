# option-strategy-recognizer

> Identify options strategies from raw brokerage positions — Iron Condor, Bull Put Spread,
> Covered Call, and 20+ more — with zero external dependencies.

```
pip install option-strategy-recognizer
```

---

## What it does

Given a flat list of positions from any broker (stocks + options), this library groups them by
underlying and classifies each group as a named strategy. It also computes net Greeks,
max profit/loss, breakevens, and DTE automatically.

**Input:** raw positions (any broker — see adapters below)
**Output:** structured strategy groups, ready for risk analysis or display

---

## Quick start

```python
from option_strategy_recognizer import OptionStrategyRecognizer, PositionRecord

positions = [
    # AAPL Bull Put Spread: short 180P / long 175P, same expiry
    PositionRecord(
        symbol="AAPL240119P00180000", asset_category="OPT",
        put_call="P", strike=180.0, expiry="20240119",
        multiplier=100, position=-1,
        cost_basis_price=3.50, mark_price=2.80, unrealized_pnl=70.0,
        delta=-0.28, gamma=0.04, theta=-0.12, vega=0.18,
        underlying_symbol="AAPL",
    ),
    PositionRecord(
        symbol="AAPL240119P00175000", asset_category="OPT",
        put_call="P", strike=175.0, expiry="20240119",
        multiplier=100, position=+1,
        cost_basis_price=1.80, mark_price=1.40, unrealized_pnl=-40.0,
        delta=0.18, gamma=0.03, theta=-0.08, vega=0.12,
        underlying_symbol="AAPL",
    ),
]

recognizer = OptionStrategyRecognizer()
groups = recognizer.recognize(positions)

for g in groups:
    print(g.strategy_type)   # "Bull Put Spread"
    print(g.intent)           # "income"
    print(g.net_credit)       # 170.0
    print(g.max_profit)       # 170.0
    print(g.max_loss)         # 330.0
    print(g.breakevens)       # [178.30]
    print(g.dte)              # days to expiry
    print(g.net_delta)        # -0.10
```

---

## Real-world example: analyzing a full portfolio

```python
from option_strategy_recognizer import OptionStrategyRecognizer, PositionRecord

# Positions from your broker (write a small adapter — see below)
positions = load_positions_from_broker()

recognizer = OptionStrategyRecognizer()
groups = recognizer.recognize(positions)

for g in groups:
    print(f"{g.underlying:8s}  {g.strategy_type:20s}  "
          f"DTE={g.dte:3d}  P&L=${g.net_pnl:+,.0f}  "
          f"delta={g.net_delta:+.2f}")
```

Sample output:

```
AAPL      Bull Put Spread      DTE= 18  P&L=+$170  delta=-0.10
NVDA      Iron Condor          DTE= 32  P&L=-$340  delta=+0.04
TSLA      Naked Put            DTE=  7  P&L=-$890  delta=-0.45
MSFT      Covered Call         DTE= 25  P&L=+$230  delta=+0.72
SPY       Protective Put       DTE= 60  P&L=-$120  delta=+0.95
```

---

## Strategies recognized

| Intent | Strategies |
|--------|-----------|
| Income | Naked Put, Naked Call, Cash-Secured Put, Covered Call, Bull Put Spread, Bear Call Spread, Iron Condor, Iron Butterfly, Ratio Put Spread, Ratio Call Spread, PMCC |
| Hedge | Protective Put, LEAPS Put, Collar |
| Directional | Bull Call Spread, Bear Put Spread, LEAPS Call, Long Stock, Short Stock |
| Speculation | Straddle, Strangle, Long Put, Long Call |
| Mixed | Calendar Spread, Diagonal Spread |

Multi-expiry and ratio spreads are handled. Unrecognized combinations are labeled `Unclassified`.

---

## Broker adapters

The library defines its own `PositionRecord` dataclass. Write a small adapter for your broker:

### Interactive Brokers (Flex XML)

```python
from option_strategy_recognizer import PositionRecord

def from_ib_flex(ib_pos) -> PositionRecord:
    return PositionRecord(
        symbol=ib_pos.symbol,
        asset_category=ib_pos.asset_category,
        put_call=ib_pos.put_call,
        strike=ib_pos.strike,
        expiry=ib_pos.expiry,
        multiplier=ib_pos.multiplier,
        position=ib_pos.position,
        cost_basis_price=ib_pos.cost_basis_price,
        mark_price=ib_pos.mark_price,
        unrealized_pnl=ib_pos.unrealized_pnl,
        delta=ib_pos.delta,
        gamma=ib_pos.gamma,
        theta=ib_pos.theta,
        vega=ib_pos.vega,
        underlying_symbol=ib_pos.underlying_symbol,
        currency=ib_pos.currency,
    )
```

### CSV / spreadsheet

```python
import csv
from option_strategy_recognizer import PositionRecord

def from_csv(row: dict) -> PositionRecord:
    return PositionRecord(
        symbol=row["symbol"],
        asset_category="OPT" if row["type"] == "option" else "STK",
        put_call=row.get("put_call", ""),
        strike=float(row.get("strike", 0)),
        expiry=row.get("expiry", "").replace("-", ""),  # normalize to YYYYMMDD
        multiplier=float(row.get("multiplier", 100)),
        position=float(row["quantity"]),
        cost_basis_price=float(row.get("avg_cost", 0)),
        mark_price=float(row["last_price"]),
        unrealized_pnl=float(row.get("unrealized_pnl", 0)),
        delta=float(row.get("delta", 0)),
        gamma=float(row.get("gamma", 0)),
        theta=float(row.get("theta", 0)),
        vega=float(row.get("vega", 0)),
        underlying_symbol=row.get("underlying", row["symbol"]),
    )

with open("positions.csv") as f:
    positions = [from_csv(row) for row in csv.DictReader(f)]

groups = OptionStrategyRecognizer().recognize(positions)
```

---

## StrategyGroup fields

| Field | Type | Description |
|-------|------|-------------|
| `underlying` | str | Underlying ticker (e.g. "AAPL") |
| `strategy_type` | str | Strategy name (e.g. "Bull Put Spread") |
| `intent` | str | "income" / "hedge" / "directional" / "speculation" / "mixed" |
| `legs` | list[PositionRecord] | Option legs |
| `stock_leg` | PositionRecord \| None | Stock position if part of strategy |
| `net_delta` | float | Sum of all leg deltas |
| `net_theta` | float | Sum of all leg thetas |
| `max_profit` | float \| None | None = unlimited |
| `max_loss` | float \| None | None = unlimited (naked positions) |
| `breakevens` | list[float] | Breakeven price(s) at expiry |
| `dte` | int | Days to expiry of primary leg |
| `net_pnl` | float | Unrealized P&L of all legs combined |
| `net_credit` | float | Net premium received (>0) or paid (<0) |

---

## Requirements

- Python 3.10+
- No external dependencies

---

## License

MIT

---

## Related

- [option-risk-engine](https://github.com/quant-tools/option-risk-engine) — risk analysis on top of these strategy groups (assignment risk, margin alerts, stress test)
