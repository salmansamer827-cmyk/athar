from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Optional


class TradeOutcome(str, Enum):
    WIN = "WIN"
    LOSS = "LOSS"
    UNKNOWN = "UNKNOWN"


@dataclass(frozen=True)
class BacktestTrade:
    timestamp: object

    entry: float
    stop_loss: float
    take_profit: float

    risk_r: float
    reward_r: float

    outcome: TradeOutcome

    realized_r: float

    market_state: str
    probability: float

    transaction_cost_r: float = 0.0


@dataclass(frozen=True)
class BacktestMetrics:
    trades: int

    wins: int
    losses: int

    win_rate: float

    gross_profit_r: float
    gross_loss_r: float

    net_r: float

    expectancy_r: float

    profit_factor: Optional[float]

    max_drawdown_r: float
