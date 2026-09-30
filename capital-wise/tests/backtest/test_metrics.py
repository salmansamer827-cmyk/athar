from core.backtest.models import (
    BacktestTrade,
    TradeOutcome,
)

from core.backtest.metrics import (
    BacktestMetricsEngine,
)


trades = [
    BacktestTrade(
        timestamp="1",
        entry=100,
        stop_loss=99,
        take_profit=103,
        risk_r=1,
        reward_r=3,
        outcome=TradeOutcome.WIN,
        realized_r=3.0,
        market_state="VALUE_MIGRATION_UP",
        probability=0.70,
    ),

    BacktestTrade(
        timestamp="2",
        entry=100,
        stop_loss=99,
        take_profit=103,
        risk_r=1,
        reward_r=3,
        outcome=TradeOutcome.LOSS,
        realized_r=-1.0,
        market_state="BALANCED",
        probability=0.55,
    ),

    BacktestTrade(
        timestamp="3",
        entry=100,
        stop_loss=99,
        take_profit=103,
        risk_r=1,
        reward_r=3,
        outcome=TradeOutcome.WIN,
        realized_r=3.0,
        market_state="VALUE_MIGRATION_UP",
        probability=0.75,
    ),

    BacktestTrade(
        timestamp="4",
        entry=100,
        stop_loss=99,
        take_profit=103,
        risk_r=1,
        reward_r=3,
        outcome=TradeOutcome.LOSS,
        realized_r=-1.0,
        market_state="VALUE_CONTRACTION",
        probability=0.40,
    ),

    BacktestTrade(
        timestamp="5",
        entry=100,
        stop_loss=99,
        take_profit=103,
        risk_r=1,
        reward_r=3,
        outcome=TradeOutcome.WIN,
        realized_r=3.0,
        market_state="VALUE_MIGRATION_UP",
        probability=0.72,
    ),
]


engine = BacktestMetricsEngine()

metrics = engine.calculate(
    trades
)


print("=" * 60)
print("CAPITAL WISE")
print("BACKTEST METRICS ENGINE")
print("=" * 60)

print(
    f"Trades:             "
    f"{metrics.trades}"
)

print(
    f"Wins:               "
    f"{metrics.wins}"
)

print(
    f"Losses:             "
    f"{metrics.losses}"
)

print(
    f"Win Rate:           "
    f"{metrics.win_rate:.2%}"
)

print(
    f"Gross Profit:       "
    f"{metrics.gross_profit_r:.2f}R"
)

print(
    f"Gross Loss:         "
    f"{metrics.gross_loss_r:.2f}R"
)

print(
    f"Net Result:         "
    f"{metrics.net_r:.2f}R"
)

print(
    f"Expectancy:         "
    f"{metrics.expectancy_r:.4f}R"
)

print(
    f"Profit Factor:      "
    f"{metrics.profit_factor:.4f}"
)

print(
    f"Max Drawdown:       "
    f"{metrics.max_drawdown_r:.2f}R"
)

print("=" * 60)
