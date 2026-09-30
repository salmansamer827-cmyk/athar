from core.backtest.engine import (
    HistoricalBacktestEngine,
    BacktestConfig,
)

from core.backtest.metrics import (
    BacktestMetricsEngine,
)


candles = []

price = 100.0

for i in range(350):

    candles.append(
        {
            "timestamp": i,
            "open": price,
            "high": price + 1.0,
            "low": price - 1.0,
            "close": price,
            "volume": 1000.0,
        }
    )

    price += 0.10


def signal_function(history):

    entry = history[-1]["close"]

    return {
        "direction": "LONG",

        "entry": entry,

        "stop_loss": entry - 1.0,

        "take_profit": entry + 3.0,

        "probability": 0.70,

        "ev_r": 1.80,

        "market_state":
            "VALUE_MIGRATION_UP",

        "transaction_cost_r": 0.05,
    }


config = BacktestConfig(
    risk_percent=0.01,
    reward_risk=3.0,

    profile_lookback=100,
    forward_bars=20,

    min_probability=0.55,
    min_ev_r=0.0,
)


backtest = HistoricalBacktestEngine(
    config
)

trades = backtest.run(
    candles,
    signal_function,
)


metrics_engine = (
    BacktestMetricsEngine()
)

metrics = metrics_engine.calculate(
    trades
)


print("=" * 60)
print("CAPITAL WISE")
print("FULL QUANT BACKTEST PIPELINE")
print("=" * 60)

print(
    f"Trades:          {metrics.trades}"
)

print(
    f"Wins:            {metrics.wins}"
)

print(
    f"Losses:          {metrics.losses}"
)

print(
    f"Win Rate:        {metrics.win_rate:.2%}"
)

print(
    f"Gross Profit:    "
    f"{metrics.gross_profit_r:.2f}R"
)

print(
    f"Gross Loss:      "
    f"{metrics.gross_loss_r:.2f}R"
)

print(
    f"Net R:           "
    f"{metrics.net_r:.2f}R"
)

print(
    f"Expectancy:      "
    f"{metrics.expectancy_r:.4f}R"
)

print(
    "Profit Factor:   "
    + (
        f"{metrics.profit_factor:.4f}"
        if metrics.profit_factor is not None
        else "INF"
    )
)

print(
    f"Max Drawdown:    "
    f"{metrics.max_drawdown_r:.2f}R"
)

print("=" * 60)
